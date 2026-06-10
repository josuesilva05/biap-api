from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
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

