from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/items", tags=["Catálogo / Marketplace"])

@router.get("/search", response_model=List[schemas.ItemSearchResponse], summary="Buscar e filtrar itens do catálogo")
def search_items(
    q: Optional[str] = Query(None, description="Busca por palavra-chave na descrição do item"),
    min_price: Optional[Decimal] = Query(None, description="Preço unitário mínimo"),
    max_price: Optional[Decimal] = Query(None, description="Preço unitário máximo"),
    marca: Optional[str] = Query(None, description="Filtrar por marca/modelo"),
    fornecedor_id: Optional[UUID] = Query(None, description="Filtrar por ID do fornecedor"),
    numero_ata: Optional[str] = Query(None, description="Filtrar por número da ATA original"),
    sort: Optional[str] = Query("price_asc", description="Ordenação: 'price_asc' (menor preço) ou 'price_desc' (maior preço)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(auth.get_current_user)
):
    """
    Busca e filtra itens no catálogo da vitrine (Marketplace B2G).

    Permite filtrar por palavra-chave na descrição, faixa de preço unitário, marca/modelo, fornecedor e número da ATA de origem.
    Suporta paginação e ordenação por preço (crescente ou decrescente).
    Retorna a lista de itens com seus respectivos saldos físicos disponíveis calculados em tempo real.
    """
    # Base query joining ItemAta with its balance view
    query = (
        db.query(models.ItemAta, models.VwSaldoItemAta.quantidade_saldo_disponivel)
        .join(models.VwSaldoItemAta, models.VwSaldoItemAta.id == models.ItemAta.id)
        .options(
            joinedload(models.ItemAta.fornecedor),
            joinedload(models.ItemAta.ata),
            joinedload(models.ItemAta.grupo)
        )
    )

    # Apply Filters
    if q:
        query = query.filter(models.ItemAta.descricao_especificacao.ilike(f"%{q}%"))
    
    if min_price is not None:
        query = query.filter(models.ItemAta.valor_unitario >= min_price)
        
    if max_price is not None:
        query = query.filter(models.ItemAta.valor_unitario <= max_price)
        
    if marca:
        query = query.filter(models.ItemAta.marca_modelo.ilike(f"%{marca}%"))
        
    if fornecedor_id:
        query = query.filter(models.ItemAta.fornecedor_id == fornecedor_id)
        
    if numero_ata:
        # We need to join the Ata table to filter by its attributes
        query = query.join(models.Ata, models.Ata.id == models.ItemAta.ata_id).filter(
            models.Ata.numero_ata.ilike(f"%{numero_ata}%")
        )

    # Apply Sorting
    if sort == "price_desc":
        query = query.order_by(models.ItemAta.valor_unitario.desc())
    else:  # default is price_asc
        query = query.order_by(models.ItemAta.valor_unitario.asc())

    results = query.offset(skip).limit(limit).all()

    # Map the tuple (ItemAta, quantidade_saldo_disponivel) to the response schema format
    response_items = []
    for item, saldo_disp in results:
        # Set the dynamic saldo property so that it gets serialized into Pydantic
        item.quantidade_saldo_disponivel = saldo_disp
        response_items.append(item)

    return response_items


@router.put("/{item_ata_id}", response_model=schemas.ItemAtaResponse, summary="Atualizar um item da ATA")
def update_item_ata(
    item_ata_id: UUID,
    item_update: schemas.ItemAtaUpdate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(auth.get_current_user)
):
    """
    Atualiza as informações de um item de ATA (ItemAta) por ID.

    Regras de autorização e validação (Modelo 1):
    - Se o usuário for ADMIN_GERENCIADOR e gerencia a ATA (ou seja, o orgao_gerenciador_id da ATA associada ao item é igual ao orgao_id do usuário atual):
      - Permite atualizar qualquer um dos campos fornecidos: descricao_especificacao, unidade_medida, marca_modelo, valor_unitario, quantidade_total_ofertada.
    - Se o usuário for FORNECEDOR e é o fornecedor do item (ou seja, o fornecedor_id do item é igual ao fornecedor_id do usuário atual):
      - Permite atualizar APENAS o campo marca_modelo.
      - Se o usuário tentar enviar qualquer outro campo para atualização, retorna erro 403 Forbidden.
    - Em qualquer outro caso (usuário não tem permissão), retorna erro 403 Forbidden.
    """
    # 1. Buscar o item com sua ATA associada
    item = (
        db.query(models.ItemAta)
        .options(joinedload(models.ItemAta.ata))
        .filter(models.ItemAta.id == item_ata_id)
        .first()
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item da ATA não encontrado."
        )

    user_role = current_user.papel.value if hasattr(current_user.papel, "value") else current_user.papel

    # 2. Verificar permissões com base no papel
    is_admin_gerenciador = (
        user_role == "ADMIN_GERENCIADOR" 
        and item.ata.orgao_gerenciador_id == current_user.orgao_id
    )
    is_fornecedor_dono = (
        user_role == "FORNECEDOR"
        and item.fornecedor_id == current_user.fornecedor_id
    )

    if not is_admin_gerenciador and not is_fornecedor_dono:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado: você não tem permissão para editar este item."
        )

    # 3. Extrair dados enviados no corpo da requisição
    update_data = item_update.model_dump(exclude_unset=True)

    # Se for FORNECEDOR, validar que apenas marca_modelo e url_imagem estão sendo atualizados
    if is_fornecedor_dono:
        other_fields = [k for k in update_data.keys() if k not in ["marca_modelo", "url_imagem"]]
        if other_fields:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado: fornecedores só têm permissão para atualizar os campos 'marca_modelo' e 'url_imagem'."
            )

    # 4. Aplicar as alterações
    for field, value in update_data.items():
        setattr(item, field, value)

    try:
        db.commit()
        db.refresh(item)
        return item
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar o item da ATA: {str(e)}"
        )
