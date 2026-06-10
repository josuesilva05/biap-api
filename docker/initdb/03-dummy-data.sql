-- ============================================================================
-- BIAP - Business Intelligence and Procurement Platform
-- Scripts para Inserção Massiva de Dados Fictícios (Dummy Data)
-- ============================================================================

BEGIN;

-- Limpar dados anteriores para evitar duplicações/conflitos ao reinicializar
TRUNCATE TABLE "public".item_pedido CASCADE;
TRUNCATE TABLE "public".pedido CASCADE;
TRUNCATE TABLE "public".regra_limite_carona CASCADE;
TRUNCATE TABLE "public".item_ata CASCADE;
TRUNCATE TABLE "public".grupo_lote CASCADE;
TRUNCATE TABLE "public".ata CASCADE;
TRUNCATE TABLE "public".usuario CASCADE;
TRUNCATE TABLE "public".orgao CASCADE;
TRUNCATE TABLE "public".fornecedor CASCADE;

-- 1. POPULAR FORNECEDORES (10 registros)
INSERT INTO "public".fornecedor (id, cnpj, razao_social, endereco, nome_representante, cpf_representante, telefone, email)
VALUES
  ('d7b5f543-982c-4b53-8b77-d7d8e62d4701', '12.345.678/0001-90', 'Acme Tecnologia Ltda', 'Av. Paulista, 1000 - Bela Vista, São Paulo - SP', 'Carlos Eduardo Silva', '123.456.789-00', '(11) 98765-4321', 'vendas@acmetec.com.br'),
  ('e1bfdc81-2292-4914-9988-518df9df8c82', '98.765.432/0001-10', 'Papelaria e Distribuidora Rio Branco', 'Rua Riachuelo, 450 - Centro, Rio de Janeiro - RJ', 'Mariana Oliveira Costa', '987.654.321-11', '(21) 2233-4455', 'licitacoes@riobrancopapelaria.com.br'),
  ('a57f58bb-c419-4820-9411-9683935dbdf3', '45.678.901/0001-22', 'Mobiliário Design S.A.', 'Av. das Nações, 2500 - Distrito Industrial, Curitiba - PR', 'Roberto Alencar Melo', '456.789.012-33', '(41) 3344-5566', 'corporativo@designmobiliario.com.br'),
  ('6b8b0e77-5054-47c3-88bb-83df3ee08d04', '33.111.222/0001-33', 'Alfa Construtora e Incorporadora Eireli', 'Rua das Obras, 12 - Setor Industrial, Goiânia - GO', 'Geraldo Magela Fontes', '333.444.555-66', '(62) 3222-1100', 'licita@alfaconstrutora.com.br'),
  ('a5db2291-fe88-4c8d-aa34-11cf9a77cd05', '55.222.333/0001-44', 'NutriVida Distribuidora de Alimentos', 'Av. Brasil, 4500 - Bonsucesso, Rio de Janeiro - RJ', 'Ana Beatriz Souza', '555.666.777-88', '(21) 3888-9999', 'comercial@nutrivida.com.br'),
  ('1f2a3b4c-5d6e-7f8a-9b0c-1d2e3f4a5b6c', '77.333.444/0001-55', 'MedCorp Equipamentos Hospitalares', 'Av. Contorno, 8000 - Lourdes, Belo Horizonte - MG', 'Fernanda Lima Dias', '777.888.999-00', '(31) 3456-7890', 'vendas@medcorp.com.br'),
  ('7a8b9c0d-1e2f-3a4b-5c6d-7e8f9a0b1c2d', '88.444.555/0001-66', 'CleanForce Soluções em Limpeza', 'Rua dos Limpos, 101 - Jardim das Flores, Porto Alegre - RS', 'José Almir Guimarães', '888.999.000-11', '(51) 3211-4455', 'comercial@cleanforce.com.br'),
  ('3f4e5d6c-7b8a-9c0d-1e2f-3a4b5c6d7e8f', '11.555.666/0001-77', 'Lógica Softwares & Licenças', 'Rua Virtual, 404 - Tech Park, Florianópolis - SC', 'Patricia Nogueira Santos', '111.222.333-44', '(48) 3028-4040', 'gov@logicasoftware.com.br'),
  ('5d6e7f8a-9b0c-1d2e-3f4a-5b6c7d8e9f0a', '22.666.777/0001-88', 'AutoPeças Global Peças Ltda', 'Av. Industrial, 1200 - Distrito Industrial, Sorocaba - SP', 'Marcos Aurélio Prado', '222.333.444-55', '(15) 3224-5050', 'licita@globalpecas.com.br'),
  ('9b0c1d2e-3f4a-5b6c-7d8e-9f0a1b2c3d4e', '44.777.888/0001-99', 'SegurMax Monitoramento de Segurança', 'Rua Vigilante, 50 - Centro, Vitória - ES', 'Wanderley Cardoso Junior', '444.555.666-77', '(27) 3322-9900', 'licitacoes@segurmax.com.br')
ON CONFLICT (cnpj) DO NOTHING;

-- 2. POPULAR ÓRGÃOS PÚBLICOS (10 registros)
INSERT INTO "public".orgao (id, cnpj, nome, tipo, endereco)
VALUES
  ('f7a2ab53-b3c9-467a-9777-709de7483601', '00.394.460/0001-41', 'Ministério da Infraestrutura', 'FEDERAL', 'Esplanada dos Ministérios, Bloco R - Brasília - DF'),
  ('1b1388b8-b80c-4cc0-928e-0bdf60ff7c02', '46.374.500/0001-90', 'Secretaria Estadual de Saúde - SP', 'ESTADUAL', 'Av. Dr. Arnaldo, 351 - Pacaembu, São Paulo - SP'),
  ('762de6c4-722a-464a-bb91-88849b2f7003', '46.604.288/0001-83', 'Prefeitura Municipal de Campinas', 'MUNICIPAL', 'Av. Anchieta, 200 - Centro, Campinas - SP'),
  ('92a18b76-fe88-4432-82ef-dcf9a77fd204', '00.394.447/0001-92', 'Ministério da Educação', 'FEDERAL', 'Esplanada dos Ministérios, Bloco L - Brasília - DF'),
  ('8bcf8c7d-de45-4781-a9bc-fcdcf98d5c05', '51.174.001/0001-90', 'Tribunal de Justiça do Estado de SP', 'ESTADUAL', 'Praça da Sé, s/n - Centro, São Paulo - SP'),
  ('10af8d23-01ef-42d3-9bc4-7cf4a95df606', '58.200.111/0001-22', 'Prefeitura Municipal de Santos', 'MUNICIPAL', 'Praça Mauá, s/n - Centro, Santos - SP'),
  ('ac56b78d-90de-45f6-789a-01bcde234567', '00.394.499/0001-89', 'Ministério do Meio Ambiente', 'FEDERAL', 'Esplanada dos Ministérios, Bloco B - Brasília - DF'),
  ('bd78c90e-12fa-34bc-56de-789f01ab2345', '60.409.075/0001-52', 'Universidade Federal de São Paulo', 'FEDERAL', 'Rua Sena Madureira, 1500 - Vila Clementino, São Paulo - SP'),
  ('ce90d12f-34ab-56cd-789e-012ab34cd567', '42.498.600/0001-11', 'Secretaria Estadual de Segurança Pública - RJ', 'ESTADUAL', 'Praça Cristiano Otoni, s/n - Central do Brasil, Rio de Janeiro - RJ'),
  ('df01e23a-45bc-67de-8901-2345bc67de89', '13.927.801/0001-44', 'Prefeitura Municipal de Salvador', 'MUNICIPAL', 'Praça Thomé de Souza, s/n - Centro, Salvador - BA')
ON CONFLICT (cnpj) DO NOTHING;

-- 3. POPULAR USUÁRIOS (12 registros)
-- Senha de teste em texto plano para todos: "Senha123!"
INSERT INTO "public".usuario (id, email, senha_hash, orgao_id, fornecedor_id, papel)
VALUES
  ('3d8b5a76-96b6-45ef-bd98-7cf4a40df601', 'admin.infra@gov.br', '$2b$12$rQroQ0GGpdS/JgdZsg9LIOiQEWQUezJHKMP67WztNu3x/vTIwuggG', 'f7a2ab53-b3c9-467a-9777-709de7483601', NULL, 'ADMIN_GERENCIADOR'),
  ('6ee5367d-d45a-4712-9c4c-2234e402cf02', 'comprador.saude@sp.gov.br', '$2b$12$rQroQ0GGpdS/JgdZsg9LIOiQEWQUezJHKMP67WztNu3x/vTIwuggG', '1b1388b8-b80c-4cc0-928e-0bdf60ff7c02', NULL, 'COMPRADOR'),
  ('b8ef6c7d-e6b7-4c48-b4b3-c19df3bc7103', 'vendas@acmetec.com.br', '$2b$12$rQroQ0GGpdS/JgdZsg9LIOiQEWQUezJHKMP67WztNu3x/vTIwuggG', NULL, 'd7b5f543-982c-4b53-8b77-d7d8e62d4701', 'FORNECEDOR'),
  ('c7df812c-01ef-42d3-9bc4-7cf4a95df604', 'licita@riobrancopapelaria.com.br', '$2b$12$rQroQ0GGpdS/JgdZsg9LIOiQEWQUezJHKMP67WztNu3x/vTIwuggG', NULL, 'e1bfdc81-2292-4914-9988-518df9df8c82', 'FORNECEDOR'),
  ('12ab34cd-56ef-7890-1234-567890abcdef', 'gestor.mec@gov.br', '$2b$12$rQroQ0GGpdS/JgdZsg9LIOiQEWQUezJHKMP67WztNu3x/vTIwuggG', '92a18b76-fe88-4432-82ef-dcf9a77fd204', NULL, 'ADMIN_GERENCIADOR'),
  ('23bc45de-67f0-8901-2345-67890abcdef1', 'compras@campinas.sp.gov.br', '$2b$12$rQroQ0GGpdS/JgdZsg9LIOiQEWQUezJHKMP67WztNu3x/vTIwuggG', '762de6c4-722a-464a-bb91-88849b2f7003', NULL, 'COMPRADOR'),
  ('34cd56ef-78fa-9012-3456-7890abcdef12', 'compras@tjsp.jus.br', '$2b$12$rQroQ0GGpdS/JgdZsg9LIOiQEWQUezJHKMP67WztNu3x/vTIwuggG', '8bcf8c7d-de45-4781-a9bc-fcdcf98d5c05', NULL, 'COMPRADOR'),
  ('45de67f0-89ab-0123-4567-890abcdef123', 'licitacoes@santos.sp.gov.br', '$2b$12$rQroQ0GGpdS/JgdZsg9LIOiQEWQUezJHKMP67WztNu3x/vTIwuggG', '10af8d23-01ef-42d3-9bc4-7cf4a95df606', NULL, 'COMPRADOR'),
  ('56ef78fa-9000-1234-5678-90abcdef1234', 'comercial@designmobiliario.com.br', '$2b$12$rQroQ0GGpdS/JgdZsg9LIOiQEWQUezJHKMP67WztNu3x/vTIwuggG', NULL, 'a57f58bb-c419-4820-9411-9683935dbdf3', 'FORNECEDOR'),
  ('67f089ab-0100-2345-6789-0abcdef12345', 'comercial@nutrivida.com.br', '$2b$12$rQroQ0GGpdS/JgdZsg9LIOiQEWQUezJHKMP67WztNu3x/vTIwuggG', NULL, 'a5db2291-fe88-4c8d-aa34-11cf9a77cd05', 'FORNECEDOR'),
  ('78fa9000-12bc-3456-7890-abcdef123456', 'compras@unifesp.edu.br', '$2b$12$rQroQ0GGpdS/JgdZsg9LIOiQEWQUezJHKMP67WztNu3x/vTIwuggG', 'bd78c90e-12fa-34bc-56de-789f01ab2345', NULL, 'COMPRADOR'),
  ('89ab0100-23cd-4567-890a-bcdef1234567', 'comprador.seg@rj.gov.br', '$2b$12$rQroQ0GGpdS/JgdZsg9LIOiQEWQUezJHKMP67WztNu3x/vTIwuggG', 'ce90d12f-34ab-56cd-789e-012ab34cd567', NULL, 'COMPRADOR')
ON CONFLICT (email) DO NOTHING;

-- 4. POPULAR ATAS DE REGISTRO DE PREÇOS (6 registros)
INSERT INTO "public".ata (id, numero_ata, processo_administrativo, numero_pregao, orgao_gerenciador_id, data_assinatura, data_publicacao, vigencia_meses, valor_total_global)
VALUES
  ('931b26f5-56f8-4f98-b88a-dfcf1e77df01', 'ATA-001/2026', 'PA-2025-0043', 'PREGAO-002/2026', 'f7a2ab53-b3c9-467a-9777-709de7483601', '2026-01-15', '2026-01-17', 12, 1500000.00),
  ('02bf3532-6bf2-4148-8dfa-ef13efcf0f02', 'ATA-015/2026', 'PA-2025-1082', 'PREGAO-011/2026', '1b1388b8-b80c-4cc0-928e-0bdf60ff7c02', '2026-02-10', '2026-02-12', 12, 600000.00),
  ('3f7492c1-d4fe-482a-89a0-fcdcf9839403', 'ATA-008/2026', 'PA-2025-5020', 'PREGAO-005/2026', '92a18b76-fe88-4432-82ef-dcf9a77fd204', '2026-01-20', '2026-01-22', 12, 4500000.00),
  ('4a8f9d0c-12fa-34bc-56de-789f01ab2344', 'ATA-022/2026', 'PA-2025-0812', 'PREGAO-018/2026', '8bcf8c7d-de45-4781-a9bc-fcdcf98d5c05', '2026-02-15', '2026-02-16', 12, 350000.00),
  ('5b9e0f1d-23ab-45cd-67ef-890123456789', 'ATA-045/2026', 'PA-2025-2244', 'PREGAO-033/2026', 'ce90d12f-34ab-56cd-789e-012ab34cd567', '2026-03-01', '2026-03-02', 24, 850000.00),
  ('6c0f1a2b-34bc-56de-789f-012345678901', 'ATA-050/2026', 'PA-2026-0005', 'PREGAO-001/2026', '762de6c4-722a-464a-bb91-88849b2f7003', '2026-03-10', '2026-03-12', 12, 1200000.00);

-- 5. POPULAR GRUPOS/LOTES DAS ATAS (8 registros)
INSERT INTO "public".grupo_lote (id, ata_id, numero_grupo, descricao)
VALUES
  ('e5cf56f2-bf8f-4d92-bb82-fcf627072f01', '931b26f5-56f8-4f98-b88a-dfcf1e77df01', 'G-01', 'Equipamentos de Tecnologia da Informação (Hardwares)'),
  ('12ab45cd-67ef-8901-2345-67890abcdef1', '931b26f5-56f8-4f98-b88a-dfcf1e77df01', 'G-02', 'Mobiliário Corporativo de Escritório'),
  ('cf8d9101-de23-4567-8901-23456789abcd', '02bf3532-6bf2-4148-8dfa-ef13efcf0f02', 'G-01', 'Material de Escritório Geral e Papelaria'),
  ('fa98c0d1-01ef-42d3-9bc4-7cf4a95df604', '3f7492c1-d4fe-482a-89a0-fcdcf9839403', 'G-01', 'Dispositivos de Informática Educacionais (Alunos e Professores)'),
  ('db89e0f1-12fa-34bc-56de-789f01ab2345', '3f7492c1-d4fe-482a-89a0-fcdcf9839403', 'G-02', 'Licenciamento de Software Corporativo e Educacional'),
  ('ec90f1a2-23ab-45cd-67ef-890123456789', '4a8f9d0c-12fa-34bc-56de-789f01ab2344', 'G-01', 'Produtos de Higiene, Limpeza e Desinfecção Hospitalar/Corporativo'),
  ('fd01a2b3-34bc-56de-789f-012345678901', '5b9e0f1d-23ab-45cd-67ef-890123456789', 'G-01', 'Câmeras IP e NVRs para Monitoramento de Vias Públicas'),
  ('ae12b3c4-45cd-67ef-8901-234567890123', '6c0f1a2b-34bc-56de-789f-012345678901', 'G-01', 'Alimentos Perecíveis e Merenda Escolar Municipal');

-- 6. POPULAR ITENS DAS ATAS (25 registros)
INSERT INTO "public".item_ata (id, ata_id, grupo_id, fornecedor_id, numero_item, descricao_especificacao, unidade_medida, marca_modelo, valor_unitario, quantidade_total_ofertada)
VALUES
  -- ATA 001/2026 (Infraestrutura TI & Móveis)
  ('6df4ef1e-9df2-47ef-b924-f7b2e3e57f01', '931b26f5-56f8-4f98-b88a-dfcf1e77df01', 'e5cf56f2-bf8f-4d92-bb82-fcf627072f01', 'd7b5f543-982c-4b53-8b77-d7d8e62d4701', '01', 'Notebook Corporativo, Processador Intel Core i7, 16GB RAM, SSD 512GB NVMe, Tela 15.6 FHD, Windows 11 Pro', 'UN', 'Lenovo ThinkPad L15', 4500.00, 100.0000),
  ('41ef7de1-2aef-46e3-82ef-df93e7fdf002', '931b26f5-56f8-4f98-b88a-dfcf1e77df01', 'e5cf56f2-bf8f-4d92-bb82-fcf627072f01', 'd7b5f543-982c-4b53-8b77-d7d8e62d4701', '02', 'Monitor Profissional 27 polegadas 4K IPS, conexões HDMI, DisplayPort e USB-C, ajuste de altura e rotação pivot', 'UN', 'Dell U2723QE', 1800.00, 200.0000),
  ('9ef4a7d3-f093-4a11-884c-bdf19dff3003', '931b26f5-56f8-4f98-b88a-dfcf1e77df01', '12ab45cd-67ef-8901-2345-67890abcdef1', 'a57f58bb-c419-4820-9411-9683935dbdf3', '01', 'Cadeira de Escritório Ergonômica com regulagem de braço, suporte lombar ativo, rodízios anti-risco', 'UN', 'Flexform Tecton', 850.00, 150.0000),
  ('5ef678d2-45e3-4b6e-8ffc-df93e7fd0004', '931b26f5-56f8-4f98-b88a-dfcf1e77df01', '12ab45cd-67ef-8901-2345-67890abcdef1', 'a57f58bb-c419-4820-9411-9683935dbdf3', '02', 'Mesa em L para Escritório, tampo em MDF 25mm, estrutura metálica com calha para cabeamento estruturado', 'UN', 'Marelli Master', 1200.00, 100.0000),

  -- ATA 015/2026 (Saúde - Papelaria)
  ('ef890123-4567-8901-2345-67890abcdef1', '02bf3532-6bf2-4148-8dfa-ef13efcf0f02', 'cf8d9101-de23-4567-8901-23456789abcd', 'e1bfdc81-2292-4914-9988-518df9df8c82', '01', 'Papel A4 Sulfite Alvo 75g/m², caixa com 10 resmas de 500 folhas cada', 'CX', 'Chamex Office', 220.00, 1000.0000),
  ('bc234567-8901-2345-6789-0abcdef12345', '02bf3532-6bf2-4148-8dfa-ef13efcf0f02', 'cf8d9101-de23-4567-8901-23456789abcd', 'e1bfdc81-2292-4914-9988-518df9df8c82', '02', 'Pasta Suspensa Plástica reforçada para arquivo, pacote com 50 unidades, cor azul', 'PCT', 'Dello Pastas', 45.00, 2000.0000),

  -- ATA 008/2026 (MEC - Educacional TI)
  ('cd345678-9012-3456-7890-1234567890ab', '3f7492c1-d4fe-482a-89a0-fcdcf9839403', 'fa98c0d1-01ef-42d3-9bc4-7cf4a95df604', 'd7b5f543-982c-4b53-8b77-d7d8e62d4701', '01', 'Chromebook Educacional, processador Dual Core, 4GB RAM, 32GB eMMC, Tela 11.6 HD Touch, Chrome OS', 'UN', 'Samsung Chromebook 4', 1650.00, 2000.0000),
  ('de456789-0123-4567-8901-234567890abc', '3f7492c1-d4fe-482a-89a0-fcdcf9839403', 'fa98c0d1-01ef-42d3-9bc4-7cf4a95df604', 'd7b5f543-982c-4b53-8b77-d7d8e62d4701', '02', 'Tablet Educacional 10 polegadas, Octa Core, 64GB Armazenamento, 4GB RAM, com capa antichoque e caneta ativa', 'UN', 'Samsung Galaxy Tab A8', 1150.00, 3000.0000),
  ('ef567890-1234-5678-9012-34567890abcd', '3f7492c1-d4fe-482a-89a0-fcdcf9839403', 'db89e0f1-12fa-34bc-56de-789f01ab2345', '3f4e5d6c-7b8a-9c0d-1e2f-3a4b5c6d7e8f', '03', 'Licença de Sistema Operacional Windows 11 Pro Academic, licença perpétua para órgãos públicos', 'LIC', 'Microsoft Windows Pro', 250.00, 5000.0000),
  ('f0678901-2345-6789-0123-456789012abc', '3f7492c1-d4fe-482a-89a0-fcdcf9839403', 'db89e0f1-12fa-34bc-56de-789f01ab2345', '3f4e5d6c-7b8a-9c0d-1e2f-3a4b5c6d7e8f', '04', 'Licença anual para Suite de Escritório Office 365 A3 para Professores e Alunos', 'LIC', 'Microsoft Office 365', 180.00, 8000.0000),

  -- ATA 022/2026 (TJSP - Limpeza)
  ('a1789012-3456-7890-1234-567890123abc', '4a8f9d0c-12fa-34bc-56de-789f01ab2344', 'ec90f1a2-23ab-45cd-67ef-890123456789', '7a8b9c0d-1e2f-3a4b-5c6d-7e8f9a0b1c2d', '01', 'Álcool Etílico Antisséptico em Gel 70%, galão de 5 Litros para higienização geral', 'GL', 'Super Clean 70', 45.00, 1000.0000),
  ('b2890123-4567-8901-2345-678901234bcd', '4a8f9d0c-12fa-34bc-56de-789f01ab2344', 'ec90f1a2-23ab-45cd-67ef-890123456789', '7a8b9c0d-1e2f-3a4b-5c6d-7e8f9a0b1c2d', '02', 'Papel Toalha Interfolhado, folha dupla, 100% celulose virgem, pacote com 2400 folhas', 'PCT', 'Elite Professional', 22.50, 4000.0000),
  ('c3901234-5678-9012-3456-789012345cde', '4a8f9d0c-12fa-34bc-56de-789f01ab2344', 'ec90f1a2-23ab-45cd-67ef-890123456789', '7a8b9c0d-1e2f-3a4b-5c6d-7e8f9a0b1c2d', '03', 'Sabonete Líquido Neutro, glicerinado, hipoalergênico suave, galão com 5 litros', 'GL', 'Premisse Neutro', 38.00, 800.0000),

  -- ATA 045/2026 (Segurança RJ)
  ('d4012345-6789-0123-4567-890123456def', '5b9e0f1d-23ab-45cd-67ef-890123456789', 'fd01a2b3-34bc-56de-789f-012345678901', '9b0c1d2e-3f4a-5b6c-7d8e-9f0a1b2c3d4e', '01', 'Câmera de Monitoramento IP Bullet 4MP, lente varifocal motorizada, infravermelho 50m, proteção IP67', 'UN', 'Intelbras VIP 3430 B', 480.00, 800.0000),
  ('e5123456-7890-1234-5678-901234567ef0', '5b9e0f1d-23ab-45cd-67ef-890123456789', 'fd01a2b3-34bc-56de-789f-012345678901', '9b0c1d2e-3f4a-5b6c-7d8e-9f0a1b2c3d4e', '02', 'Gravador Digital de Vídeo em Rede (NVR) 16 canais PoE, suporte a resolução 4K, compressão H.265+', 'UN', 'Intelbras NVD 3016', 1600.00, 100.0000),
  ('f6234567-8901-2345-6789-012345678f01', '5b9e0f1d-23ab-45cd-67ef-890123456789', 'fd01a2b3-34bc-56de-789f-012345678901', '9b0c1d2e-3f4a-5b6c-7d8e-9f0a1b2c3d4e', '03', 'HD Interno 8TB SATA 3 Surveillance, otimizado para gravação contínua de segurança 24/7', 'UN', 'WD Purple 8TB', 1250.00, 200.0000),

  -- ATA 050/2026 (Campinas - Merenda)
  ('a7345678-9012-3456-7890-123456789f02', '6c0f1a2b-34bc-56de-789f-012345678901', 'ae12b3c4-45cd-67ef-8901-234567890123', 'a5db2291-fe88-4c8d-aa34-11cf9a77cd05', '01', 'Arroz Subgrupo Polido, Classe Longo Fino, Tipo 1, isento de sujidades, fardo de 5kg', 'FD', 'Arroz Tio João', 26.50, 10000.0000),
  ('b8456789-0123-4567-8901-234567890f03', '6c0f1a2b-34bc-56de-789f-012345678901', 'ae12b3c4-45cd-67ef-8901-234567890123', 'a5db2291-fe88-4c8d-aa34-11cf9a77cd05', '02', 'Feijão Comum Carioca, Tipo 1, safra nova, excelente cozimento, pacote de 1kg', 'PCT', 'Feijão Kicaldo', 8.20, 15000.0000),
  ('c9567890-1234-5678-9012-345678901f04', '6c0f1a2b-34bc-56de-789f-012345678901', 'ae12b3c4-45cd-67ef-8901-234567890123', 'a5db2291-fe88-4c8d-aa34-11cf9a77cd05', '03', 'Óleo Refinado de Soja, livre de ranço, garrafa plástica de 900ml', 'UN', 'Óleo Liza', 6.10, 12000.0000),
  ('d0678901-2345-6789-0123-456789012f05', '6c0f1a2b-34bc-56de-789f-012345678901', 'ae12b3c4-45cd-67ef-8901-234567890123', 'a5db2291-fe88-4c8d-aa34-11cf9a77cd05', '04', 'Leite Integral UHT homogeneizado, caixinha de 1 Litro com tampa rosca', 'UN', 'Leite Italac', 4.45, 25000.0000),

  -- ITENS EXTRAS AVULSOS (Lotes de Construção e Saúde)
  ('e1789012-3456-7890-1234-567890123f06', '931b26f5-56f8-4f98-b88a-dfcf1e77df01', '12ab45cd-67ef-8901-2345-67890abcdef1', '6b8b0e77-5054-47c3-88bb-83df3ee08d04', '03', 'Cimento Portland Composto com Pozolana CP II-Z 32, saco de 50 kg', 'SC', 'Cimento Votoran', 36.00, 5000.0000),
  ('f2890123-4567-8901-2345-678901234f07', '931b26f5-56f8-4f98-b88a-dfcf1e77df01', '12ab45cd-67ef-8901-2345-67890abcdef1', '6b8b0e77-5054-47c3-88bb-83df3ee08d04', '04', 'Tijolo Cerâmico de 8 furos, dimensões aproximadas 9x19x19 cm, milheiro', 'MIL', 'Olaria Central', 780.00, 300.0000),
  ('a3901234-5678-9012-3456-789012345f08', '02bf3532-6bf2-4148-8dfa-ef13efcf0f02', 'cf8d9101-de23-4567-8901-23456789abcd', '1f2a3b4c-5d6e-7f8a-9b0c-1d2e3f4a5b6c', '03', 'Desfibrilador Externo Automático (DEA), portátil, com instruções de voz em português', 'UN', 'Zoll AED Plus', 7200.00, 50.0000),
  ('b4012345-6789-0123-4567-890123456f09', '02bf3532-6bf2-4148-8dfa-ef13efcf0f02', 'cf8d9101-de23-4567-8901-23456789abcd', '1f2a3b4c-5d6e-7f8a-9b0c-1d2e3f4a5b6c', '04', 'Eletrocardiógrafo Portátil digital com 12 canais simultâneos, tela colorida touch e impressora térmica', 'UN', 'Hartmann Touch', 9400.00, 30.0000),
  ('c5123456-7890-1234-5678-901234567f10', '02bf3532-6bf2-4148-8dfa-ef13efcf0f02', 'cf8d9101-de23-4567-8901-23456789abcd', '5d6e7f8a-9b0c-1d2e-3f4a-5b6c7d8e9f0a', '05', 'Filtro de Óleo Lubrificante blindado para motores diesel leves de ambulâncias', 'UN', 'Filtros Mann', 48.50, 1200.0000);

-- 7. POPULAR REGRAS DE LIMITE CARONA (6 registros)
INSERT INTO "public".regra_limite_carona (id, ata_id, percentual_maximo_do_saldo, descricao)
VALUES
  ('f145f8ef-8e8e-4a6c-9ad5-c49bcf2e2101', '931b26f5-56f8-4f98-b88a-dfcf1e77df01', 50.00, 'Órgãos não participantes (caronas) podem solicitar no máximo 50% da quantidade total licitada de cada item.'),
  ('02194ad2-fe34-453d-8291-a1284d728ea2', '02bf3532-6bf2-4148-8dfa-ef13efcf0f02', 100.00, 'Permitido caronas aderirem até 100% das quantidades originais, limitado ao teto global por esfera administrativa.'),
  ('132a5be3-0f45-567e-9302-b2395e839fb3', '3f7492c1-d4fe-482a-89a0-fcdcf9839403', 40.00, 'Limite restrito de carona de 40% devido à alta demanda planejada no plano nacional de computadores escolares.'),
  ('243b6cf4-1a56-678f-0413-c34af940acb4', '4a8f9d0c-12fa-34bc-56de-789f01ab2344', 50.00, 'Adesões de carona liberadas até 50% do total da ata, respeitando a capacidade logística de entrega regional.'),
  ('354c7da5-2b67-789a-1524-d45ba051bdc5', '5b9e0f1d-23ab-45cd-67ef-890123456789', 30.00, 'Limite de carona muito restrito de 30% em virtude da flutuação de preço dos componentes de câmeras importadas.'),
  ('465d8ea6-3c78-890a-2635-e56ca162ced6', '6c0f1a2b-34bc-56de-789f-012345678901', 50.00, 'Limite padrão municipal de 50% de adesão de carona para prefeituras vizinhas associadas ao consórcio.');

-- 8. POPULAR PEDIDOS DE COMPRAS (15 registros com status variados)
INSERT INTO "public".pedido (id, orgao_comprador_id, ata_id, data_pedido, tipo_adesao, status, autorizado_por_usuario_id, data_autorizacao, justificativa_rejeicao)
VALUES
  -- Pedido 1: Prefeitura de Campinas usando a Ata do Ministério da Infraestrutura (Carona, Emitido)
  ('74cf5e2e-fa9d-4781-bcfa-12349e5d7f01', '762de6c4-722a-464a-bb91-88849b2f7003', '931b26f5-56f8-4f98-b88a-dfcf1e77df01', '2026-03-01 14:30:00+00', 'CARONA', 'EMITIDO', '3d8b5a76-96b6-45ef-bd98-7cf4a40df601', '2026-03-02 10:00:00+00', NULL),
  
  -- Pedido 2: Sec Saúde SP usando a Ata da Saúde (Direta, Pendente)
  ('12b3c4d5-e6f7-8901-2345-67890abcdef1', '1b1388b8-b80c-4cc0-928e-0bdf60ff7c02', '931b26f5-56f8-4f98-b88a-dfcf1e77df01', '2026-03-10 09:00:00+00', 'DIRETA', 'PENDENTE', NULL, NULL, NULL),
  
  -- Pedido 3: Prefeitura de Campinas extrapolando limite de papel na Ata da Saúde (Rejeitado)
  ('98a7b6c5-d4e3-2109-8765-43210abcdef2', '762de6c4-722a-464a-bb91-88849b2f7003', '02bf3532-6bf2-4148-8dfa-ef13efcf0f02', '2026-04-15 16:45:00+00', 'CARONA', 'REJEITADO', '6ee5367d-d45a-4712-9c4c-2234e402cf02', '2026-04-16 11:15:00+00', 'A quantidade solicitada de papel excede o limite máximo de saldo de carona estabelecido para esta ATA.'),
  
  -- Pedido 4: Prefeitura de Santos na Ata de Infraestrutura (Carona, Autorizado)
  ('bc34de56-78fa-90bc-de12-34567890abcd', '10af8d23-01ef-42d3-9bc4-7cf4a95df606', '931b26f5-56f8-4f98-b88a-dfcf1e77df01', '2026-03-15 11:00:00+00', 'CARONA', 'AUTORIZADO', '3d8b5a76-96b6-45ef-bd98-7cf4a40df601', '2026-03-16 09:30:00+00', NULL),
  
  -- Pedido 5: Unifesp na Ata do MEC (Carona, Emitido)
  ('cd45ef67-89ab-01cd-ef23-456789012345', 'bd78c90e-12fa-34bc-56de-789f01ab2345', '3f7492c1-d4fe-482a-89a0-fcdcf9839403', '2026-03-20 10:15:00+00', 'CARONA', 'EMITIDO', '12ab34cd-56ef-7890-1234-567890abcdef', '2026-03-21 14:00:00+00', NULL),
  
  -- Pedido 6: MEC (Direta, Emitido)
  ('de56f078-90bc-12de-f034-567890123456', '92a18b76-fe88-4432-82ef-dcf9a77fd204', '3f7492c1-d4fe-482a-89a0-fcdcf9839403', '2026-03-22 08:30:00+00', 'DIRETA', 'EMITIDO', '12ab34cd-56ef-7890-1234-567890abcdef', '2026-03-22 10:00:00+00', NULL),
  
  -- Pedido 7: Prefeitura de Campinas na própria Ata de Merenda (Direta, Autorizado)
  ('ef67a189-01cd-23ef-a145-678901234567', '762de6c4-722a-464a-bb91-88849b2f7003', '6c0f1a2b-34bc-56de-789f-012345678901', '2026-03-25 15:00:00+00', 'DIRETA', 'AUTORIZADO', '23bc45de-67f0-8901-2345-67890abcdef1', '2026-03-26 11:30:00+00', NULL),
  
  -- Pedido 8: Prefeitura de Salvador na Ata de Merenda de Campinas (Carona, Pendente)
  ('f078b290-12de-34fa-b256-789012345678', 'df01e23a-45bc-67de-8901-2345bc67de89', '6c0f1a2b-34bc-56de-789f-012345678901', '2026-04-01 13:00:00+00', 'CARONA', 'PENDENTE', NULL, NULL, NULL),
  
  -- Pedido 9: TJSP na própria Ata de Limpeza (Direta, Emitido)
  ('a189c301-23ef-45ab-c367-890123456789', '8bcf8c7d-de45-4781-a9bc-fcdcf98d5c05', '4a8f9d0c-12fa-34bc-56de-789f01ab2344', '2026-04-05 09:00:00+00', 'DIRETA', 'EMITIDO', '34cd56ef-78fa-9012-3456-7890abcdef12', '2026-04-05 10:30:00+00', NULL),
  
  -- Pedido 10: Prefeitura de Santos na Ata de Limpeza do TJSP (Carona, Autorizado)
  ('b290d412-34fa-56ab-d478-901234567890', '10af8d23-01ef-42d3-9bc4-7cf4a95df606', '4a8f9d0c-12fa-34bc-56de-789f01ab2344', '2026-04-10 14:20:00+00', 'CARONA', 'AUTORIZADO', '34cd56ef-78fa-9012-3456-7890abcdef12', '2026-04-11 16:00:00+00', NULL),
  
  -- Pedido 11: Sec Seg RJ na própria Ata de Câmeras (Direta, Emitido)
  ('c301e523-45ab-67cd-e589-012345678901', 'ce90d12f-34ab-56cd-789e-012ab34cd567', '5b9e0f1d-23ab-45cd-67ef-890123456789', '2026-04-12 10:00:00+00', 'DIRETA', 'EMITIDO', '89ab0100-23cd-4567-890a-bcdef1234567', '2026-04-12 11:00:00+00', NULL),
  
  -- Pedido 12: Prefeitura de Salvador na Ata de Câmeras de Seg RJ (Carona, Rejeitado)
  ('d412f634-56ab-78de-f690-123456789012', 'df01e23a-45bc-67de-8901-2345bc67de89', '5b9e0f1d-23ab-45cd-67ef-890123456789', '2026-04-18 15:30:00+00', 'CARONA', 'REJEITADO', '89ab0100-23cd-4567-890a-bcdef1234567', '2026-04-19 09:00:00+00', 'Justificativa técnica inválida ou ausente para aquisição em carona de câmeras tipo IP Bullet nesta quantidade.'),
  
  -- Pedido 13: Sec Saúde SP na Ata de Limpeza do TJSP (Carona, Pendente)
  ('e523a745-67cd-89ab-a701-234567890123', '1b1388b8-b80c-4cc0-928e-0bdf60ff7c02', '4a8f9d0c-12fa-34bc-56de-789f01ab2344', '2026-04-20 11:45:00+00', 'CARONA', 'PENDENTE', NULL, NULL, NULL),
  
  -- Pedido 14: Unifesp na Ata de Merenda de Campinas (Carona, Autorizado)
  ('f634b856-78de-90ab-b812-345678901234', 'bd78c90e-12fa-34bc-56de-789f01ab2345', '6c0f1a2b-34bc-56de-789f-012345678901', '2026-04-22 09:15:00+00', 'CARONA', 'AUTORIZADO', '23bc45de-67f0-8901-2345-67890abcdef1', '2026-04-23 14:30:00+00', NULL),
  
  -- Pedido 15: Ministério da Infraestrutura na Ata de Papelaria da Saúde (Carona, Emitido)
  ('a745c967-89ab-01de-c923-456789012345', 'f7a2ab53-b3c9-467a-9777-709de7483601', '02bf3532-6bf2-4148-8dfa-ef13efcf0f02', '2026-04-25 16:00:00+00', 'CARONA', 'EMITIDO', '6ee5367d-d45a-4712-9c4c-2234e402cf02', '2026-04-26 10:00:00+00', NULL);

-- 9. POPULAR ITENS DE PEDIDOS DE COMPRAS (28 registros vinculando itens às ordens)
INSERT INTO "public".item_pedido (id, pedido_id, item_ata_id, quantidade_solicitada, preco_unitario_no_pedido)
VALUES
  -- Pedido 1 (P1 - Carona Emitido)
  ('47f5ef9e-fb2e-4b67-8af3-fbdf8efcf101', '74cf5e2e-fa9d-4781-bcfa-12349e5d7f01', '6df4ef1e-9df2-47ef-b924-f7b2e3e57f01', 10.0000, 4500.00), -- 10 Notebooks
  ('d18fe7fc-4e6f-4d2b-bfe9-73e4b7cf8c02', '74cf5e2e-fa9d-4781-bcfa-12349e5d7f01', '9ef4a7d3-f093-4a11-884c-bdf19dff3003', 20.0000, 850.00),  -- 20 Cadeiras

  -- Pedido 2 (P2 - Direta Pendente)
  ('ab12cd34-56ef-7890-1234-567890abcdef', '12b3c4d5-e6f7-8901-2345-67890abcdef1', '41ef7de1-2aef-46e3-82ef-df93e7fdf002', 15.0000, 1800.00), -- 15 Monitores (não deduz saldo por estar pendente)

  -- Pedido 3 (P3 - Carona Rejeitado)
  ('cd56ef78-9012-3456-7890-1234567890ab', '98a7b6c5-d4e3-2109-8765-43210abcdef2', 'ef890123-4567-8901-2345-67890abcdef1', 600.0000, 220.00),  -- Tentativa de 600 cx papel

  -- Pedido 4 (P4 - Carona Autorizado)
  ('9a8b7c6d-5e4f-3d2c-1b0a-9876543210ab', 'bc34de56-78fa-90bc-de12-34567890abcd', '6df4ef1e-9df2-47ef-b924-f7b2e3e57f01', 5.0000, 4500.00),  -- 5 Notebooks
  ('8b7c6d5e-4f3d-2c1b-0a98-76543210ab98', 'bc34de56-78fa-90bc-de12-34567890abcd', '5ef678d2-45e3-4b6e-8ffc-df93e7fd0004', 10.0000, 1200.00), -- 10 Mesas L

  -- Pedido 5 (P5 - Carona Emitido MEC)
  ('7c6d5e4f-3d2c-1b0a-9876-543210ab9876', 'cd45ef67-89ab-01cd-ef23-456789012345', 'cd345678-9012-3456-7890-1234567890ab', 200.0000, 1650.00), -- 200 Chromebooks
  ('6d5e4f3d-2c1b-0a98-7654-3210ab987654', 'cd45ef67-89ab-01cd-ef23-456789012345', 'de456789-0123-4567-8901-234567890abc', 400.0000, 1150.00), -- 400 Tablets

  -- Pedido 6 (P6 - Direta Emitido MEC)
  ('5d4e3c2b-1a09-8765-4321-0ab987654321', 'de56f078-90bc-12de-f034-567890123456', 'cd345678-9012-3456-7890-1234567890ab', 500.0000, 1650.00), -- 500 Chromebooks
  ('4d3e2c1b-0a98-7654-3210-ab9876543210', 'de56f078-90bc-12de-f034-567890123456', 'ef567890-1234-5678-9012-34567890abcd', 300.0000, 250.00),  -- 300 Licenças Win

  -- Pedido 7 (P7 - Direta Autorizado Merenda)
  ('3d2e1c0b-a987-6543-210a-b9876543210a', 'ef67a189-01cd-23ef-a145-678901234567', 'a7345678-9012-3456-7890-123456789f02', 1500.0000, 26.50), -- 1500 fardos arroz
  ('2d1e0c9b-8765-4321-0ab9-876543210ab9', 'ef67a189-01cd-23ef-a145-678901234567', 'b8456789-0123-4567-8901-234567890f03', 2000.0000, 8.20),  -- 2000 pct feijão
  ('1d0e9c8b-7654-3210-ab98-76543210ab98', 'ef67a189-01cd-23ef-a145-678901234567', 'c9567890-1234-5678-9012-345678901f04', 1000.0000, 6.10),  -- 1000 óleo

  -- Pedido 8 (P8 - Carona Pendente Merenda)
  ('0d9e8c7b-6543-210a-b987-6543210ab987', 'f078b290-12de-34fa-b256-789012345678', 'd0678901-2345-6789-0123-456789012f05', 500.0000, 4.45),   -- 500 caixas leite

  -- Pedido 9 (P9 - Direta Emitido Limpeza)
  ('ae789012-3456-7890-1234-567890123abc', 'a189c301-23ef-45ab-c367-890123456789', 'a1789012-3456-7890-1234-567890123abc', 100.0000, 45.00),  -- 100 galões álcool
  ('be890123-4567-8901-2345-678901234bcd', 'a189c301-23ef-45ab-c367-890123456789', 'b2890123-4567-8901-2345-678901234bcd', 500.0000, 22.50),  -- 500 pacotes papel toalha

  -- Pedido 10 (P10 - Carona Autorizado Limpeza)
  ('ce901234-5678-9012-3456-789012345cde', 'b290d412-34fa-56ab-d478-901234567890', 'c3901234-5678-9012-3456-789012345cde', 50.0000, 38.00),   -- 50 galões sabonete
  ('de012345-6789-0123-4567-890123456def', 'b290d412-34fa-56ab-d478-901234567890', 'b2890123-4567-8901-2345-678901234bcd', 200.0000, 22.50),  -- 200 pct papel toalha

  -- Pedido 11 (P11 - Direta Emitido Câmeras)
  ('ee123456-7890-1234-5678-901234567ef0', 'c301e523-45ab-67cd-e589-012345678901', 'd4012345-6789-0123-4567-890123456def', 80.0000, 480.00),   -- 80 Câmeras IP
  ('fe234567-8901-2345-6789-012345678f01', 'c301e523-45ab-67cd-e589-012345678901', 'e5123456-7890-1234-5678-901234567ef0', 10.0000, 1600.00),  -- 10 NVRs
  ('ab345678-9012-3456-7890-123456789f01', 'c301e523-45ab-67cd-e589-012345678901', 'f6234567-8901-2345-6789-012345678f01', 20.0000, 1250.00),  -- 20 HDs 8TB

  -- Pedido 12 (P12 - Carona Rejeitado Câmeras)
  ('ae345678-9012-3456-7890-123456789f02', 'd412f634-56ab-78de-f690-123456789012', 'd4012345-6789-0123-4567-890123456def', 300.0000, 480.00),  -- Tentativa de 300 câmeras

  -- Pedido 13 (P13 - Carona Pendente Limpeza)
  ('be456789-0123-4567-8901-234567890f03', 'e523a745-67cd-89ab-a701-234567890123', 'a1789012-3456-7890-1234-567890123abc', 30.0000, 45.00),   -- 30 galões álcool

  -- Pedido 14 (P14 - Carona Autorizado Merenda)
  ('ce567890-1234-5678-9012-345678901f04', 'f634b856-78de-90ab-b812-345678901234', 'd0678901-2345-6789-0123-456789012f05', 2500.0000, 4.45),  -- 2500 caixas leite

  -- Pedido 15 (P15 - Carona Emitido Papelaria da Saúde)
  ('de678901-2345-6789-0123-456789012f05', 'a745c967-89ab-01de-c923-456789012345', 'bc234567-8901-2345-6789-0abcdef12345', 100.0000, 45.00);  -- 100 pct pasta suspensa

COMMIT;
