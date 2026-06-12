-- ============================================================================
-- BIAP - Business Intelligence and Procurement Platform
-- Schema de Criação de Banco de Dados
-- ============================================================================

-- Criar schema
CREATE SCHEMA IF NOT EXISTS "public";

-- ============================================================================
-- 1. TIPOS ENUM (Custom Types)
-- ============================================================================

CREATE TYPE "public".papel_usuario AS ENUM (
    'ADMIN_GERENCIADOR',
    'COMPRADOR',
    'FORNECEDOR'
);

CREATE TYPE "public".tipo_orgao AS ENUM (
    'FEDERAL',
    'ESTADUAL',
    'MUNICIPAL'
);

CREATE TYPE "public".tipo_adesao AS ENUM (
    'DIRETA',
    'CARONA'
);

CREATE TYPE "public".status_pedido AS ENUM (
    'PENDENTE',
    'AUTORIZADO',
    'REJEITADO',
    'EMITIDO'
);

-- ============================================================================
-- 2. TABELAS BASE (sem dependências externas)
-- ============================================================================

-- Tabela: Fornecedor
CREATE TABLE "public".fornecedor
(
    id                 UUID DEFAULT gen_random_uuid() NOT NULL,
    cnpj               VARCHAR(18)                    NOT NULL,
    razao_social       VARCHAR(200)                   NOT NULL,
    endereco           TEXT,
    nome_representante VARCHAR(100),
    cpf_representante  VARCHAR(14),
    telefone           VARCHAR(20),
    email              VARCHAR(100),

    CONSTRAINT fornecedor_pkey PRIMARY KEY (id),
    CONSTRAINT fornecedor_cnpj_key UNIQUE (cnpj)
);

-- Tabela: Órgão
CREATE TABLE "public".orgao
(
    id       UUID DEFAULT gen_random_uuid() NOT NULL,
    cnpj     VARCHAR(18)                    NOT NULL,
    nome     VARCHAR(200)                   NOT NULL,
    tipo     "public".tipo_orgao            NOT NULL,
    endereco TEXT,

    CONSTRAINT orgao_pkey PRIMARY KEY (id),
    CONSTRAINT orgao_cnpj_key UNIQUE (cnpj)
);

-- Tabela: Usuário
CREATE TABLE "public".usuario
(
    id            UUID DEFAULT gen_random_uuid() NOT NULL,
    email         VARCHAR(100)                   NOT NULL,
    senha_hash    VARCHAR(255)                   NOT NULL,
    orgao_id      UUID,
    fornecedor_id UUID,
    papel         "public".papel_usuario         NOT NULL,

    CONSTRAINT usuario_pkey PRIMARY KEY (id),
    CONSTRAINT usuario_email_key UNIQUE (email),
    CONSTRAINT usuario_email_check CHECK (email ~* '^[^@\s]+@[^@\s]+\.[^@\s]+$'
) ,
    CONSTRAINT chk_usuario_vinculo CHECK (
        (papel = 'FORNECEDOR'::"public".papel_usuario AND fornecedor_id IS NOT NULL AND orgao_id IS NULL)
        OR
        (papel = ANY(ARRAY['ADMIN_GERENCIADOR'::"public".papel_usuario, 'COMPRADOR'::"public".papel_usuario]) AND orgao_id IS NOT NULL AND fornecedor_id IS NULL)
    ),
    
    CONSTRAINT usuario_fornecedor_id_fkey FOREIGN KEY (fornecedor_id) REFERENCES "public".fornecedor(id),
    CONSTRAINT usuario_orgao_id_fkey FOREIGN KEY (orgao_id) REFERENCES "public".orgao(id)
);

-- ============================================================================
-- 3. TABELAS DE NEGÓCIO (ATA e relacionadas)
-- ============================================================================

-- Tabela: ATA (Ata de Registro de Preços)
CREATE TABLE "public".ata
(
    id                      UUID     DEFAULT gen_random_uuid() NOT NULL,
    numero_ata              VARCHAR(50)                        NOT NULL,
    processo_administrativo VARCHAR(100),
    numero_pregao           VARCHAR(50),
    orgao_gerenciador_id    UUID                               NOT NULL,
    data_assinatura         DATE,
    data_publicacao         DATE,
    vigencia_meses          SMALLINT DEFAULT 12                NOT NULL,
    valor_total_global      DECIMAL(15, 2),

    CONSTRAINT ata_pkey PRIMARY KEY (id),
    CONSTRAINT ata_numero_ata_key UNIQUE (numero_ata),
    CONSTRAINT ata_vigencia_meses_check CHECK (vigencia_meses > 0),
    CONSTRAINT ata_orgao_gerenciador_id_fkey FOREIGN KEY (orgao_gerenciador_id) REFERENCES "public".orgao (id)
);

-- Índice para buscar ATAs por órgão gerenciador
CREATE INDEX idx_ata_orgao_gerenciador ON "public".ata USING BTREE (orgao_gerenciador_id);

-- Tabela: Grupo de Lote
CREATE TABLE "public".grupo_lote
(
    id                   UUID DEFAULT gen_random_uuid() NOT NULL,
    ata_id               UUID                           NOT NULL,
    numero_grupo         VARCHAR(20),
    descricao            TEXT,
    orgao_id             UUID,                          -- Órgão participante deste lote (NULL = item isolado/sem participante definido)
    quantidade_planejada DECIMAL(15, 4),                -- Cota planejada pelo órgão para os itens deste lote

    CONSTRAINT grupo_lote_pkey PRIMARY KEY (id),
    CONSTRAINT grupo_lote_quantidade_check CHECK (quantidade_planejada IS NULL OR quantidade_planejada > 0),
    CONSTRAINT grupo_lote_ata_id_fkey FOREIGN KEY (ata_id) REFERENCES "public".ata (id) ON DELETE CASCADE,
    CONSTRAINT grupo_lote_orgao_id_fkey FOREIGN KEY (orgao_id) REFERENCES "public".orgao (id)
);

-- Índice para buscar grupos por ATA
CREATE INDEX idx_grupo_lote_ata   ON "public".grupo_lote USING BTREE (ata_id);
CREATE INDEX idx_grupo_lote_orgao ON "public".grupo_lote USING BTREE (orgao_id);

-- Tabela: Item da ATA
CREATE TABLE "public".item_ata
(
    id                        UUID DEFAULT gen_random_uuid() NOT NULL,
    ata_id                    UUID                           NOT NULL,
    grupo_id                  UUID,
    fornecedor_id             UUID                           NOT NULL,
    numero_item               VARCHAR(20),
    descricao_especificacao   TEXT                           NOT NULL,
    unidade_medida            VARCHAR(10),
    marca_modelo              VARCHAR(100),
    valor_unitario            DECIMAL(15, 2)                 NOT NULL,
    quantidade_total_ofertada DECIMAL(15, 4)                 NOT NULL,

    CONSTRAINT item_ata_pkey PRIMARY KEY (id),
    CONSTRAINT item_ata_quantidade_total_ofertada_check CHECK (quantidade_total_ofertada >= 0),
    CONSTRAINT item_ata_valor_unitario_check CHECK (valor_unitario >= 0),
    CONSTRAINT item_ata_ata_id_fkey FOREIGN KEY (ata_id) REFERENCES "public".ata (id),
    CONSTRAINT item_ata_grupo_id_fkey FOREIGN KEY (grupo_id) REFERENCES "public".grupo_lote (id),
    CONSTRAINT item_ata_fornecedor_id_fkey FOREIGN KEY (fornecedor_id) REFERENCES "public".fornecedor (id)
);

-- Índices para Item da ATA
CREATE INDEX idx_item_ata_ata ON "public".item_ata USING BTREE (ata_id);
CREATE INDEX idx_item_ata_fornecedor ON "public".item_ata USING BTREE (fornecedor_id);
CREATE INDEX idx_item_ata_fts ON "public".item_ata USING GIN (to_tsvector('portuguese', descricao_especificacao));

-- Tabela: Regra de Limite Carona
CREATE TABLE "public".regra_limite_carona
(
    id                         UUID DEFAULT gen_random_uuid() NOT NULL,
    ata_id                     UUID                           NOT NULL,
    percentual_maximo_do_saldo DECIMAL(5, 2)                  NOT NULL,
    descricao                  TEXT,

    CONSTRAINT regra_limite_carona_pkey PRIMARY KEY (id),
    CONSTRAINT regra_limite_carona_percentual_maximo_do_saldo_check CHECK (
        percentual_maximo_do_saldo > 0 AND percentual_maximo_do_saldo <= 200
        ),
    CONSTRAINT regra_limite_carona_ata_id_fkey FOREIGN KEY (ata_id) REFERENCES "public".ata (id) ON DELETE CASCADE
);

-- Índice para Regra de Limite Carona
CREATE INDEX idx_regra_limite_carona_ata ON "public".regra_limite_carona USING BTREE (ata_id);

-- ============================================================================
-- 4. TABELAS DE PEDIDOS
-- ============================================================================

-- Tabela: Pedido
CREATE TABLE "public".pedido
(
    id                        UUID                   DEFAULT gen_random_uuid() NOT NULL,
    orgao_comprador_id        UUID                                             NOT NULL,
    ata_id                    UUID                                             NOT NULL,
    data_pedido               TIMESTAMPTZ            DEFAULT CURRENT_TIMESTAMP NOT NULL,
    tipo_adesao               "public".tipo_adesao                             NOT NULL,
    status                    "public".status_pedido DEFAULT 'PENDENTE'        NOT NULL,
    autorizado_por_usuario_id UUID,
    data_autorizacao          TIMESTAMPTZ,
    justificativa_rejeicao    TEXT,

    CONSTRAINT pedido_pkey PRIMARY KEY (id),
    CONSTRAINT chk_pedido_rejeicao CHECK (
        status <> 'REJEITADO'::"public".status_pedido OR justificativa_rejeicao IS NOT NULL
) ,
    CONSTRAINT pedido_orgao_comprador_id_fkey FOREIGN KEY (orgao_comprador_id) REFERENCES "public".orgao(id),
    CONSTRAINT pedido_ata_id_fkey FOREIGN KEY (ata_id) REFERENCES "public".ata(id),
    CONSTRAINT pedido_autorizado_por_usuario_id_fkey FOREIGN KEY (autorizado_por_usuario_id) REFERENCES "public".usuario(id)
);

-- Índices para Pedido
CREATE INDEX idx_pedido_status ON "public".pedido USING BTREE (status);
CREATE INDEX idx_pedido_orgao ON "public".pedido USING BTREE (orgao_comprador_id);
CREATE INDEX idx_pedido_ata ON "public".pedido USING BTREE (ata_id);

-- Tabela: Item do Pedido
CREATE TABLE "public".item_pedido
(
    id                       UUID DEFAULT gen_random_uuid() NOT NULL,
    pedido_id                UUID                           NOT NULL,
    item_ata_id              UUID                           NOT NULL,
    quantidade_solicitada    DECIMAL(15, 4)                 NOT NULL,
    preco_unitario_no_pedido DECIMAL(15, 2)                 NOT NULL,
    subtotal                 DECIMAL(15, 2) GENERATED ALWAYS AS (quantidade_solicitada * preco_unitario_no_pedido) STORED,

    CONSTRAINT item_pedido_pkey PRIMARY KEY (id),
    CONSTRAINT item_pedido_pedido_id_item_ata_id_key UNIQUE (pedido_id, item_ata_id),
    CONSTRAINT item_pedido_quantidade_solicitada_check CHECK (quantidade_solicitada > 0),
    CONSTRAINT item_pedido_preco_unitario_no_pedido_check CHECK (preco_unitario_no_pedido >= 0),
    CONSTRAINT item_pedido_pedido_id_fkey FOREIGN KEY (pedido_id) REFERENCES "public".pedido (id),
    CONSTRAINT item_pedido_item_ata_id_fkey FOREIGN KEY (item_ata_id) REFERENCES "public".item_ata (id)
);

-- Índices para Item do Pedido
CREATE INDEX idx_item_pedido_pedido ON "public".item_pedido USING BTREE (pedido_id);
CREATE INDEX idx_item_pedido_item ON "public".item_pedido USING BTREE (item_ata_id);

-- ============================================================================
-- 5. VIEWS
-- ============================================================================

-- View: Saldo Disponível por Item da ATA (com divisão Participante vs. Carona)
CREATE
OR REPLACE VIEW "public".vw_saldo_item_ata AS
SELECT
    ia.id,
    ia.ata_id,
    ia.fornecedor_id,
    ia.quantidade_total_ofertada,

    -- Consumo total de pedidos DIRETA (participantes oficiais)
    COALESCE(SUM(ip.quantidade_solicitada) FILTER (
        WHERE p.tipo_adesao = 'DIRETA'::"public".tipo_adesao
    ), 0) AS quantidade_consumida_participantes,

    -- Consumo total de pedidos CARONA (órgãos externos)
    COALESCE(SUM(ip.quantidade_solicitada) FILTER (
        WHERE p.tipo_adesao = 'CARONA'::"public".tipo_adesao
    ), 0) AS quantidade_consumida_caronas,

    -- Consumo total geral (DIRETA + CARONA)
    COALESCE(SUM(ip.quantidade_solicitada), 0) AS quantidade_consumida,

    -- Saldo físico restante
    (ia.quantidade_total_ofertada - COALESCE(SUM(ip.quantidade_solicitada), 0)) AS quantidade_saldo_disponivel

FROM item_ata ia
    LEFT JOIN item_pedido ip ON (ip.item_ata_id = ia.id)
    LEFT JOIN pedido p ON (
        p.id = ip.pedido_id
        AND p.status = ANY (ARRAY[
            'AUTORIZADO'::"public".status_pedido,
            'EMITIDO'::"public".status_pedido
        ])
    )
GROUP BY ia.id, ia.ata_id, ia.fornecedor_id, ia.quantidade_total_ofertada;

-- ============================================================================
-- FIM DO SCHEMA
-- ============================================================================