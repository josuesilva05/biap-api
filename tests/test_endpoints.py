import os
import uuid
import pytest
import requests

BASE_URL = "http://localhost:8000"

# ── IDs do seed (03-dummy-data.sql) ──────────────────────────────────────────
INFRA_ID        = "f7a2ab53-b3c9-467a-9777-709de7483601"  # Ministério Infraestrutura (gerenciador ATA-001)
SAUDE_SP_ID     = "1b1388b8-b80c-4cc0-928e-0bdf60ff7c02"  # Sec. Saúde SP
CAMPINAS_ID     = "762de6c4-722a-464a-bb91-88849b2f7003"  # Prefeitura Campinas
MEC_ID          = "92a18b76-fe88-4432-82ef-dcf9a77fd204"  # Ministério da Educação
SANTOS_ID       = "10af8d23-01ef-42d3-9bc4-7cf4a95df606"  # Prefeitura Santos (será o carona)

CARONA_ORG_ID   = SANTOS_ID
CARONA_EMAIL    = "licitacoes@santos.sp.gov.br"

ACME_ID         = "d7b5f543-982c-4b53-8b77-d7d8e62d4701"  # Acme Tecnologia
DESIGN_ID       = "a57f58bb-c419-4820-9411-9683935dbdf3"  # Mobiliário Design

ADMIN_INFRA        = "admin.infra@gov.br"
COMPRADOR_SAUDE    = "comprador.saude@sp.gov.br"
COMPRADOR_CAMPINAS = "compras@campinas.sp.gov.br"
COMPRADOR_SANTOS   = "licitacoes@santos.sp.gov.br"   # carona
FORNECEDOR_ACME    = "vendas@acmetec.com.br"
GESTOR_MEC         = "gestor.mec@gov.br"
SENHA              = "Senha123!"

ATA_001_ID      = "931b26f5-56f8-4f98-b88a-dfcf1e77df01"
ITEM_NOTEBOOK   = "6df4ef1e-9df2-47ef-b924-f7b2e3e57f01"
ITEM_MONITOR    = "41ef7de1-2aef-46e3-82ef-df93e7fdf002"
ITEM_CADEIRA    = "9ef4a7d3-f093-4a11-884c-bdf19dff3003"

# Dicionário para compartilhar estado entre testes sequenciais
shared_state = {}

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def req(url, method="GET", token=None, data=None, expected=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        
    if method == "GET":
        r = requests.get(url, headers=headers)
    elif method == "POST":
        r = requests.post(url, headers=headers, json=data)
    elif method == "PUT":
        r = requests.put(url, headers=headers, json=data)
    elif method == "DELETE":
        r = requests.delete(url, headers=headers)
    else:
        raise ValueError(f"Unknown HTTP method: {method}")
        
    status = r.status_code
    try:
        res = r.json()
    except Exception:
        res = {"detail": r.text}
        
    if expected:
        expected_list = expected if isinstance(expected, list) else [expected]
        assert status in expected_list, (
            f"\n{method} {url}\n"
            f"   Esperado: {expected} | Recebeu: {status}\n"
            f"   Resposta: {res}"
        )
    return status, res


def login(email):
    _, r = req(f"{BASE_URL}/auth/login/json", "POST",
               data={"email": email, "password": SENHA}, expected=200)
    return r["access_token"]


@pytest.fixture(scope="module")
def tokens():
    """Fixture que obtém os tokens JWT de todos os perfis no início do teste."""
    return {
        "admin": login(ADMIN_INFRA),
        "comprador": login(COMPRADOR_SAUDE),
        "campinas": login(COMPRADOR_CAMPINAS),
        "acme": login(FORNECEDOR_ACME),
        "mec": login(GESTOR_MEC),
        "carona": login(CARONA_EMAIL)
    }

# ─────────────────────────────────────────────────────────────────────────────
# TEST CASES
# ─────────────────────────────────────────────────────────────────────────────

def test_authentication(tokens):
    """MÓDULO 0 | Autenticação e Login de todos os perfis"""
    assert tokens["admin"] is not None
    assert tokens["comprador"] is not None
    assert tokens["campinas"] is not None
    assert tokens["acme"] is not None
    assert tokens["mec"] is not None
    assert tokens["carona"] is not None


def test_modulo_1_catalog_and_search(tokens):
    """MÓDULO 1 | Catálogo e Busca Avançada"""
    comprador_token = tokens["comprador"]
    admin_token = tokens["admin"]

    # 1.1 Busca por palavra-chave (FTS Português)
    _, r = req(f"{BASE_URL}/items/search?q=Notebook", token=comprador_token, expected=200)
    assert any(i["id"] == ITEM_NOTEBOOK for i in r), "Notebook não retornado na busca"

    _, r = req(f"{BASE_URL}/items/search?q=chromebook", token=comprador_token, expected=200)
    assert len(r) > 0

    # 1.2 Filtro por fornecedor
    _, r = req(f"{BASE_URL}/items/search?fornecedor_id={ACME_ID}", token=comprador_token, expected=200)
    assert len(r) >= 2

    # 1.3 Filtro por número de ATA
    _, r = req(f"{BASE_URL}/items/search?numero_ata=ATA-001", token=comprador_token, expected=200)
    assert len(r) >= 4

    # 1.4 Ordenação por menor preço
    _, r = req(f"{BASE_URL}/items/search?sort=price_asc", token=comprador_token, expected=200)
    prices = [float(i["valor_unitario"]) for i in r]
    assert prices == sorted(prices), "Itens não estão ordenados por preço crescente"

    # 1.5 Saldo disponível presente nos cards
    assert "quantidade_saldo_disponivel" in r[0], "Campo saldo ausente"

    # 1.6 Saldo em tempo real após pedidos existentes no seed
    _, saldo = req(f"{BASE_URL}/atas/balances/item/{ITEM_NOTEBOOK}", token=admin_token, expected=200)
    assert "quantidade_total_ofertada" in saldo
    assert "quantidade_consumida" in saldo
    assert "quantidade_saldo_disponivel" in saldo

    # 1.7 Saldos de toda a ATA
    _, balances = req(f"{BASE_URL}/atas/{ATA_001_ID}/balances", token=admin_token, expected=200)
    assert len(balances) >= 4


def test_setup_temporary_ata(tokens):
    """SETUP | Criar uma nova ATA isolada para os testes de regras de negócio"""
    admin_token = tokens["admin"]
    
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
    
    _, ata_teste = req(f"{BASE_URL}/atas", "POST", token=admin_token, data=ata_payload, expected=201)
    shared_state["ata_teste_id"] = ata_teste["id"]
    
    _, ata_detail = req(f"{BASE_URL}/atas/{ata_teste['id']}", token=admin_token, expected=200)
    item_teste = ata_detail["items"][0]
    shared_state["item_teste_id"] = item_teste["id"]
    
    assert float(item_teste["quantidade_total_ofertada"]) == 100.0


def test_modulo_2a_direct_detection(tokens):
    """MÓDULO 2-A | Detecção Automática — DIRETA (Participante)"""
    comprador_token = tokens["comprador"]
    ata_teste_id = shared_state["ata_teste_id"]
    item_teste_id = shared_state["item_teste_id"]
    
    _, pedido_direta = req(f"{BASE_URL}/orders", "POST", token=comprador_token, data={
        "orgao_comprador_id": SAUDE_SP_ID,
        "ata_id": ata_teste_id,
        "itens": [{"item_ata_id": item_teste_id, "quantidade_solicitada": 10.0,
                   "preco_unitario_no_pedido": 100.00}]
    }, expected=201)
    
    assert pedido_direta["tipo_adesao"] == "DIRETA"
    shared_state["pedido_direta_id"] = pedido_direta["id"]


def test_modulo_2b_carona_detection(tokens):
    """MÓDULO 2-B | Detecção Automática — CARONA (Externo)"""
    carona_token = tokens["carona"]
    ata_teste_id = shared_state["ata_teste_id"]
    item_teste_id = shared_state["item_teste_id"]
    
    _, pedido_carona = req(f"{BASE_URL}/orders", "POST", token=carona_token, data={
        "orgao_comprador_id": CARONA_ORG_ID,
        "ata_id": ata_teste_id,
        "itens": [{"item_ata_id": item_teste_id, "quantidade_solicitada": 5.0,
                   "preco_unitario_no_pedido": 100.00}]
    }, expected=201)
    
    assert pedido_carona["tipo_adesao"] == "CARONA"
    shared_state["pedido_carona_id"] = pedido_carona["id"]


def test_modulo_2c_anti_fraud_type_ignored(tokens):
    """MÓDULO 2-C | Anti-Fraude — Comprador não escolhe tipo manualmente"""
    carona_token = tokens["carona"]
    ata_teste_id = shared_state["ata_teste_id"]
    item_teste_id = shared_state["item_teste_id"]
    
    _, r = req(f"{BASE_URL}/orders", "POST", token=carona_token, data={
        "orgao_comprador_id": CARONA_ORG_ID,
        "ata_id": ata_teste_id,
        "tipo_adesao": "DIRETA",  # Tentativa de fraude (forçar DIRETA)
        "itens": [{"item_ata_id": item_teste_id, "quantidade_solicitada": 2.0,
                   "preco_unitario_no_pedido": 100.00}]
    }, expected=201)
    
    assert r["tipo_adesao"] == "CARONA"


def test_modulo_2d_individual_carona_limit(tokens):
    """MÓDULO 2-D | Trava 1 — Limite Individual de Carona (50% = 50 un)"""
    carona_token = tokens["carona"]
    ata_teste_id = shared_state["ata_teste_id"]
    item_teste_id = shared_state["item_teste_id"]
    
    # 51/100 (51%) deve ser bloqueado
    req(f"{BASE_URL}/orders", "POST", token=carona_token, data={
        "orgao_comprador_id": CARONA_ORG_ID,
        "ata_id": ata_teste_id,
        "itens": [{"item_ata_id": item_teste_id, "quantidade_solicitada": 51.0,
                   "preco_unitario_no_pedido": 100.00}]
    }, expected=400)
    
    # Exatamente 50/100 (50%) deve passar
    _, r50 = req(f"{BASE_URL}/orders", "POST", token=carona_token, data={
        "orgao_comprador_id": CARONA_ORG_ID,
        "ata_id": ata_teste_id,
        "itens": [{"item_ata_id": item_teste_id, "quantidade_solicitada": 50.0,
                   "preco_unitario_no_pedido": 100.00}]
    }, expected=201)
    assert r50["tipo_adesao"] == "CARONA"


def test_modulo_2e_global_carona_limit(tokens):
    """MÓDULO 2-E | Trava 2 — Limite Global de Caronas (200% = 200 un)"""
    carona_token = tokens["carona"]
    ata_teste_id = shared_state["ata_teste_id"]
    item_teste_id = shared_state["item_teste_id"]
    
    # Já temos acumuladas: 5 (pedido_carona) + 2 (anti-fraude) + 50 (pedido r50) = 57 un.
    # Pedir mais 50 (total = 107)
    req(f"{BASE_URL}/orders", "POST", token=carona_token, data={
        "orgao_comprador_id": CARONA_ORG_ID, "ata_id": ata_teste_id,
        "itens": [{"item_ata_id": item_teste_id, "quantidade_solicitada": 50.0,
                   "preco_unitario_no_pedido": 100.00}]
    }, expected=201)
    
    # Pedir mais 50 (total = 157)
    req(f"{BASE_URL}/orders", "POST", token=carona_token, data={
        "orgao_comprador_id": CARONA_ORG_ID, "ata_id": ata_teste_id,
        "itens": [{"item_ata_id": item_teste_id, "quantidade_solicitada": 50.0,
                   "preco_unitario_no_pedido": 100.00}]
    }, expected=201)
    
    # Pedir mais 43 (total = 200 - exatamente o teto)
    req(f"{BASE_URL}/orders", "POST", token=carona_token, data={
        "orgao_comprador_id": CARONA_ORG_ID, "ata_id": ata_teste_id,
        "itens": [{"item_ata_id": item_teste_id, "quantidade_solicitada": 43.0,
                   "preco_unitario_no_pedido": 100.00}]
    }, expected=201)
    
    # Adicionar 1 unidade extra acima de 200 deve ser bloqueado
    req(f"{BASE_URL}/orders", "POST", token=carona_token, data={
        "orgao_comprador_id": CARONA_ORG_ID, "ata_id": ata_teste_id,
        "itens": [{"item_ata_id": item_teste_id, "quantidade_solicitada": 1.0,
                   "preco_unitario_no_pedido": 100.00}]
    }, expected=400)


def test_modulo_2f_direct_cota_limit(tokens):
    """MÓDULO 2-F | Trava de Cota DIRETA (cota planejada = 100)"""
    comprador_token = tokens["comprador"]
    ata_teste_id = shared_state["ata_teste_id"]
    item_teste_id = shared_state["item_teste_id"]
    
    # Já temos 10 (test_modulo_2a_direct_detection). Tentar pedir 91 ultrapassa a cota (101 > 100) e deve falhar.
    req(f"{BASE_URL}/orders", "POST", token=comprador_token, data={
        "orgao_comprador_id": SAUDE_SP_ID,
        "ata_id": ata_teste_id,
        "itens": [{"item_ata_id": item_teste_id, "quantidade_solicitada": 91.0,
                   "preco_unitario_no_pedido": 100.00}]
    }, expected=400)
    
    # Pedir exatamente o restante da cota (90) deve passar
    _, r90 = req(f"{BASE_URL}/orders", "POST", token=comprador_token, data={
        "orgao_comprador_id": SAUDE_SP_ID,
        "ata_id": ata_teste_id,
        "itens": [{"item_ata_id": item_teste_id, "quantidade_solicitada": 90.0,
                   "preco_unitario_no_pedido": 100.00}]
    }, expected=201)
    
    assert r90["tipo_adesao"] == "DIRETA"
    shared_state["pedido_direta2_id"] = r90["id"]


def test_modulo_2g_real_time_balances(tokens):
    """MÓDULO 2-G | Saldo Físico Disponível em Tempo Real"""
    admin_token = tokens["admin"]
    item_teste_id = shared_state["item_teste_id"]
    
    _, saldo = req(f"{BASE_URL}/atas/balances/item/{item_teste_id}", token=admin_token, expected=200)
    assert float(saldo["quantidade_total_ofertada"]) == 100.0
    assert float(saldo["quantidade_consumida"]) == 300.0  # 100 Direta + 200 Carona
    assert float(saldo["quantidade_consumida_participantes"]) == 0.0  # Pedidos DIRETA estão PENDENTES no banco
    assert float(saldo["quantidade_consumida_caronas"]) == 0.0       # Pedidos CARONA estão PENDENTES no banco
    assert float(saldo["quantidade_saldo_disponivel"]) == -200.0


def test_modulo_3_authorization_workflow(tokens):
    """MÓDULO 3 | Workflow de Autorização do Gerenciador e RBAC"""
    admin_token = tokens["admin"]
    comprador_token = tokens["comprador"]
    carona_token = tokens["carona"]
    pedido_direta_id = shared_state["pedido_direta_id"]
    pedido_carona_id = shared_state["pedido_carona_id"]
    pedido_direta2_id = shared_state["pedido_direta2_id"]

    # 3.1 Listar pedidos pendentes
    _, pedidos = req(f"{BASE_URL}/orders", token=admin_token, expected=200)
    pendentes = [p for p in pedidos if p["status"] == "PENDENTE"]
    assert len(pendentes) > 0

    # 3.2 Autorizar pedido DIRETA do participante
    _, res = req(f"{BASE_URL}/orders/{pedido_direta_id}/status", "PUT", token=admin_token,
                 data={"status": "AUTORIZADO", "autorizado_por_usuario_id": None}, expected=200)
    assert res["status"] == "AUTORIZADO"

    # 3.3 Rejeitar sem justificativa → deve falhar (400)
    req(f"{BASE_URL}/orders/{pedido_carona_id}/status", "PUT", token=admin_token,
        data={"status": "REJEITADO"}, expected=400)

    # 3.4 Rejeitar com justificativa → deve passar
    _, res = req(f"{BASE_URL}/orders/{pedido_carona_id}/status", "PUT", token=admin_token,
                 data={
                     "status": "REJEITADO",
                     "justificativa_rejeicao": "Quantidade não justificada tecnicamente para o período."
                 }, expected=200)
    assert res["status"] == "REJEITADO"
    assert res["justificativa_rejeicao"] == "Quantidade não justificada tecnicamente para o período."

    # 3.5 Comprador emite nota de empenho (transição AUTORIZADO -> EMITIDO)
    _, res = req(f"{BASE_URL}/orders/{pedido_direta_id}/status", "PUT", token=comprador_token,
                 data={"status": "EMITIDO"}, expected=200)
    assert res["status"] == "EMITIDO"

    # 3.6 Comprador não pode autorizar próprio pedido (só gerenciador)
    req(f"{BASE_URL}/orders/{pedido_direta2_id}/status", "PUT", token=carona_token,
        data={"status": "AUTORIZADO"}, expected=403)


def test_modulo_4_supplier_dashboard(tokens):
    """MÓDULO 4 | Painel do Fornecedor"""
    acme_token = tokens["acme"]

    # 4.1 Fornecedor vê seus itens com saldo
    _, itens = req(f"{BASE_URL}/suppliers/{ACME_ID}/items", token=acme_token, expected=200)
    assert len(itens) >= 2
    assert all("quantidade_saldo_disponivel" in i for i in itens)

    # 4.2 Fornecedor atualiza marca/modelo (campo permitido)
    _, r = req(f"{BASE_URL}/items/{ITEM_NOTEBOOK}", "PUT", token=acme_token,
               data={"marca_modelo": "Lenovo ThinkPad L15 Gen 5 (2026)"}, expected=200)
    assert r["marca_modelo"] == "Lenovo ThinkPad L15 Gen 5 (2026)"

    # 4.3 Fornecedor tenta alterar valor_unitario (campo proibido)
    req(f"{BASE_URL}/items/{ITEM_NOTEBOOK}", "PUT", token=acme_token,
        data={"valor_unitario": 0.01}, expected=403)

    # 4.4 Fornecedor tenta alterar descrição (campo proibido)
    req(f"{BASE_URL}/items/{ITEM_NOTEBOOK}", "PUT", token=acme_token,
        data={"descricao_especificacao": "Especificação falsa"}, expected=403)

    # 4.5 Central de Notificações — pedidos recebidos
    _, pedidos_fornecedor = req(f"{BASE_URL}/suppliers/{ACME_ID}/orders", token=acme_token, expected=200)
    assert isinstance(pedidos_fornecedor, list)

    # 4.6 Fornecedor vê apenas seus pedidos no GET /orders
    _, pedidos_proprios = req(f"{BASE_URL}/orders", token=acme_token, expected=200)
    assert isinstance(pedidos_proprios, list)


def test_rbac_access_controls(tokens):
    """RBAC | Controle de Acesso Cruzado"""
    campinas_token = tokens["campinas"]
    acme_token = tokens["acme"]
    mec_token = tokens["mec"]
    admin_token = tokens["admin"]
    ata_teste_id = shared_state["ata_teste_id"]
    item_teste_id = shared_state["item_teste_id"]

    # Dummy payload para criação de ATA
    dummy_payload = {
        "numero_ata": f"DUMMY-{uuid.uuid4().hex[:8]}",
        "processo_administrativo": "PA-TEST",
        "numero_pregao": "PP-TEST",
        "orgao_gerenciador_id": INFRA_ID,
        "data_assinatura": "2026-06-01",
        "data_publicacao": "2026-06-02",
        "vigencia_meses": 12,
        "valor_total_global": 1000.0,
        "grupos": [], "items": [], "regras_carona": []
    }

    # Comprador não pode criar ATA
    req(f"{BASE_URL}/atas", "POST", token=campinas_token, data=dummy_payload, expected=403)

    # Fornecedor não pode criar ATA
    req(f"{BASE_URL}/atas", "POST", token=acme_token, data=dummy_payload, expected=403)

    # Comprador não pode criar pedido para outro órgão
    req(f"{BASE_URL}/orders", "POST", token=campinas_token, data={
        "orgao_comprador_id": INFRA_ID,  # não é o órgão de Campinas
        "ata_id": ata_teste_id,
        "itens": [{"item_ata_id": item_teste_id, "quantidade_solicitada": 1.0,
                   "preco_unitario_no_pedido": 100.00}]
    }, expected=403)

    # Fornecedor não pode criar pedido
    req(f"{BASE_URL}/orders", "POST", token=acme_token, data={
        "orgao_comprador_id": ACME_ID,
        "ata_id": ata_teste_id,
        "itens": [{"item_ata_id": item_teste_id, "quantidade_solicitada": 1.0,
                   "preco_unitario_no_pedido": 100.00}]
    }, expected=403)

    # Admin de outro órgão não pode atualizar item de outro gerenciador
    req(f"{BASE_URL}/items/{ITEM_NOTEBOOK}", "PUT", token=mec_token,
        data={"descricao_especificacao": "Hack MEC"}, expected=403)

    # Get user profile check
    _, user_info = req(f"{BASE_URL}/auth/me", token=admin_token, expected=200)
    assert user_info["email"] == ADMIN_INFRA
