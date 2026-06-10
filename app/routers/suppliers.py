from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from uuid import UUID
from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/suppliers", tags=["Fornecedores"])

@router.get("", response_model=List[schemas.FornecedorResponse], summary="Listar fornecedores")
def list_suppliers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(auth.get_current_user)
):
    """Lista todos os fornecedores cadastrados."""
    suppliers = db.query(models.Fornecedor).offset(skip).limit(limit).all()
    return suppliers

@router.post("", response_model=schemas.FornecedorResponse, status_code=status.HTTP_201_CREATED, summary="Criar fornecedor")
def create_supplier(
    supplier: schemas.FornecedorCreate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(auth.RoleChecker(["ADMIN_GERENCIADOR"]))
):
    """Cadastra um novo fornecedor. Retorna erro se o CNPJ já estiver cadastrado."""
    # Check if CNPJ already exists
    db_supplier = db.query(models.Fornecedor).filter(models.Fornecedor.cnpj == supplier.cnpj).first()
    if db_supplier:
        raise HTTPException(
            status_code=400,
            detail="Um fornecedor com este CNPJ já existe."
        )
    
    new_supplier = models.Fornecedor(**supplier.model_dump())
    db.add(new_supplier)
    db.commit()
    db.refresh(new_supplier)
    return new_supplier

@router.get("/{supplier_id}", response_model=schemas.FornecedorResponse, summary="Obter detalhe do fornecedor")
def get_supplier(
    supplier_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(auth.get_current_user)
):
    """Recupera os dados cadastrais de um fornecedor específico por ID."""
    supplier = db.query(models.Fornecedor).filter(models.Fornecedor.id == supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=404,
            detail="Fornecedor não encontrado."
        )
    return supplier

@router.get("/{supplier_id}/items", response_model=List[schemas.ItemSearchResponse], summary="Listar itens ganhos pelo fornecedor")
def get_supplier_items(
    supplier_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(auth.get_current_user)
):
    """Lista todos os itens ganhos por um fornecedor específico, incluindo o saldo físico disponível."""
    # Se for papel FORNECEDOR, ele só pode acessar os próprios itens
    if current_user.papel.value == "FORNECEDOR" and current_user.fornecedor_id != supplier_id:
        raise HTTPException(
            status_code=403,
            detail="Acesso negado: você só pode consultar os itens da sua própria empresa."
        )
    # Check if supplier exists
    supplier_exists = db.query(models.Fornecedor.id).filter(models.Fornecedor.id == supplier_id).first()
    if not supplier_exists:
        raise HTTPException(
            status_code=404,
            detail="Fornecedor não encontrado."
        )
    
    # Query won items with their calculated balances
    results = (
        db.query(models.ItemAta, models.VwSaldoItemAta.quantidade_saldo_disponivel)
        .join(models.VwSaldoItemAta, models.VwSaldoItemAta.id == models.ItemAta.id)
        .options(
            joinedload(models.ItemAta.fornecedor),
            joinedload(models.ItemAta.ata),
            joinedload(models.ItemAta.grupo)
        )
        .filter(models.ItemAta.fornecedor_id == supplier_id)
        .all()
    )
    
    response_items = []
    for item, saldo_disp in results:
        item.quantidade_saldo_disponivel = saldo_disp
        response_items.append(item)
    return response_items

@router.get("/{supplier_id}/orders", response_model=List[schemas.PedidoDetailResponse], summary="Listar pedidos do fornecedor (Central de Notificações)")
def get_supplier_orders(
    supplier_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(auth.get_current_user)
):
    """Central de Notificações do Fornecedor: Lista todos os pedidos que contêm itens deste fornecedor."""
    # Se for papel FORNECEDOR, ele só pode acessar os próprios pedidos
    if current_user.papel.value == "FORNECEDOR" and current_user.fornecedor_id != supplier_id:
        raise HTTPException(
            status_code=403,
            detail="Acesso negado: você só pode consultar pedidos direcionados à sua própria empresa."
        )
    # Check if supplier exists
    supplier_exists = db.query(models.Fornecedor.id).filter(models.Fornecedor.id == supplier_id).first()
    if not supplier_exists:
        raise HTTPException(
            status_code=404,
            detail="Fornecedor não encontrado."
        )
    
    # Query orders (notification center) that contain items belonging to this supplier
    orders = (
        db.query(models.Pedido)
        .options(
            joinedload(models.Pedido.orgao_comprador),
            joinedload(models.Pedido.itens).joinedload(models.ItemPedido.item_ata)
        )
        .join(models.ItemPedido, models.ItemPedido.pedido_id == models.Pedido.id)
        .join(models.ItemAta, models.ItemAta.id == models.ItemPedido.item_ata_id)
        .filter(models.ItemAta.fornecedor_id == supplier_id)
        .order_by(models.Pedido.data_pedido.desc())
        .distinct()
        .all()
    )
    return orders
