from pydantic import BaseModel, ConfigDict, EmailStr
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from enum import Enum

class TipoOrgao(str, Enum):
    FEDERAL = "FEDERAL"
    ESTADUAL = "ESTADUAL"
    MUNICIPAL = "MUNICIPAL"

class PapelUsuario(str, Enum):
    ADMIN_GERENCIADOR = "ADMIN_GERENCIADOR"
    COMPRADOR = "COMPRADOR"
    FORNECEDOR = "FORNECEDOR"

class TipoAdesao(str, Enum):
    DIRETA = "DIRETA"
    CARONA = "CARONA"

class StatusPedido(str, Enum):
    PENDENTE = "PENDENTE"
    AUTORIZADO = "AUTORIZADO"
    REJEITADO = "REJEITADO"
    EMITIDO = "EMITIDO"


# FORNECEDOR SCHEMAS
class FornecedorBase(BaseModel):
    cnpj: str
    razao_social: str
    endereco: Optional[str] = None
    nome_representante: Optional[str] = None
    cpf_representante: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None

class FornecedorCreate(FornecedorBase):
    pass

class FornecedorResponse(FornecedorBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)


# ORGAO SCHEMAS
class OrgaoBase(BaseModel):
    cnpj: str
    nome: str
    tipo: TipoOrgao
    endereco: Optional[str] = None

class OrgaoCreate(OrgaoBase):
    pass

class OrgaoResponse(OrgaoBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)


# GRUPO LOTE SCHEMAS
class GrupoLoteResponse(BaseModel):
    id: UUID
    numero_grupo: Optional[str] = None
    descricao: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


# ITEM ATA SCHEMAS
class ItemAtaParticipanteCreateNested(BaseModel):
    orgao_id: UUID
    quantidade_planejada: Decimal

class ItemAtaParticipanteResponse(BaseModel):
    id: UUID
    item_ata_id: UUID
    orgao_id: UUID
    quantidade_planejada: Decimal
    orgao: Optional[OrgaoResponse] = None
    model_config = ConfigDict(from_attributes=True)

class ItemAtaResponse(BaseModel):
    id: UUID
    ata_id: UUID
    grupo_id: Optional[UUID] = None
    fornecedor_id: UUID
    numero_item: Optional[str] = None
    descricao_especificacao: str
    unidade_medida: Optional[str] = None
    marca_modelo: Optional[str] = None
    url_imagem: Optional[str] = None
    valor_unitario: Decimal
    quantidade_total_ofertada: Decimal
    participantes: List[ItemAtaParticipanteResponse] = []
    model_config = ConfigDict(from_attributes=True)


# REGRA LIMITE CARONA SCHEMAS
class RegraLimiteCaronaResponse(BaseModel):
    id: UUID
    percentual_maximo_do_saldo: Decimal
    descricao: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


# ATA SCHEMAS
class AtaBase(BaseModel):
    numero_ata: str
    processo_administrativo: Optional[str] = None
    numero_pregao: Optional[str] = None
    orgao_gerenciador_id: UUID
    data_assinatura: Optional[date] = None
    data_publicacao: Optional[date] = None
    vigencia_meses: int = 12
    valor_total_global: Optional[Decimal] = None

class AtaCreate(AtaBase):
    pass

class AtaResponse(AtaBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)

class AtaDetailResponse(AtaResponse):
    orgao_gerenciador: OrgaoResponse
    grupos: List[GrupoLoteResponse] = []
    items: List[ItemAtaResponse] = []
    regras_carona: List[RegraLimiteCaronaResponse] = []
    model_config = ConfigDict(from_attributes=True)


# ITEM PEDIDO SCHEMAS
class ItemPedidoCreate(BaseModel):
    item_ata_id: UUID
    quantidade_solicitada: Decimal
    preco_unitario_no_pedido: Decimal

class ItemPedidoResponse(BaseModel):
    id: UUID
    pedido_id: UUID
    item_ata_id: UUID
    quantidade_solicitada: Decimal
    preco_unitario_no_pedido: Decimal
    subtotal: Decimal
    item_ata: ItemAtaResponse
    model_config = ConfigDict(from_attributes=True)


# PEDIDO SCHEMAS
class PedidoCreate(BaseModel):
    orgao_comprador_id: UUID
    ata_id: UUID
    # tipo_adesao removido: determinado automaticamente pelo backend
    # consultando item_ata_participante para cada item do pedido
    itens: List[ItemPedidoCreate]

class PedidoResponse(BaseModel):
    id: UUID
    orgao_comprador_id: UUID
    ata_id: UUID
    data_pedido: datetime
    tipo_adesao: TipoAdesao
    status: StatusPedido
    autorizado_por_usuario_id: Optional[UUID] = None
    data_autorizacao: Optional[datetime] = None
    justificativa_rejeicao: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class PedidoDetailResponse(PedidoResponse):
    orgao_comprador: OrgaoResponse
    itens: List[ItemPedidoResponse] = []
    model_config = ConfigDict(from_attributes=True)


# VIEW SALDO ITEM ATA SCHEMAS
class VwSaldoItemAtaResponse(BaseModel):
    id: UUID
    ata_id: UUID
    fornecedor_id: UUID
    quantidade_total_ofertada: Decimal
    quantidade_consumida_participantes: Decimal
    quantidade_consumida_caronas: Decimal
    quantidade_consumida: Decimal
    quantidade_saldo_disponivel: Decimal
    model_config = ConfigDict(from_attributes=True)


# WORKFLOW STATUS UPDATE SCHEMAS
class OrderStatusUpdate(BaseModel):
    status: StatusPedido
    justificativa_rejeicao: Optional[str] = None
    autorizado_por_usuario_id: Optional[UUID] = None


# NESTED ATA CREATION SCHEMAS
class ItemAtaCreateNested(BaseModel):
    grupo_numero: Optional[str] = None  # Matches a numero_grupo in the same payload
    fornecedor_id: UUID
    numero_item: Optional[str] = None
    descricao_especificacao: str
    unidade_medida: Optional[str] = None
    marca_modelo: Optional[str] = None
    url_imagem: Optional[str] = None
    valor_unitario: Decimal
    quantidade_total_ofertada: Optional[Decimal] = None
    participantes: List[ItemAtaParticipanteCreateNested] = []

class GrupoLoteCreateNested(BaseModel):
    numero_grupo: str
    descricao: Optional[str] = None

class RegraLimiteCaronaCreateNested(BaseModel):
    percentual_maximo_do_saldo: Decimal
    descricao: Optional[str] = None

class AtaCreateNested(BaseModel):
    numero_ata: str
    processo_administrativo: Optional[str] = None
    numero_pregao: Optional[str] = None
    orgao_gerenciador_id: UUID
    data_assinatura: Optional[date] = None
    data_publicacao: Optional[date] = None
    vigencia_meses: int = 12
    valor_total_global: Optional[Decimal] = None
    
    grupos: List[GrupoLoteCreateNested] = []
    items: List[ItemAtaCreateNested] = []
    regras_carona: List[RegraLimiteCaronaCreateNested] = []


# ITEM SEARCH RESPONSE (MARKETPLACE CATALOG VITRINE)
class ItemSearchResponse(BaseModel):
    id: UUID
    numero_item: Optional[str] = None
    descricao_especificacao: str
    unidade_medida: Optional[str] = None
    marca_modelo: Optional[str] = None
    url_imagem: Optional[str] = None
    valor_unitario: Decimal
    
    # Balances
    quantidade_total_ofertada: Decimal
    quantidade_saldo_disponivel: Decimal
    
    # Parent context
    fornecedor: FornecedorResponse
    ata: AtaResponse
    grupo: Optional[GrupoLoteResponse] = None
    
    model_config = ConfigDict(from_attributes=True)


# AUTHENTICATION SCHEMAS
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    usuario_id: Optional[UUID] = None
    email: Optional[str] = None
    papel: Optional[PapelUsuario] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    id: UUID
    email: str
    papel: PapelUsuario
    orgao_id: Optional[UUID] = None
    fornecedor_id: Optional[UUID] = None


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    papel: PapelUsuario
    orgao_id: Optional[UUID] = None
    fornecedor_id: Optional[UUID] = None


class UserResponse(BaseModel):
    id: UUID
    email: str
    papel: PapelUsuario
    orgao_id: Optional[UUID] = None
    fornecedor_id: Optional[UUID] = None
    
    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    papel: Optional[PapelUsuario] = None
    orgao_id: Optional[UUID] = None
    fornecedor_id: Optional[UUID] = None


class ItemAtaUpdate(BaseModel):
    descricao_especificacao: Optional[str] = None
    unidade_medida: Optional[str] = None
    marca_modelo: Optional[str] = None
    url_imagem: Optional[str] = None
    valor_unitario: Optional[Decimal] = None
    quantidade_total_ofertada: Optional[Decimal] = None


# ATA MONITORING SCHEMAS
class ItemAtaParticipanteMonitorResponse(BaseModel):
    orgao_id: UUID
    nome_orgao: str
    cnpj_orgao: str
    quantidade_planejada: Decimal
    quantidade_consumida: Decimal

class ItemAtaMonitorResponse(BaseModel):
    id: UUID
    numero_item: Optional[str] = None
    descricao_especificacao: str
    unidade_medida: Optional[str] = None
    marca_modelo: Optional[str] = None
    valor_unitario: Decimal
    fornecedor_razao_social: str
    quantidade_total_ofertada: Decimal
    quantidade_consumida: Decimal
    quantidade_saldo_disponivel: Decimal
    quantidade_consumida_participantes: Decimal
    quantidade_consumida_caronas: Decimal
    participantes: List[ItemAtaParticipanteMonitorResponse] = []

class AtaMonitorResponse(BaseModel):
    id: UUID
    numero_ata: str
    processo_administrativo: Optional[str] = None
    numero_pregao: Optional[str] = None
    data_assinatura: Optional[date] = None
    data_publicacao: Optional[date] = None
    vigencia_meses: int
    valor_total_global: Optional[Decimal] = None
    orgao_gerenciador_nome: str
    orgao_gerenciador_cnpj: str
    items: List[ItemAtaMonitorResponse] = []



