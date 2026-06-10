from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone
from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/orders", tags=["Pedidos"])

@router.get("", response_model=List[schemas.PedidoResponse], summary="Listar pedidos")
def list_orders(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(auth.get_current_user)
):
    """
    Lista todos os pedidos de adesão cadastrados na base, ordenados pela data de criação decrescente.
    """
    query = db.query(models.Pedido)
    user_role = current_user.papel.value if hasattr(current_user.papel, "value") else current_user.papel
    
    if user_role == "COMPRADOR":
        query = query.filter(models.Pedido.orgao_comprador_id == current_user.orgao_id)
    elif user_role == "FORNECEDOR":
        query = (
            query.join(models.ItemPedido, models.ItemPedido.pedido_id == models.Pedido.id)
            .join(models.ItemAta, models.ItemAta.id == models.ItemPedido.item_ata_id)
            .filter(models.ItemAta.fornecedor_id == current_user.fornecedor_id)
            .distinct()
        )
    elif user_role == "ADMIN_GERENCIADOR":
        query = (
            query.join(models.Ata, models.Ata.id == models.Pedido.ata_id)
            .filter(
                (models.Pedido.orgao_comprador_id == current_user.orgao_id) |
                (models.Ata.orgao_gerenciador_id == current_user.orgao_id)
            )
        )
        
    orders = query.order_by(models.Pedido.data_pedido.desc()).offset(skip).limit(limit).all()
    return orders

@router.get("/{order_id}", response_model=schemas.PedidoDetailResponse, summary="Obter detalhe do pedido")
def get_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(auth.get_current_user)
):
    """
    Recupera os detalhes completos de um pedido específico por ID, incluindo o órgão comprador e todos os itens do pedido com suas respectivas informações da ATA.
    """
    order = (
        db.query(models.Pedido)
        .options(
            joinedload(models.Pedido.orgao_comprador),
            joinedload(models.Pedido.itens).joinedload(models.ItemPedido.item_ata)
        )
        .filter(models.Pedido.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(
            status_code=404,
            detail="Pedido não encontrado."
        )
        
    # Validar autorização de leitura baseada no papel
    is_authorized = False
    user_role = current_user.papel.value if hasattr(current_user.papel, "value") else current_user.papel
    if user_role == "ADMIN_GERENCIADOR":
        if order.orgao_comprador_id == current_user.orgao_id or order.ata.orgao_gerenciador_id == current_user.orgao_id:
            is_authorized = True
    elif user_role == "COMPRADOR":
        if order.orgao_comprador_id == current_user.orgao_id:
            is_authorized = True
    elif user_role == "FORNECEDOR":
        is_authorized = any(item.item_ata.fornecedor_id == current_user.fornecedor_id for item in order.itens)

    if not is_authorized:
        raise HTTPException(
            status_code=403,
            detail="Acesso negado: você não tem permissão para visualizar este pedido."
        )
        
    return order

@router.post("", response_model=schemas.PedidoResponse, status_code=status.HTTP_201_CREATED, summary="Criar pedido (Checkout)")
def create_order(
    order_in: schemas.PedidoCreate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(auth.RoleChecker(["COMPRADOR"]))
):
    """
    Cria e efetua um novo pedido de compra (Checkout) vinculado a uma ATA específica.

    Validações realizadas na transação:
    - Verificação de existência do Órgão Comprador e da ATA.
    - Bloqueio pessimista de concorrência nos itens da ATA solicitados (via `FOR UPDATE`).
    - Validação de saldo físico disponível (quantidade solicitada não pode exceder o saldo atual).
    - Validação de limite legal da modalidade CARONA (não permite ultrapassar o percentual máximo configurado na ATA).
    """
    # Validar se o comprador autenticado é do mesmo órgão comprador solicitado
    if current_user.orgao_id != order_in.orgao_comprador_id:
        raise HTTPException(
            status_code=403,
            detail="Acesso negado: você só pode criar pedidos em nome do seu próprio órgão comprador."
        )

    # 1. Validate Buyer Organ
    organ = db.query(models.Orgao).filter(models.Orgao.id == order_in.orgao_comprador_id).first()
    if not organ:
        raise HTTPException(
            status_code=400,
            detail=f"Órgão Comprador com ID {order_in.orgao_comprador_id} não encontrado."
        )

    # 2. Validate ATA
    ata = db.query(models.Ata).filter(models.Ata.id == order_in.ata_id).first()
    if not ata:
        raise HTTPException(
            status_code=400,
            detail=f"Ata com ID {order_in.ata_id} não encontrada."
        )

    # Begin transaction block via DB Session
    new_order = models.Pedido(
        orgao_comprador_id=order_in.orgao_comprador_id,
        ata_id=order_in.ata_id,
        data_pedido=datetime.now(timezone.utc),
        tipo_adesao=order_in.tipo_adesao.value,
        status=schemas.StatusPedido.PENDENTE.value
    )
    
    db.add(new_order)
    db.flush() # Flush to populate new_order.id

    # 3. Create items with row locks and business validations
    for item_in in order_in.itens:
        # Validate that the item belongs to the selected ATA AND lock it
        # utilizing with_for_update() to prevent race conditions during checkout
        item_ata = (
            db.query(models.ItemAta)
            .filter(
                models.ItemAta.id == item_in.item_ata_id,
                models.ItemAta.ata_id == order_in.ata_id
            )
            .with_for_update()
            .first()
        )
        
        if not item_ata:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"O item com ID {item_in.item_ata_id} não pertence à ATA {order_in.ata_id}."
            )

        if item_in.quantidade_solicitada <= 0:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail="Quantidade solicitada deve ser maior que zero."
            )

        # A. Physical balance check
        # Query current active consumed quantity (Authorized or Emitted)
        active_consumed = (
            db.query(func.coalesce(func.sum(models.ItemPedido.quantidade_solicitada), 0))
            .join(models.Pedido, models.Pedido.id == models.ItemPedido.pedido_id)
            .filter(
                models.ItemPedido.item_ata_id == item_ata.id,
                models.Pedido.status.in_([schemas.StatusPedido.AUTORIZADO.value, schemas.StatusPedido.EMITIDO.value])
            )
            .scalar()
        )
        available_balance = item_ata.quantidade_total_ofertada - active_consumed

        if item_in.quantidade_solicitada > available_balance:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Saldo físico insuficiente para o item {item_ata.numero_item} "
                    f"({item_ata.descricao_especificacao[:30]}...). "
                    f"Solicitado: {item_in.quantidade_solicitada}, Disponível: {available_balance}."
                )
            )

        # B. Carona legal limit check (Auto limit block)
        if order_in.tipo_adesao == schemas.TipoAdesao.CARONA:
            # Check the carona rules configured for this ATA
            regra = db.query(models.RegraLimiteCarona).filter(models.RegraLimiteCarona.ata_id == order_in.ata_id).first()
            if regra:
                limit_percent = regra.percentual_maximo_do_saldo
                limite_carona_item = item_ata.quantidade_total_ofertada * (limit_percent / 100)

                if item_in.quantidade_solicitada > limite_carona_item:
                    db.rollback()
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            f"Trava de Carona Ativada: A quantidade solicitada ({item_in.quantidade_solicitada}) "
                            f"para o item {item_ata.numero_item} excede o limite legal máximo permitido para adesões externas "
                            f"({limite_carona_item} correspondente a {limit_percent}% da quantidade ofertada)."
                        )
                    )
            
        new_item_pedido = models.ItemPedido(
            pedido_id=new_order.id,
            item_ata_id=item_in.item_ata_id,
            quantidade_solicitada=item_in.quantidade_solicitada,
            preco_unitario_no_pedido=item_in.preco_unitario_no_pedido
        )
        db.add(new_item_pedido)

    try:
        db.commit()
        db.refresh(new_order)
        return new_order
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Não foi possível criar o pedido: {str(e)}"
        )


@router.put("/{order_id}/status", response_model=schemas.PedidoResponse, summary="Atualizar status do pedido (Workflow)")
def update_order_status(
    order_id: UUID,
    status_update: schemas.OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(auth.get_current_user)
):
    """
    Atualiza o status de aprovação de um pedido específico (Workflow de autorização e justificativa de rejeição).

    Regras de transição:
    - Permite mudar o status para `AUTORIZADO`, `REJEITADO` ou `EMITIDO`.
    - Ao aprovar (`AUTORIZADO`), é obrigatório informar o ID de um usuário autorizador válido com permissão de gestor.
    - Ao rejeitar (`REJEITADO`), é obrigatório informar a justificativa detalhada da rejeição.
    """
    # 1. Fetch order
    order = db.query(models.Pedido).filter(models.Pedido.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=404,
            detail="Pedido não encontrado."
        )

    # 2. Validar permissões baseadas nas transições de status
    user_role = current_user.papel.value if hasattr(current_user.papel, "value") else current_user.papel
    if status_update.status in [schemas.StatusPedido.AUTORIZADO, schemas.StatusPedido.REJEITADO]:
        # Apenas gestores do órgão gerenciador da ATA podem aprovar/rejeitar
        if user_role != "ADMIN_GERENCIADOR" or current_user.orgao_id != order.ata.orgao_gerenciador_id:
            raise HTTPException(
                status_code=403,
                detail="Acesso negado: apenas usuários gerenciadores do órgão gestor da ATA podem aprovar ou rejeitar solicitações."
            )
    elif status_update.status == schemas.StatusPedido.EMITIDO:
        # Apenas compradores do próprio órgão comprador podem emitir o pedido final
        if user_role != "COMPRADOR" or current_user.orgao_id != order.orgao_comprador_id:
            raise HTTPException(
                status_code=403,
                detail="Acesso negado: apenas usuários compradores do órgão que realizou o pedido podem emitir a nota de empenho."
            )

    # 3. Validate transitions
    if status_update.status == schemas.StatusPedido.REJEITADO:
        if not status_update.justificativa_rejeicao:
            raise HTTPException(
                status_code=400,
                detail="A justificativa de rejeição é obrigatória para rejeitar um pedido."
            )
        order.justificativa_rejeicao = status_update.justificativa_rejeicao
        order.autorizado_por_usuario_id = status_update.autorizado_por_usuario_id
        order.data_autorizacao = datetime.now(timezone.utc)
        
    elif status_update.status == schemas.StatusPedido.AUTORIZADO:
        if not status_update.autorizado_por_usuario_id:
            raise HTTPException(
                status_code=400,
                detail="O usuário autorizador é obrigatório para aprovar o pedido."
            )
        # Verify that the user exists and has permission
        user = db.query(models.Usuario).filter(models.Usuario.id == status_update.autorizado_por_usuario_id).first()
        user_role = user.papel.value if user and hasattr(user.papel, "value") else (user.papel if user else None)
        if not user or user_role not in ["ADMIN_GERENCIADOR", "COMPRADOR"]:
            raise HTTPException(
                status_code=400,
                detail="Usuário autorizador inválido ou sem permissões de gestor."
            )
        order.autorizado_por_usuario_id = status_update.autorizado_por_usuario_id
        order.data_autorizacao = datetime.now(timezone.utc)
        order.justificativa_rejeicao = None
        
    elif status_update.status == schemas.StatusPedido.EMITIDO:
        order.justificativa_rejeicao = None

    order.status = status_update.status.value

    try:
        db.commit()
        db.refresh(order)
        return order
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Não foi possível atualizar o status do pedido: {str(e)}"
        )
