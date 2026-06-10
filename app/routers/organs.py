from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/organs", tags=["Órgãos"])

@router.get("", response_model=List[schemas.OrgaoResponse], summary="Listar órgãos")
def list_organs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(auth.get_current_user)
):
    """Lista todos os órgãos públicos cadastrados."""
    organs = db.query(models.Orgao).offset(skip).limit(limit).all()
    return organs

@router.post("", response_model=schemas.OrgaoResponse, status_code=status.HTTP_201_CREATED, summary="Criar órgão")
def create_organ(
    organ: schemas.OrgaoCreate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(auth.RoleChecker(["ADMIN_GERENCIADOR"]))
):
    """Cadastra um novo órgão público. Retorna erro se o CNPJ já estiver cadastrado."""
    # Check if CNPJ already exists
    db_organ = db.query(models.Orgao).filter(models.Orgao.cnpj == organ.cnpj).first()
    if db_organ:
        raise HTTPException(
            status_code=400,
            detail="Um órgão com este CNPJ já existe."
        )
    
    new_organ = models.Orgao(**organ.model_dump())
    db.add(new_organ)
    db.commit()
    db.refresh(new_organ)
    return new_organ

@router.get("/{organ_id}", response_model=schemas.OrgaoResponse, summary="Obter detalhe do órgão")
def get_organ(
    organ_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(auth.get_current_user)
):
    """Recupera os dados cadastrais de um órgão público específico por ID."""
    organ = db.query(models.Orgao).filter(models.Orgao.id == organ_id).first()
    if not organ:
        raise HTTPException(
            status_code=404,
            detail="Órgão não encontrado."
        )
    return organ
