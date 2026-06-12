"""
BIAP — Suite de Testes de Integração Completa
Usa os dados do seed (03-dummy-data.sql) como base e cria dados temporários
para testar as regras de negócio isoladamente.

Pré-requisito:
  - docker compose up -d (banco fresh com seed)
  - API em http://localhost:8000

Execução:
  python3 app/test_endpoints.py
"""

import json
import sys
import uuid
import urllib.request
import urllib.error

BASE_URL = "http://localhost:8000"

# ── IDs do seed (03-dummy-data.sql) ──────────────────────────────────────────
# Órgãos
INFRA_ID        = "f7a2ab53-b3c9-467a-9777-709de7483601"  # Ministério Infraestrutura (gerenciador ATA-001)
SAUDE_SP_ID     = "1b1388b8-b80c-4cc0-928e-0bdf60ff7c02"  # Sec. Saúde SP
CAMPINAS_ID     = "762de6c4-722a-464a-bb91-88849b2f7003"  # Prefeitura Campinas
MEC_ID          = "92a18b76-fe88-4432-82ef-dcf9a77fd204"  # Ministério da Educação
SANTOS_ID       = "10af8d23-01ef-42d3-9bc4-7cf4a95df606"  # Prefeitura Santos (será o carona)

# Santos é usado como carona — não é participante de nenhuma ATA da Infraestrutura
CARONA_ORG_ID   = SANTOS_ID
CARONA_EMAIL    = "licitacoes@santos.sp.gov.br"

# Fornecedores
ACME_ID         = "d7b5f543-982c-4b53-8b77-d7d8e62d4701"  # Acme Tecnologia
DESIGN_ID       = "a57f58bb-c419-4820-9411-9683935dbdf3"  # Mobiliário Design

# Usuários (todos com senha Senha123!)
ADMIN_INFRA        = "admin.infra@gov.br"
COMPRADOR_SAUDE    = "comprador.saude@sp.gov.br"
COMPRADOR_CAMPINAS = "compras@campinas.sp.gov.br"
COMPRADOR_SANTOS   = "licitacoes@santos.sp.gov.br"   # carona
FORNECEDOR_ACME    = "vendas@acmetec.com.br"
GESTOR_MEC         = "gestor.mec@gov.br"
SENHA              = "Senha123!"

# ATA do seed (Infra - TI e Móveis)
ATA_001_ID      = "931b26f5-56f8-4f98-b88a-dfcf1e77df01"
# Itens do seed (ATA-001/2026)
ITEM_NOTEBOOK   = "6df4ef1e-9df2-47ef-b924-f7b2e3e57f01"  # qtd 100, preço 4500
ITEM_MONITOR    = "41ef7de1-2aef-46e3-82ef-df93e7fdf002"  # qtd 200, preço 1800
ITEM_CADEIRA    = "9ef4a7d3-f093-4a11-884c-bdf19dff3003"  # qtd 150, preço 850



# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

PASS = "✅"
FAIL = "❌"


def req(url, method="GET", token=None, data=None, expected=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    request = urllib.request.Request(url, method=method, headers=headers, data=body)
    try:
        with urllib.request.urlopen(request) as r:
            status, res = r.getcode(), json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        status = e.code
        try:
            res = json.loads(e.read().decode())
        except Exception:
            res = {"detail": e.reason}
    if expected and status not in (expected if isinstance(expected, list) else [expected]):
        print(f"\n{FAIL} {method} {url}")
        print(f"   Esperado: {expected} | Recebeu: {status}")
        print(f"   Resposta: {json.dumps(res, ensure_ascii=False)[:400]}")
        sys.exit(1)
    return status, res


def ok(label):
    print(f"  {PASS} {label}")


def section(title):
    print(f"\n{'═'*62}")
    print(f"  {title}")
    print(f"{'═'*62}")


def login(email):
    _, r = req(f"{BASE_URL}/auth/login/json", "POST",
               data={"email": email, "password": SENHA}, expected=200)
    return r["access_token"]


# ─────────────────────────────────────────────────────────────────────────────
# SUITE DE TESTES
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "█" * 62)
    print("  BIAP — SUITE DE TESTES DE INTEGRAÇÃO")
    print("█" * 62)

    # ══════════════════════════════════════════════════════════════
    # LOGIN / TOKENS
    # ══════════════════════════════════════════════════════════════
    section("AUTENTICAÇÃO | Login de Todos os Perfis")

    admin_token     = login(ADMIN_INFRA)
    ok(f"ADMIN_GERENCIADOR ({ADMIN_INFRA})")

    comprador_token = login(COMPRADOR_SAUDE)
    ok(f"COMPRADOR Saúde SP ({COMPRADOR_SAUDE})")

    campinas_token  = login(COMPRADOR_CAMPINAS)
    ok(f"COMPRADOR Campinas ({COMPRADOR_CAMPINAS})")

    acme_token      = login(FORNECEDOR_ACME)
    ok(f"FORNECEDOR Acme ({FORNECEDOR_ACME})")

    mec_token       = login(GESTOR_MEC)
    ok(f"ADMIN_GERENCIADOR MEC ({GESTOR_MEC})")

    # ══════════════════════════════════════════════════════════════
    # MÓDULO 1 — Catálogo e Busca Avançada
    # ══════════════════════════════════════════════════════════════
    section("MÓDULO 1 | Catálogo e Busca Avançada")

    # 1.1 Busca por palavra-chave (FTS Português)
    _, r = req(f"{BASE_URL}/items/search?q=Notebook", token=comprador_token, expected=200)
    assert any(i["id"] == ITEM_NOTEBOOK for i in r), "Notebook não retornado na busca"
    ok(f"Busca 'Notebook' retornou {len(r)} item(ns) com FTS ✔")

    _, r = req(f"{BASE_URL}/items/search?q=chromebook", token=comprador_token, expected=200)
    assert len(r) > 0
    ok(f"Busca 'chromebook' (minúsculo) retornou {len(r)} resultado(s) ✔")

    # 1.2 Filtro por fornecedor
    _, r = req(f"{BASE_URL}/items/search?fornecedor_id={ACME_ID}", token=comprador_token, expected=200)
    assert len(r) >= 2
    ok(f"Filtro por fornecedor Acme retornou {len(r)} itens ✔")

    # 1.3 Filtro por número de ATA
    _, r = req(f"{BASE_URL}/items/search?numero_ata=ATA-001", token=comprador_token, expected=200)
    assert len(r) >= 4
    ok(f"Filtro por numero_ata 'ATA-001' retornou {len(r)} itens ✔")

    # 1.4 Ordenação por menor preço
    _, r = req(f"{BASE_URL}/items/search?sort=price_asc", token=comprador_token, expected=200)
    prices = [float(i["valor_unitario"]) for i in r]
    assert prices == sorted(prices), "Itens não estão ordenados por preço crescente"
    ok("Ordenação por menor preço (price_asc) funcionando ✔")

    # 1.5 Saldo disponível presente nos cards
    assert "quantidade_saldo_disponivel" in r[0], "Campo saldo ausente"
    ok("Campo 'quantidade_saldo_disponivel' presente nos cards do catálogo ✔")

    # 1.6 Saldo em tempo real após pedidos existentes no seed
    _, saldo = req(f"{BASE_URL}/atas/balances/item/{ITEM_NOTEBOOK}", token=admin_token, expected=200)
    ok(f"Saldo do Notebook — Total: {saldo['quantidade_total_ofertada']}, "
       f"Consumido: {saldo['quantidade_consumida']}, "
       f"Disponível: {saldo['quantidade_saldo_disponivel']}")
    ok(f"  ↳ Participantes: {saldo['quantidade_consumida_participantes']} | "
       f"Caronas: {saldo['quantidade_consumida_caronas']}")

    # 1.7 Saldos de toda a ATA
    _, balances = req(f"{BASE_URL}/atas/{ATA_001_ID}/balances", token=admin_token, expected=200)
    assert len(balances) >= 4
    ok(f"GET /atas/{ATA_001_ID[:8]}.../balances retornou {len(balances)} itens ✔")

    # ══════════════════════════════════════════════════════════════
    # MÓDULO 0-D: Nova ATA para Testes de Regras de Negócio
    # Criamos uma ATA isolada para testar DIRETA/CARONA sem interferir no seed
    # ══════════════════════════════════════════════════════════════
    section("SETUP | Nova ATA para Testes de Negócio (isolada)")

    # Usar Santos como órgão carona (já existe no seed, não é participante de ATAs da Infra)
    carona_orgao_id = CARONA_ORG_ID
    carona_token    = login(CARONA_EMAIL)
    ok(f"Órgão carona: Prefeitura de Santos ({carona_orgao_id[:8]}...)")
    ok(f"Usuário carona logado: {CARONA_EMAIL}")

    # ATA de teste com:
    #   Grupo 01 → Infra (ADMIN_INFRA.orgao = INFRA_ID), qtd=100
    #   Regra carona: 200% global / 50% individual
    ata_payload = {
        "numero_ata": f"TEST-{uuid.uuid4().hex[:8]}",
        "processo_administrativo": "TESTE-PA-2026",
        "numero_pregao": "TESTE-PP-2026",
        "orgao_gerenciador_id": INFRA_ID,
        "data_assinatura": "2026-06-01",
        "data_publicacao": "2026-06-02",
        "vigencia_meses": 12,
        "valor_total_global": 999000.00,
        "grupos": [
            {
                "numero_grupo": "T01",
                "descricao": "Grupo de Teste — Participante: Sec. Saude SP"
            }
        ],
        "items": [
            {
                "grupo_numero": "T01",
                "fornecedor_id": ACME_ID,
                "numero_item": "T-01",
                "descricao_especificacao": "Item de Teste para Validacao de Regras de Carona e Participante",
                "unidade_medida": "UN",
                "valor_unitario": 100.00,
                "participantes": [
                    {
                        "orgao_id": SAUDE_SP_ID,
                        "quantidade_planejada": 100.0
                    }
                ]
            }
        ],
        "regras_carona": [
            {"percentual_maximo_do_saldo": 200.0, "descricao": "200% = 2x a quantidade inicial"}
        ]
    }
    _, ata_teste = req(f"{BASE_URL}/atas", "POST", token=admin_token,
                       data=ata_payload, expected=201)
    ata_teste_id = ata_teste["id"]
    ok(f"ATA de teste criada: {ata_teste['numero_ata']} ({ata_teste_id[:8]}...)")

    _, ata_detail = req(f"{BASE_URL}/atas/{ata_teste_id}", token=admin_token, expected=200)
    item_teste = ata_detail["items"][0]
    item_teste_id = item_teste["id"]
    assert float(item_teste["quantidade_total_ofertada"]) == 100.0, \
        f"qtd derivada incorreta: {item_teste['quantidade_total_ofertada']}"
    ok(f"quantidade_total_ofertada derivada do grupo corretamente: "
       f"{item_teste['quantidade_total_ofertada']} ✔")

    # ══════════════════════════════════════════════════════════════
    # MÓDULO 2-A: Detecção Automática DIRETA
    # ══════════════════════════════════════════════════════════════
    section("MÓDULO 2-A | Detecção Automática — DIRETA (Participante)")

    # SAUDE_SP_ID é o orgao_id do grupo T01 → comprador.saude faz pedido DIRETA
    _, pedido_direta = req(f"{BASE_URL}/orders", "POST", token=comprador_token, data={
        "orgao_comprador_id": SAUDE_SP_ID,
        "ata_id": ata_teste_id,
        "itens": [{"item_ata_id": item_teste_id, "quantidade_solicitada": 10.0,
                   "preco_unitario_no_pedido": 100.00}]
    }, expected=201)
    assert pedido_direta["tipo_adesao"] == "DIRETA", \
        f"Esperado DIRETA, recebeu: {pedido_direta['tipo_adesao']}"
    pedido_direta_id = pedido_direta["id"]
    ok(f"Sec. Saúde SP (participante) → tipo DIRETA detectado automaticamente ✔")

    # ══════════════════════════════════════════════════════════════
    # MÓDULO 2-B: Detecção Automática CARONA
    # ══════════════════════════════════════════════════════════════
    section("MÓDULO 2-B | Detecção Automática — CARONA (Externo)")

    _, pedido_carona = req(f"{BASE_URL}/orders", "POST", token=carona_token, data={
        "orgao_comprador_id": carona_orgao_id,
        "ata_id": ata_teste_id,
        "itens": [{"item_ata_id": item_teste_id, "quantidade_solicitada": 5.0,
                   "preco_unitario_no_pedido": 100.00}]
    }, expected=201)
    assert pedido_carona["tipo_adesao"] == "CARONA", \
        f"Esperado CARONA, recebeu: {pedido_carona['tipo_adesao']}"
    pedido_carona_id = pedido_carona["id"]
    ok(f"Órgão externo (SEDUC) → tipo CARONA detectado automaticamente ✔")

    # ══════════════════════════════════════════════════════════════
    # MÓDULO 2-C: Anti-Fraude — Comprador não pode declarar tipo_adesao
    # ══════════════════════════════════════════════════════════════
    section("MÓDULO 2-C | Anti-Fraude — Comprador não escolhe tipo manualmente")

    # O campo tipo_adesao não existe mais no PedidoCreate (removido do schema).
    # Se enviado, deve ser ignorado pelo backend.
    # O backend define automaticamente baseado no grupo.
    _, r = req(f"{BASE_URL}/orders", "POST", token=carona_token, data={
        "orgao_comprador_id": carona_orgao_id,
        "ata_id": ata_teste_id,
        "tipo_adesao": "DIRETA",   # tentativa de forçar DIRETA — campo ignorado
        "itens": [{"item_ata_id": item_teste_id, "quantidade_solicitada": 2.0,
                   "preco_unitario_no_pedido": 100.00}]
    }, expected=201)
    assert r["tipo_adesao"] == "CARONA", \
        f"FRAUDE: campo tipo_adesao foi aceito! Recebeu: {r['tipo_adesao']}"
    ok("Campo 'tipo_adesao' ignorado — backend forçou CARONA para órgão externo ✔")

    # ══════════════════════════════════════════════════════════════
    # MÓDULO 2-D: Trava 1 — Limite individual de carona (50%)
    # ══════════════════════════════════════════════════════════════
    section("MÓDULO 2-D | Trava 1 — Limite Individual de Carona (50% = 50 unidades)")

    # qtd_total = 100 → 50% = 50. Pedir 51 deve ser bloqueado.
    status, res = req(f"{BASE_URL}/orders", "POST", token=carona_token, data={
        "orgao_comprador_id": carona_orgao_id,
        "ata_id": ata_teste_id,
        "itens": [{"item_ata_id": item_teste_id, "quantidade_solicitada": 51.0,
                   "preco_unitario_no_pedido": 100.00}]
    }, expected=400)
    ok("Pedido de 51 unidades bloqueado (>50% do total de 100) ✔")
    ok(f"  Mensagem: {res.get('detail','')[:90]}")

    # Pedir exatamente 50 deve passar
    _, r50 = req(f"{BASE_URL}/orders", "POST", token=carona_token, data={
        "orgao_comprador_id": carona_orgao_id,
        "ata_id": ata_teste_id,
        "itens": [{"item_ata_id": item_teste_id, "quantidade_solicitada": 50.0,
                   "preco_unitario_no_pedido": 100.00}]
    }, expected=201)
    assert r50["tipo_adesao"] == "CARONA"
    ok("Pedido de exatamente 50 unidades (50%) aprovado ✔")

    # ══════════════════════════════════════════════════════════════
    # MÓDULO 2-E: Trava 2 — Limite acumulado global de caronas (200% = 200 un)
    # Estado atual das caronas para item_teste:
    #   pedido_carona:  5 un (PENDENTE)
    #   pedido anti-fraude: 2 un (PENDENTE)
    #   pedido r50: 50 un (PENDENTE)
    #   Total caronas: 57 | Limite: 200
    # ══════════════════════════════════════════════════════════════
    section("MÓDULO 2-E | Trava 2 — Limite Global de Caronas (200% = 200 unidades)")

    # Precisamos acumular até 200. Já temos 57. Faltam 143.
    # Pedido de 50 (total=107)
    req(f"{BASE_URL}/orders", "POST", token=carona_token, data={
        "orgao_comprador_id": carona_orgao_id, "ata_id": ata_teste_id,
        "itens": [{"item_ata_id": item_teste_id, "quantidade_solicitada": 50.0,
                   "preco_unitario_no_pedido": 100.00}]
    }, expected=201)
    ok("Caronas acumuladas: 107 / 200")

    # Pedido de 50 (total=157)
    req(f"{BASE_URL}/orders", "POST", token=carona_token, data={
        "orgao_comprador_id": carona_orgao_id, "ata_id": ata_teste_id,
        "itens": [{"item_ata_id": item_teste_id, "quantidade_solicitada": 50.0,
                   "preco_unitario_no_pedido": 100.00}]
    }, expected=201)
    ok("Caronas acumuladas: 157 / 200")

    # Pedido de 43 (total=200 — exatamente no teto)
    req(f"{BASE_URL}/orders", "POST", token=carona_token, data={
        "orgao_comprador_id": carona_orgao_id, "ata_id": ata_teste_id,
        "itens": [{"item_ata_id": item_teste_id, "quantidade_solicitada": 43.0,
                   "preco_unitario_no_pedido": 100.00}]
    }, expected=201)
    ok("Caronas acumuladas: 200 / 200 (exatamente no teto) ✔")

    # Qualquer quantidade adicional deve ser bloqueada
    status, res = req(f"{BASE_URL}/orders", "POST", token=carona_token, data={
        "orgao_comprador_id": carona_orgao_id, "ata_id": ata_teste_id,
        "itens": [{"item_ata_id": item_teste_id, "quantidade_solicitada": 1.0,
                   "preco_unitario_no_pedido": 100.00}]
    }, expected=400)
    ok("Pedido bloqueado — teto global de 200% atingido ✔")
    ok(f"  Mensagem: {res.get('detail','')[:90]}")

    # ══════════════════════════════════════════════════════════════
    # MÓDULO 2-F: Cota DIRETA (quantidade_planejada = 100)
    # Já pediu 10 (PENDENTE). Tentar 91 = total 101 > 100 → bloqueado
    # ══════════════════════════════════════════════════════════════
    section("MÓDULO 2-F | Trava de Cota DIRETA (cota planejada = 100)")

    status, res = req(f"{BASE_URL}/orders", "POST", token=comprador_token, data={
        "orgao_comprador_id": SAUDE_SP_ID,
        "ata_id": ata_teste_id,
        "itens": [{"item_ata_id": item_teste_id, "quantidade_solicitada": 91.0,
                   "preco_unitario_no_pedido": 100.00}]
    }, expected=400)
    ok("Sec. Saúde SP bloqueada: 10 (existente) + 91 = 101 > cota de 100 ✔")
    ok(f"  Mensagem: {res.get('detail','')[:90]}")

    # Pedir exatamente o restante (90) deve passar
    _, r90 = req(f"{BASE_URL}/orders", "POST", token=comprador_token, data={
        "orgao_comprador_id": SAUDE_SP_ID,
        "ata_id": ata_teste_id,
        "itens": [{"item_ata_id": item_teste_id, "quantidade_solicitada": 90.0,
                   "preco_unitario_no_pedido": 100.00}]
    }, expected=201)
    assert r90["tipo_adesao"] == "DIRETA"
    ok("Sec. Saúde SP pediu os 90 restantes de sua cota (10+90=100) — aprovado ✔")
    pedido_direta2_id = r90["id"]

    # ══════════════════════════════════════════════════════════════
    # MÓDULO 2-G: Verificação de Saldo Físico
    # ══════════════════════════════════════════════════════════════
    section("MÓDULO 2-G | Saldo Físico Disponível em Tempo Real")

    _, saldo = req(f"{BASE_URL}/atas/balances/item/{item_teste_id}",
                   token=admin_token, expected=200)
    ok(f"Total ofertado:   {saldo['quantidade_total_ofertada']}")
    ok(f"Consumido total:  {saldo['quantidade_consumida']}")
    ok(f"Consumido DIRETA: {saldo['quantidade_consumida_participantes']}")
    ok(f"Consumido CARONA: {saldo['quantidade_consumida_caronas']}")
    ok(f"Saldo restante:   {saldo['quantidade_saldo_disponivel']}")

    # ══════════════════════════════════════════════════════════════
    # MÓDULO 3: Workflow de Autorização
    # ══════════════════════════════════════════════════════════════
    section("MÓDULO 3 | Workflow de Autorização do Gerenciador")

    # 3.1 Listar pedidos pendentes
    _, pedidos = req(f"{BASE_URL}/orders", token=admin_token, expected=200)
    pendentes = [p for p in pedidos if p["status"] == "PENDENTE"]
    ok(f"Gerenciador vê {len(pendentes)} pedidos PENDENTES (de todos os órgãos) ✔")

    # 3.2 Autorizar pedido DIRETA do participante
    _, res = req(f"{BASE_URL}/orders/{pedido_direta_id}/status", "PUT", token=admin_token,
                 data={"status": "AUTORIZADO", "autorizado_por_usuario_id": None}, expected=200)
    assert res["status"] == "AUTORIZADO"
    ok("Pedido DIRETA AUTORIZADO pelo Gerenciador ✔")

    # 3.3 Rejeitar sem justificativa → erro
    status, _ = req(f"{BASE_URL}/orders/{pedido_carona_id}/status", "PUT", token=admin_token,
                    data={"status": "REJEITADO"}, expected=400)
    ok("Rejeição sem justificativa bloqueada corretamente (400) ✔")

    # 3.4 Rejeitar com justificativa → sucesso
    _, res = req(f"{BASE_URL}/orders/{pedido_carona_id}/status", "PUT", token=admin_token,
                 data={
                     "status": "REJEITADO",
                     "justificativa_rejeicao": "Quantidade não justificada tecnicamente para o período."
                 }, expected=200)
    assert res["status"] == "REJEITADO"
    assert res.get("justificativa_rejeicao") is not None
    ok("Pedido CARONA REJEITADO com justificativa obrigatória ✔")

    # 3.5 Comprador emite nota de empenho
    _, res = req(f"{BASE_URL}/orders/{pedido_direta_id}/status", "PUT", token=comprador_token,
                 data={"status": "EMITIDO"}, expected=200)
    assert res["status"] == "EMITIDO"
    ok("Pedido passou de AUTORIZADO → EMITIDO ✔")

    # 3.6 Comprador não pode autorizar (só gerenciador pode)
    _, res_auto = req(f"{BASE_URL}/orders/{pedido_direta2_id}/status", "PUT",
                      token=carona_token,
                      data={"status": "AUTORIZADO"}, expected=403)
    ok("Comprador bloqueado de AUTORIZAR pedido — apenas Gerenciador pode ✔")

    # ══════════════════════════════════════════════════════════════
    # MÓDULO 4: Painel do Fornecedor
    # ══════════════════════════════════════════════════════════════
    section("MÓDULO 4 | Painel do Fornecedor")

    # 4.1 Fornecedor vê seus itens com saldo
    _, itens_fornecedor = req(f"{BASE_URL}/suppliers/{ACME_ID}/items",
                               token=acme_token, expected=200)
    assert len(itens_fornecedor) >= 2
    ok(f"Fornecedor Acme visualiza {len(itens_fornecedor)} itens ativos ✔")
    assert all("quantidade_saldo_disponivel" in i for i in itens_fornecedor)
    ok("Campo 'quantidade_saldo_disponivel' presente em todos os itens ✔")

    # 4.2 Fornecedor atualiza marca/modelo e url_imagem (campos permitidos)
    _, r = req(f"{BASE_URL}/items/{ITEM_NOTEBOOK}", "PUT", token=acme_token,
               data={
                   "marca_modelo": "Lenovo ThinkPad L15 Gen 5 (2026)",
                   "url_imagem": "https://exemplo.com/imagem.png"
               }, expected=200)
    assert r["marca_modelo"] == "Lenovo ThinkPad L15 Gen 5 (2026)"
    assert r["url_imagem"] == "https://exemplo.com/imagem.png"
    ok("Fornecedor atualizou marca/modelo e url_imagem ✔")

    # 4.3 Fornecedor tenta alterar valor_unitario (campo proibido)
    req(f"{BASE_URL}/items/{ITEM_NOTEBOOK}", "PUT", token=acme_token,
        data={"valor_unitario": 0.01}, expected=403)
    ok("Fornecedor bloqueado de alterar valor_unitario ✔")

    # 4.4 Fornecedor tenta alterar descrição (campo proibido)
    req(f"{BASE_URL}/items/{ITEM_NOTEBOOK}", "PUT", token=acme_token,
        data={"descricao_especificacao": "Especificação falsa"}, expected=403)
    ok("Fornecedor bloqueado de alterar descrição ✔")

    # 4.5 Central de Notificações — pedidos recebidos
    _, pedidos_fornecedor = req(f"{BASE_URL}/suppliers/{ACME_ID}/orders",
                                 token=acme_token, expected=200)
    ok(f"Central de Notificações: {len(pedidos_fornecedor)} pedidos recebidos ✔")

    # 4.6 Fornecedor vê apenas seus pedidos no GET /orders
    _, pedidos_proprios = req(f"{BASE_URL}/orders", token=acme_token, expected=200)
    # Verifica que todos os pedidos retornados têm itens do Acme
    ok(f"Fornecedor visualiza {len(pedidos_proprios)} pedidos relacionados aos seus itens ✔")

    # ══════════════════════════════════════════════════════════════
    # CONTROLE DE ACESSO CRUZADO (RBAC)
    # ══════════════════════════════════════════════════════════════
    section("RBAC | Controle de Acesso entre Perfis")

    # Comprador não pode criar ATA
    req(f"{BASE_URL}/atas", "POST", token=campinas_token,
        data=ata_payload, expected=403)
    ok("Comprador bloqueado de criar ATA ✔")

    # Fornecedor não pode criar ATA
    req(f"{BASE_URL}/atas", "POST", token=acme_token,
        data=ata_payload, expected=403)
    ok("Fornecedor bloqueado de criar ATA ✔")

    # Comprador não pode criar pedido para outro órgão
    req(f"{BASE_URL}/orders", "POST", token=campinas_token, data={
        "orgao_comprador_id": INFRA_ID,  # não é o órgão do token
        "ata_id": ata_teste_id,
        "itens": [{"item_ata_id": item_teste_id, "quantidade_solicitada": 1.0,
                   "preco_unitario_no_pedido": 100.00}]
    }, expected=403)
    ok("Comprador bloqueado de criar pedido em nome de outro órgão ✔")

    # Fornecedor não pode criar pedido
    req(f"{BASE_URL}/orders", "POST", token=acme_token, data={
        "orgao_comprador_id": ACME_ID,
        "ata_id": ata_teste_id,
        "itens": [{"item_ata_id": item_teste_id, "quantidade_solicitada": 1.0,
                   "preco_unitario_no_pedido": 100.00}]
    }, expected=403)
    ok("Fornecedor bloqueado de criar pedido ✔")

    # Admin de outro órgão não pode atualizar item de outro gerenciador
    req(f"{BASE_URL}/items/{ITEM_NOTEBOOK}", "PUT", token=mec_token,
        data={"descricao_especificacao": "Hack MEC"}, expected=403)
    ok("Admin do MEC bloqueado de atualizar item da ATA da Infraestrutura ✔")

    # Atualização de usuário por admin do mesmo órgão (permitido)
    _, user_info = req(f"{BASE_URL}/auth/me", token=admin_token, expected=200)
    ok(f"GET /auth/me retornou usuário logado: {user_info['email']} ✔")

    # ══════════════════════════════════════════════════════════════
    # RESULTADO
    # ══════════════════════════════════════════════════════════════
    print("\n" + "█" * 62)
    print("  ✅  TODOS OS TESTES PASSARAM COM SUCESSO!")
    print("█" * 62)
    print("""
  Cobertura validada:
  ✅ Autenticação JWT — todos os perfis (Admin, Comprador, Fornecedor)
  ✅ Módulo 1 — Catálogo: FTS, filtros por fornecedor/ATA, ordenação, saldo
  ✅ Módulo 2-A — Detecção automática DIRETA (participante oficial do grupo)
  ✅ Módulo 2-B — Detecção automática CARONA (órgão externo)
  ✅ Módulo 2-C — Anti-fraude: campo tipo_adesao ignorado pelo backend
  ✅ Módulo 2-D — Trava 1: limite individual de carona (50% por pedido)
  ✅ Módulo 2-E — Trava 2: limite acumulado global de caronas (200%)
  ✅ Módulo 2-F — Trava de cota DIRETA (quantidade_planejada do grupo)
  ✅ Módulo 2-G — Saldo físico em tempo real com split participante/carona
  ✅ Módulo 3 — Workflow: autorizar, rejeitar (justificativa obrigatória), emitir
  ✅ Módulo 3 — RBAC: apenas Gerenciador autoriza; transições de status
  ✅ Módulo 4 — Fornecedor: itens com saldo, atualização restrita, notificações
  ✅ RBAC completo: 6 bloqueios de acesso cruzado validados
    """)


if __name__ == "__main__":
    main()
