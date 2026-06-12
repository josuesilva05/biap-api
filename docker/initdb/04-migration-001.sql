-- ============================================================================
-- BIAP — Migration 001: Estender grupo_lote com orgao_id e quantidade_planejada
--                        e atualizar vw_saldo_item_ata com split DIRETA/CARONA
-- Execute como arphub_admin quando o banco já existir com schema antigo.
-- ============================================================================

-- 1. Adicionar colunas à grupo_lote
ALTER TABLE grupo_lote
    ADD COLUMN IF NOT EXISTS orgao_id             UUID REFERENCES orgao(id),
    ADD COLUMN IF NOT EXISTS quantidade_planejada DECIMAL(15, 4)
        CHECK (quantidade_planejada IS NULL OR quantidade_planejada > 0);

-- Índice de busca por órgão participante
CREATE INDEX IF NOT EXISTS idx_grupo_lote_orgao ON grupo_lote(orgao_id);

-- 2. Recriar view com split Participante vs. Carona
DROP VIEW IF EXISTS vw_saldo_item_ata;

CREATE VIEW "public".vw_saldo_item_ata AS
SELECT
    ia.id,
    ia.ata_id,
    ia.fornecedor_id,
    ia.quantidade_total_ofertada,

    -- Consumo de pedidos DIRETA (participantes oficiais)
    COALESCE(SUM(ip.quantidade_solicitada) FILTER (
        WHERE p.tipo_adesao = 'DIRETA'::"public".tipo_adesao
    ), 0) AS quantidade_consumida_participantes,

    -- Consumo de pedidos CARONA (órgãos externos)
    COALESCE(SUM(ip.quantidade_solicitada) FILTER (
        WHERE p.tipo_adesao = 'CARONA'::"public".tipo_adesao
    ), 0) AS quantidade_consumida_caronas,

    -- Consumo total (DIRETA + CARONA)
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

-- 3. Atualizar constraint de percentual de carona (permitir até 200% = 2x)
ALTER TABLE regra_limite_carona
    DROP CONSTRAINT IF EXISTS regra_limite_carona_percentual_maximo_do_saldo_check;

ALTER TABLE regra_limite_carona
    ADD CONSTRAINT regra_limite_carona_percentual_maximo_do_saldo_check
    CHECK (percentual_maximo_do_saldo > 0 AND percentual_maximo_do_saldo <= 200);

-- 4. Remover tabelas legadas redundantes (item_ata_participante, grupo_lote_participante)
DROP TABLE IF EXISTS item_ata_participante CASCADE;
DROP TABLE IF EXISTS grupo_lote_participante CASCADE;

