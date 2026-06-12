from sqlalchemy import Column, String, ForeignKey, Integer, Numeric, Date, DateTime, Text, Enum, Computed
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.database import Base

# Model: Fornecedor
class Fornecedor(Base):
    __tablename__ = "fornecedor"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cnpj = Column(String(18), unique=True, nullable=False)
    razao_social = Column(String(200), nullable=False)
    endereco = Column(Text)
    nome_representante = Column(String(100))
    cpf_representante = Column(String(14))
    telefone = Column(String(20))
    email = Column(String(100))

    # Relationships
    users = relationship("Usuario", back_populates="fornecedor")
    items = relationship("ItemAta", back_populates="fornecedor")


# Model: Órgão
class Orgao(Base):
    __tablename__ = "orgao"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cnpj = Column(String(18), unique=True, nullable=False)
    nome = Column(String(200), nullable=False)
    tipo = Column(Enum("FEDERAL", "ESTADUAL", "MUNICIPAL", name="tipo_orgao"), nullable=False)
    endereco = Column(Text)

    # Relationships
    users = relationship("Usuario", back_populates="orgao")
    atas = relationship("Ata", back_populates="orgao_gerenciador")
    pedidos = relationship("Pedido", back_populates="orgao_comprador")


# Model: Usuário
class Usuario(Base):
    __tablename__ = "usuario"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(100), unique=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    orgao_id = Column(UUID(as_uuid=True), ForeignKey("orgao.id"), nullable=True)
    fornecedor_id = Column(UUID(as_uuid=True), ForeignKey("fornecedor.id"), nullable=True)
    papel = Column(Enum("ADMIN_GERENCIADOR", "COMPRADOR", "FORNECEDOR", name="papel_usuario"), nullable=False)

    # Relationships
    orgao = relationship("Orgao", back_populates="users")
    fornecedor = relationship("Fornecedor", back_populates="users")
    pedidos_autorizados = relationship("Pedido", back_populates="autorizador")


# Model: ATA
class Ata(Base):
    __tablename__ = "ata"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    numero_ata = Column(String(50), unique=True, nullable=False)
    processo_administrativo = Column(String(100))
    numero_pregao = Column(String(50))
    orgao_gerenciador_id = Column(UUID(as_uuid=True), ForeignKey("orgao.id"), nullable=False)
    data_assinatura = Column(Date)
    data_publicacao = Column(Date)
    vigencia_meses = Column(Integer, nullable=False, default=12)
    valor_total_global = Column(Numeric(15, 2))

    # Relationships
    orgao_gerenciador = relationship("Orgao", back_populates="atas")
    grupos = relationship("GrupoLote", back_populates="ata", cascade="all, delete-orphan")
    items = relationship("ItemAta", back_populates="ata")
    regras_carona = relationship("RegraLimiteCarona", back_populates="ata", cascade="all, delete-orphan")
    pedidos = relationship("Pedido", back_populates="ata")


# Model: Grupo Lote
class GrupoLote(Base):
    __tablename__ = "grupo_lote"

    id                   = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ata_id               = Column(UUID(as_uuid=True), ForeignKey("ata.id", ondelete="CASCADE"), nullable=False)
    numero_grupo         = Column(String(20))
    descricao            = Column(Text)
    orgao_id             = Column(UUID(as_uuid=True), ForeignKey("orgao.id"), nullable=True)
    quantidade_planejada = Column(Numeric(15, 4), nullable=True)

    # Relationships
    ata   = relationship("Ata", back_populates="grupos")
    items = relationship("ItemAta", back_populates="grupo")
    orgao = relationship("Orgao")


# Model: Item ATA
class ItemAta(Base):
    __tablename__ = "item_ata"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ata_id = Column(UUID(as_uuid=True), ForeignKey("ata.id"), nullable=False)
    grupo_id = Column(UUID(as_uuid=True), ForeignKey("grupo_lote.id"), nullable=True)
    fornecedor_id = Column(UUID(as_uuid=True), ForeignKey("fornecedor.id"), nullable=False)
    numero_item = Column(String(20))
    descricao_especificacao = Column(Text, nullable=False)
    unidade_medida = Column(String(10))
    marca_modelo = Column(String(100))
    url_imagem = Column(String(255), nullable=True)
    valor_unitario = Column(Numeric(15, 2), nullable=False)
    quantidade_total_ofertada = Column(Numeric(15, 4), nullable=False)

    # Relationships
    ata = relationship("Ata", back_populates="items")
    grupo = relationship("GrupoLote", back_populates="items")
    fornecedor = relationship("Fornecedor", back_populates="items")
    itens_pedido = relationship("ItemPedido", back_populates="item_ata")


# Model: Regra Limite Carona
class RegraLimiteCarona(Base):
    __tablename__ = "regra_limite_carona"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ata_id = Column(UUID(as_uuid=True), ForeignKey("ata.id", ondelete="CASCADE"), nullable=False)
    percentual_maximo_do_saldo = Column(Numeric(5, 2), nullable=False)
    descricao = Column(Text)

    # Relationships
    ata = relationship("Ata", back_populates="regras_carona")


# Model: Pedido
class Pedido(Base):
    __tablename__ = "pedido"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    orgao_comprador_id = Column(UUID(as_uuid=True), ForeignKey("orgao.id"), nullable=False)
    ata_id = Column(UUID(as_uuid=True), ForeignKey("ata.id"), nullable=False)
    data_pedido = Column(DateTime(timezone=True), nullable=False)
    tipo_adesao = Column(Enum("DIRETA", "CARONA", name="tipo_adesao"), nullable=False)
    status = Column(Enum("PENDENTE", "AUTORIZADO", "REJEITADO", "EMITIDO", name="status_pedido"), nullable=False, default="PENDENTE")
    autorizado_por_usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuario.id"), nullable=True)
    data_autorizacao = Column(DateTime(timezone=True), nullable=True)
    justificativa_rejeicao = Column(Text, nullable=True)

    # Relationships
    orgao_comprador = relationship("Orgao", back_populates="pedidos")
    ata = relationship("Ata", back_populates="pedidos")
    autorizador = relationship("Usuario", back_populates="pedidos_autorizados")
    itens = relationship("ItemPedido", back_populates="pedido", cascade="all, delete-orphan")


# Model: Item Pedido
class ItemPedido(Base):
    __tablename__ = "item_pedido"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pedido_id = Column(UUID(as_uuid=True), ForeignKey("pedido.id"), nullable=False)
    item_ata_id = Column(UUID(as_uuid=True), ForeignKey("item_ata.id"), nullable=False)
    quantidade_solicitada = Column(Numeric(15, 4), nullable=False)
    preco_unitario_no_pedido = Column(Numeric(15, 2), nullable=False)
    subtotal = Column(Numeric(15, 2), Computed("quantidade_solicitada * preco_unitario_no_pedido"), nullable=False)

    # Relationships
    pedido = relationship("Pedido", back_populates="itens")
    item_ata = relationship("ItemAta", back_populates="itens_pedido")


# Model: Saldo Disponível por Item da ATA (Mapeado para a View)
class VwSaldoItemAta(Base):
    __tablename__ = "vw_saldo_item_ata"

    # Definimos chaves primárias fakes no SQLAlchemy para que ele possa mapear a View
    id = Column(UUID(as_uuid=True), primary_key=True)
    ata_id = Column(UUID(as_uuid=True))
    fornecedor_id = Column(UUID(as_uuid=True))
    quantidade_total_ofertada = Column(Numeric(15, 4))
    quantidade_consumida_participantes = Column(Numeric(15, 4))
    quantidade_consumida_caronas = Column(Numeric(15, 4))
    quantidade_consumida = Column(Numeric(15, 4))
    quantidade_saldo_disponivel = Column(Numeric(15, 4))
