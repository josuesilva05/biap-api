-- ============================================================================
-- BIAP — Migration 002: Criar tabela item_ata_participante e limpar grupo_lote
-- ============================================================================

-- 1. Criar a nova tabela item_ata_participante
CREATE TABLE IF NOT EXISTS "public".item_ata_participante (
    id UUID DEFAULT gen_random_uuid() NOT NULL,
    item_ata_id UUID NOT NULL,
    orgao_id UUID NOT NULL,
    quantidade_planejada DECIMAL(15, 4) NOT NULL CHECK (quantidade_planejada > 0),
    
    CONSTRAINT item_ata_participante_pkey PRIMARY KEY (id),
    CONSTRAINT item_ata_participante_item_ata_id_fkey FOREIGN KEY (item_ata_id) REFERENCES "public".item_ata (id) ON DELETE CASCADE,
    CONSTRAINT item_ata_participante_orgao_id_fkey FOREIGN KEY (orgao_id) REFERENCES "public".orgao (id),
    CONSTRAINT item_ata_participante_item_ata_id_orgao_id_key UNIQUE (item_ata_id, orgao_id)
);

-- Índices de busca rápidos
CREATE INDEX IF NOT EXISTS idx_item_ata_participante_item ON "public".item_ata_participante USING BTREE (item_ata_id);
CREATE INDEX IF NOT EXISTS idx_item_ata_participante_orgao ON "public".item_ata_participante USING BTREE (orgao_id);

-- 2. Migrar dados existentes de grupo_lote para item_ata_participante se houver
INSERT INTO "public".item_ata_participante (item_ata_id, orgao_id, quantidade_planejada)
SELECT ia.id, gl.orgao_id, gl.quantidade_planejada
FROM "public".item_ata ia
JOIN "public".grupo_lote gl ON ia.grupo_id = gl.id
WHERE gl.orgao_id IS NOT NULL AND gl.quantidade_planejada IS NOT NULL
ON CONFLICT (item_ata_id, orgao_id) DO NOTHING;

-- 3. Remover colunas obsoletas da tabela grupo_lote
ALTER TABLE "public".grupo_lote
    DROP COLUMN IF EXISTS orgao_id,
    DROP COLUMN IF EXISTS quantidade_planejada;
