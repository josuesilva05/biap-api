import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app import models, schemas

# Configuração do OAuth2
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    description="Insira o token JWT no formato: Bearer <token>"
)

# ============================================================================
# 1. UTILITÁRIOS DE CRIPTOGRAFIA DE SENHA (BCRYPT)
# ============================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se a senha em texto plano corresponde ao hash armazenado.
    """
    try:
        # bcrypt espera bytes para comparação
        plain_bytes = plain_password.encode("utf-8")
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(plain_bytes, hashed_bytes)
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    """
    Gera um hash Bcrypt seguro a partir de uma senha em texto plano.
    """
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

# ============================================================================
# 2. UTILITÁRIOS DE CRIAÇÃO E DECODIFICAÇÃO DE JWT
# ============================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Cria um token JWT contendo os dados do payload e tempo de expiração.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt

# ============================================================================
# 3. DEPENDÊNCIAS DO FASTAPI PARA AUTENTICAÇÃO E AUTORIZAÇÃO (RBAC)
# ============================================================================

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.Usuario:
    """
    Dependência injetável que recupera e valida o usuário a partir do token JWT.
    Retorna 401 Unauthorized se o token for inválido ou expirado.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas, faça login novamente.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id_str: str = payload.get("sub")
        email: str = payload.get("email")
        if user_id_str is None or email is None:
            raise credentials_exception
        
        user_id = UUID(user_id_str)
    except (jwt.PyJWTError, ValueError):
        raise credentials_exception
        
    user = db.query(models.Usuario).filter(models.Usuario.id == user_id).first()
    if user is None:
        raise credentials_exception
        
    return user


class RoleChecker:
    """
    Injetável para verificar o papel do usuário (RBAC - Role Based Access Control).
    Permite apenas acessos autorizados com base em uma lista de papéis permitidos.
    """
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: models.Usuario = Depends(get_current_user)) -> models.Usuario:
        user_role = current_user.papel.value if hasattr(current_user.papel, "value") else current_user.papel
        if user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado: seu papel de '{user_role}' não possui permissão para esta ação."
            )
        return current_user
