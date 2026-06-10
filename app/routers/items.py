from fastapi import APIRouter, Depends, Query
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
