from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/auth", tags=["Autenticação"])

@router.post("/login", response_model=schemas.TokenResponse, summary="Realizar login do usuário (Form/Swagger)")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Efetua o login de um usuário autenticando por formulário padrão OAuth2 (e-mail no campo 'username' e senha).
    
    Retorna o token JWT e as informações do usuário. Ideal para integração direta com o botão 'Authorize' do Swagger UI.
    """
    user = db.query(models.Usuario).filter(models.Usuario.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="E-mail ou senha incorretos."
        )
    
    # Payload do token contendo sub, email e papel
    user_role = user.papel.value if hasattr(user.papel, "value") else user.papel
    token_payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user_role
    }
    access_token = auth.create_access_token(data=token_payload)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "id": user.id,
        "email": user.email,
        "papel": user.papel,
        "orgao_id": user.orgao_id,
        "fornecedor_id": user.fornecedor_id
    }


@router.post("/login/json", response_model=schemas.TokenResponse, summary="Realizar login do usuário (JSON)")
def login_json(
    login_in: schemas.LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Efetua o login de um usuário autenticando via corpo JSON contendo e-mail e senha.
    
    Retorna o token JWT e as informações do usuário. Ideal para consumo por frontends SPA (React/Vue/Angular).
    """
    user = db.query(models.Usuario).filter(models.Usuario.email == login_in.email).first()
    if not user or not auth.verify_password(login_in.password, user.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="E-mail ou senha incorretos."
        )
    
    # Payload do token contendo sub, email e papel
    user_role = user.papel.value if hasattr(user.papel, "value") else user.papel
    token_payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user_role
    }
    access_token = auth.create_access_token(data=token_payload)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "id": user.id,
        "email": user.email,
        "papel": user.papel,
        "orgao_id": user.orgao_id,
        "fornecedor_id": user.fornecedor_id
    }


@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED, summary="Cadastrar um novo usuário (Gestão Descentralizada)")
def register(
    user_in: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(auth.RoleChecker(["ADMIN_GERENCIADOR"]))
):
    """
    Cadastra um novo usuário no portal BIAP.

    Regras de autorização e integridade (Modelo 1):
    - Apenas administradores do órgão gerenciador (`ADMIN_GERENCIADOR`) podem acessar este recurso.
    - Se for criar um usuário `COMPRADOR` ou `ADMIN_GERENCIADOR`, o `orgao_id` deve ser idêntico ao do administrador atual.
    - Se for criar um usuário `FORNECEDOR`, o `fornecedor_id` deve corresponder a uma empresa fornecedora cadastrada e ativa.
    - A senha será criptografada com algoritmo Bcrypt.
    """
    # 1. Verificar e-mail duplicado
    existing_user = db.query(models.Usuario).filter(models.Usuario.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe um usuário cadastrado com este e-mail."
        )

    user_role_str = user_in.papel.value if hasattr(user_in.papel, "value") else user_in.papel

    # 2. Validar restrições de papéis e vínculos de órgão/fornecedor
    if user_role_str in ["ADMIN_GERENCIADOR", "COMPRADOR"]:
        if not user_in.orgao_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O campo 'orgao_id' é obrigatório para administradores e compradores."
            )
        if user_in.fornecedor_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O campo 'fornecedor_id' deve ser nulo para administradores e compradores."
            )
        
        # Regra de Gestão Descentralizada: Só pode criar usuários para seu próprio órgão
        if user_in.orgao_id != current_user.orgao_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado: você só tem permissão para cadastrar usuários para o seu próprio órgão público."
            )

    elif user_role_str == "FORNECEDOR":
        if not user_in.fornecedor_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O campo 'fornecedor_id' é obrigatório para fornecedores."
            )
        if user_in.orgao_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O campo 'orgao_id' deve ser nulo para fornecedores."
            )
        
        # Verificar se o fornecedor existe no banco
        supplier = db.query(models.Fornecedor).filter(models.Fornecedor.id == user_in.fornecedor_id).first()
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Fornecedor com ID {user_in.fornecedor_id} não encontrado."
            )

    # 3. Criptografar a senha e salvar no banco
    hashed_pwd = auth.get_password_hash(user_in.password)
    new_user = models.Usuario(
        email=user_in.email,
        senha_hash=hashed_pwd,
        orgao_id=user_in.orgao_id,
        fornecedor_id=user_in.fornecedor_id,
        papel=user_in.papel.value if hasattr(user_in.papel, "value") else user_in.papel
    )

    db.add(new_user)
    try:
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Não foi possível salvar o usuário: {str(e)}"
        )


@router.put("/users/{user_id}", response_model=schemas.UserResponse, summary="Atualizar dados de um usuário")
def update_user(
    user_id: UUID,
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(auth.RoleChecker(["ADMIN_GERENCIADOR"]))
):
    """
    Atualiza as informações de um usuário por ID.

    Regras de autorização e validação (Modelo 1):
    - Apenas administradores (`ADMIN_GERENCIADOR`) podem acessar esta rota.
    - O administrador só pode editar usuários pertencentes ao seu próprio órgão.
    - Se o e-mail for alterado, verifica se não está duplicado.
    - Se a senha for enviada, ela será re-encriptada.
    """
    # 1. Buscar usuário que será atualizado
    user_to_update = db.query(models.Usuario).filter(models.Usuario.id == user_id).first()
    if not user_to_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado."
        )

    # 2. Impedir que altere usuários de outro órgão
    if user_to_update.orgao_id and user_to_update.orgao_id != current_user.orgao_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado: você só pode atualizar usuários pertencentes ao seu próprio órgão público."
        )

    # 3. Processar campos enviados
    if user_update.email is not None and user_update.email != user_to_update.email:
        # Verificar e-mail duplicado
        existing_email = db.query(models.Usuario).filter(models.Usuario.email == user_update.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Já existe um usuário cadastrado com este e-mail."
            )
        user_to_update.email = user_update.email

    if user_update.password is not None:
        user_to_update.senha_hash = auth.get_password_hash(user_update.password)

    # Se papel, orgao_id ou fornecedor_id forem enviados, re-validar as constraints
    new_papel = user_update.papel if user_update.papel is not None else user_to_update.papel
    new_papel_str = new_papel.value if hasattr(new_papel, "value") else new_papel

    new_orgao_id = user_update.orgao_id if user_update.orgao_id is not None else user_to_update.orgao_id
    new_fornecedor_id = user_update.fornecedor_id if user_update.fornecedor_id is not None else user_to_update.fornecedor_id

    # Se houver mudanças em papel ou vínculos, fazer as validações do modelo
    if user_update.papel is not None or user_update.orgao_id is not None or user_update.fornecedor_id is not None:
        if new_papel_str in ["ADMIN_GERENCIADOR", "COMPRADOR"]:
            if not new_orgao_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="O campo 'orgao_id' é obrigatório para administradores e compradores."
                )
            if new_fornecedor_id is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="O campo 'fornecedor_id' deve ser nulo para administradores e compradores."
                )
            # Garantir que o novo órgão inserido também seja o do próprio admin
            if new_orgao_id != current_user.orgao_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Acesso negado: você só pode associar usuários ao seu próprio órgão público."
                )
        elif new_papel_str == "FORNECEDOR":
            if not new_fornecedor_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="O campo 'fornecedor_id' é obrigatório para fornecedores."
                )
            if new_orgao_id is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="O campo 'orgao_id' deve ser nulo para fornecedores."
                )
            
            # Verificar se o fornecedor existe no banco
            supplier = db.query(models.Fornecedor).filter(models.Fornecedor.id == new_fornecedor_id).first()
            if not supplier:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Fornecedor com ID {new_fornecedor_id} não encontrado."
                )
        
        user_to_update.papel = new_papel_str
        user_to_update.orgao_id = new_orgao_id
        user_to_update.fornecedor_id = new_fornecedor_id

    try:
        db.commit()
        db.refresh(user_to_update)
        return user_to_update
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Não foi possível atualizar o usuário: {str(e)}"
        )


