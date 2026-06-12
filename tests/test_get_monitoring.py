import requests

BASE_URL = "http://localhost:8000"
ADMIN_INFRA = "admin.infra@gov.br"
SENHA = "Senha123!"

def test_get_monitoring():
    # 1. Autenticar para obter o token de admin
    r_login = requests.post(
        f"{BASE_URL}/auth/login/json",
        json={"email": ADMIN_INFRA, "password": SENHA}
    )
    assert r_login.status_code == 200, f"Falha no login: {r_login.text}"
    token = r_login.json()["access_token"]
    
    # 2. Requisitar o painel de monitoramento com o token de autorização
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{BASE_URL}/atas/monitoring", headers=headers)
    
    # 3. Validar a resposta
    assert r.status_code == 200, f"Status incorreto: {r.status_code}. Resposta: {r.text}"
    data = r.json()
    assert isinstance(data, list), "O retorno deve ser uma lista de atas"
    print(f"Sucesso! Retornados {len(data)} itens de monitoramento.")
