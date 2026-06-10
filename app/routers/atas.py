from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from uuid import UUID
from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/atas", tags=["ATAs"])

@router.get("", response_model=List[schemas.AtaResponse], summary="Listar ATAs")
def list_atas(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(auth.get_current_user)
):
    """Lista todas as Atas de Registro de Preços cadastradas."""
    atas = db.query(models.Ata).offset(skip).limit(limit).all()
    return atas

@router.get("/{ata_id}", response_model=schemas.AtaDetailResponse, summary="Obter detalhe da ATA")
def get_ata(
    ata_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(auth.get_current_user)
):
    """Recupera os detalhes completos de uma ATA específica, incluindo seus lotes/grupos, itens e regras de carona."""
    ata = (
        db.query(models.Ata)
        .options(
            joinedload(models.Ata.orgao_gerenciador),
            joinedload(models.Ata.grupos),
            joinedload(models.Ata.items),
            joinedload(models.Ata.regras_carona)
        )
        .filter(models.Ata.id == ata_id)
        .first()
    )
    if not ata:
        raise HTTPException(
            status_code=404,
            detail="Ata não encontrada."
        )
    return ata

@router.get("/{ata_id}/balances", response_model=List[schemas.VwSaldoItemAtaResponse], summary="Listar saldos dos itens da ATA")
def get_ata_balances(
    ata_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(auth.get_current_user)
):
    """Consulta os saldos físicos disponíveis de todos os itens de uma determinada ATA."""
    # Check if Ata exists
    ata_exists = db.query(models.Ata.id).filter(models.Ata.id == ata_id).first()
    if not ata_exists:
        raise HTTPException(
            status_code=404,
            detail="Ata não encontrada."
        )
        
    balances = db.query(models.VwSaldoItemAta).filter(models.VwSaldoItemAta.ata_id == ata_id).all()
    return balances

@router.get("/balances/item/{item_ata_id}", response_model=schemas.VwSaldoItemAtaResponse, summary="Obter saldo do item da ATA")
def get_item_balance(
    item_ata_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(auth.get_current_user)
):
    """Consulta o saldo físico disponível de um único item específico de ATA."""
    balance = db.query(models.VwSaldoItemAta).filter(models.VwSaldoItemAta.id == item_ata_id).first()
    if not balance:
        raise HTTPException(
            status_code=404,
            detail="Saldo do item ou item não encontrado."
        )
    return balance

@router.post("", response_model=schemas.AtaResponse, status_code=status.HTTP_201_CREATED, summary="Criar ATA de forma aninhada")
def create_ata(
    ata_in: schemas.AtaCreateNested,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(auth.RoleChecker(["ADMIN_GERENCIADOR"]))
):
    """Carga de Dados e Upload de ATA: Cadastra uma nova ATA contendo grupos, itens e regras de carona de forma aninhada."""
    # Check if number already exists
    db_ata = db.query(models.Ata).filter(models.Ata.numero_ata == ata_in.numero_ata).first()
    if db_ata:
        raise HTTPException(
            status_code=400,
            detail=f"Ata com número {ata_in.numero_ata} já existe."
        )

    # Validate managing organ
    organ = db.query(models.Orgao).filter(models.Orgao.id == ata_in.orgao_gerenciador_id).first()
    if not organ:
        raise HTTPException(
            status_code=400,
            detail=f"Órgão Gerenciador com ID {ata_in.orgao_gerenciador_id} não encontrado."
        )

    # Validate that current user belongs to the managing organ
    if current_user.orgao_id != ata_in.orgao_gerenciador_id:
        raise HTTPException(
            status_code=403,
            detail="Acesso negado: você só pode cadastrar uma ATA vinculada ao seu próprio órgão gerenciador."
        )

    # Create ATA
    new_ata = models.Ata(
        numero_ata=ata_in.numero_ata,
        processo_administrativo=ata_in.processo_administrativo,
        numero_pregao=ata_in.numero_pregao,
        orgao_gerenciador_id=ata_in.orgao_gerenciador_id,
        data_assinatura=ata_in.data_assinatura,
        data_publicacao=ata_in.data_publicacao,
        vigencia_meses=ata_in.vigencia_meses,
        valor_total_global=ata_in.valor_total_global
    )
    db.add(new_ata)
    db.flush()  # Popula new_ata.id

    # Create groups
    group_map = {}
    for group_in in ata_in.grupos:
        new_group = models.GrupoLote(
            ata_id=new_ata.id,
            numero_grupo=group_in.numero_grupo,
            descricao=group_in.descricao
        )
        db.add(new_group)
        db.flush()
        group_map[group_in.numero_grupo] = new_group.id

    # Create carona rules
    for rule_in in ata_in.regras_carona:
        new_rule = models.RegraLimiteCarona(
            ata_id=new_ata.id,
            percentual_maximo_do_saldo=rule_in.percentual_maximo_do_saldo,
            descricao=rule_in.descricao
        )
        db.add(new_rule)

    # Create items
    for item_in in ata_in.items:
        # Resolve group_id
        grupo_id = None
        if item_in.grupo_numero and item_in.grupo_numero in group_map:
            grupo_id = group_map[item_in.grupo_numero]

        # Validate supplier
        supplier = db.query(models.Fornecedor).filter(models.Fornecedor.id == item_in.fornecedor_id).first()
        if not supplier:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Fornecedor com ID {item_in.fornecedor_id} não encontrado."
            )

        new_item = models.ItemAta(
            ata_id=new_ata.id,
            grupo_id=grupo_id,
            fornecedor_id=item_in.fornecedor_id,
            numero_item=item_in.numero_item,
            descricao_especificacao=item_in.descricao_especificacao,
            unidade_medida=item_in.unidade_medida,
            marca_modelo=item_in.marca_modelo,
            valor_unitario=item_in.valor_unitario,
            quantidade_total_ofertada=item_in.quantidade_total_ofertada
        )
        db.add(new_item)

    try:
        db.commit()
        db.refresh(new_ata)
        return new_ata
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Não foi possível criar a Ata de Registro de Preços: {str(e)}"
        )
