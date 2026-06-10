import json
import urllib.request
import urllib.error
import sys

BASE_URL = "http://127.0.0.1:8000"

def make_request(url, method="GET", headers=None, data=None):
    if headers is None:
        headers = {}
    req_headers = {"Content-Type": "application/json"}
    req_headers.update(headers)
    
    req_data = None
    if data is not None:
        req_data = json.dumps(data).encode("utf-8")
        
    req = urllib.request.Request(url, method=method, headers=req_headers, data=req_data)
    try:
        with urllib.request.urlopen(req) as response:
            status_code = response.getcode()
            response_data = json.loads(response.read().decode("utf-8"))
            return status_code, response_data
    except urllib.error.HTTPError as e:
        status_code = e.code
        try:
            response_data = json.loads(e.read().decode("utf-8"))
        except Exception:
            response_data = e.reason
        return status_code, response_data

def get_token(username, password):
    url = f"{BASE_URL}/auth/login/json"
    status, res = make_request(url, "POST", data={"email": username, "password": password})
    if status != 200:
        print(f"Failed to get token for {username}: {res}")
        sys.exit(1)
    return res["access_token"]

def main():
    print("=== STARTING RBAC ENDPOINT TESTS ===")
    
    # Tokens
    print("Logging in users...")
    admin_infra_token = get_token("admin.infra@gov.br", "Senha123!")
    admin_mec_token = get_token("gestor.mec@gov.br", "Senha123!")
    fornecedor_acme_token = get_token("vendas@acmetec.com.br", "Senha123!")
    fornecedor_design_token = get_token("comercial@designmobiliario.com.br", "Senha123!")
    
    headers_admin_infra = {"Authorization": f"Bearer {admin_infra_token}"}
    headers_admin_mec = {"Authorization": f"Bearer {admin_mec_token}"}
    headers_fornecedor_acme = {"Authorization": f"Bearer {fornecedor_acme_token}"}
    headers_fornecedor_design = {"Authorization": f"Bearer {fornecedor_design_token}"}
    
    # ----------------------------------------------------
    # TEST 1: User Registration and Update (auth /users)
    # ----------------------------------------------------
    print("\n--- Test 1: User Update Route (PUT /auth/users/{user_id}) ---")
    
    # 1.1 Register a new buyer (COMPRADOR) in Ministry of Infrastructure as infra admin
    print("1.1 Registering buyer under Ministry of Infrastructure...")
    reg_url = f"{BASE_URL}/auth/register"
    new_user_data = {
        "email": "comprador.infra@gov.br",
        "password": "Senha123!",
        "papel": "COMPRADOR",
        "orgao_id": "f7a2ab53-b3c9-467a-9777-709de7483601"
    }
    
    import uuid
    rand_email = f"comprador.infra.{uuid.uuid4().hex[:6]}@gov.br"
    new_user_data["email"] = rand_email
    
    status, res = make_request(reg_url, "POST", headers=headers_admin_infra, data=new_user_data)
    assert status == 201, f"Failed to register user: {res}"
    new_user_id = res["id"]
    print(f"Registered user with ID: {new_user_id} and email: {rand_email}")
    
    # 1.2 Update user as admin of the same organ (Success)
    print("1.2 Updating user email as admin of same organ...")
    updated_email = f"updated.{rand_email}"
    update_user_url = f"{BASE_URL}/auth/users/{new_user_id}"
    status, res = make_request(update_user_url, "PUT", headers=headers_admin_infra, data={"email": updated_email})
    assert status == 200, f"Expected 200, got {status}: {res}"
    assert res["email"] == updated_email, f"Email was not updated: {res}"
    print("Success: Admin updated user within same organ.")
    
    # 1.3 Try to update user as admin of a different organ (Forbidden)
    print("1.3 Trying to update user as admin of a different organ...")
    status, res = make_request(update_user_url, "PUT", headers=headers_admin_mec, data={"email": "hacked@gov.br"})
    assert status == 403, f"Expected 403, got {status}: {res}"
    print("Success: Forbidden error received as expected.")
    
    # 1.4 Try to update user as a fornecedor (Forbidden)
    print("1.4 Trying to update user as a fornecedor...")
    status, res = make_request(update_user_url, "PUT", headers=headers_fornecedor_acme, data={"email": "hacked2@gov.br"})
    assert status == 403, f"Expected 403, got {status}: {res}"
    print("Success: Forbidden error received as expected.")

    # ----------------------------------------------------
    # TEST 2: Item ATA Update (PUT /items/{item_ata_id})
    # ----------------------------------------------------
    print("\n--- Test 2: Item ATA Update Route (PUT /items/{item_ata_id}) ---")
    
    # Item 6df4ef1e-9df2-47ef-b924-f7b2e3e57f01:
    # - ATA: ATA-001/2026 (Infra gerenciador)
    # - Fornecedor: Acme Tecnologia
    item_id = "6df4ef1e-9df2-47ef-b924-f7b2e3e57f01"
    item_url = f"{BASE_URL}/items/{item_id}"
    
    # 2.1 Admin Gerenciador updates multiple fields (Success)
    print("2.1 Admin Gerenciador updating description and unit price...")
    original_desc = "Notebook Corporativo, Processador Intel Core i7, 16GB RAM, SSD 512GB NVMe, Tela 15.6 FHD, Windows 11 Pro"
    status, res = make_request(
        item_url, "PUT", headers=headers_admin_infra,
        data={
            "descricao_especificacao": "Notebook Premium Corporativo i7 16GB",
            "valor_unitario": 4600.00
        }
    )
    assert status == 200, f"Expected 200, got {status}: {res}"
    assert res["descricao_especificacao"] == "Notebook Premium Corporativo i7 16GB", f"Desc not updated: {res}"
    assert float(res["valor_unitario"]) == 4600.00, f"Price not updated: {res}"
    print("Success: Admin Gerenciador updated all fields.")
    
    # Restoring original values for next runs
    make_request(
        item_url, "PUT", headers=headers_admin_infra,
        data={
            "descricao_especificacao": original_desc,
            "valor_unitario": 4500.00
        }
    )

    # 2.2 Fornecedor owner updates brand/model (Success)
    print("2.2 Fornecedor owner updating marca_modelo...")
    status, res = make_request(
        item_url, "PUT", headers=headers_fornecedor_acme,
        data={"marca_modelo": "Lenovo ThinkPad L15 Gen 4"}
    )
    assert status == 200, f"Expected 200, got {status}: {res}"
    assert res["marca_modelo"] == "Lenovo ThinkPad L15 Gen 4", f"Brand/model not updated: {res}"
    print("Success: Supplier owner updated brand/model.")
    
    # 2.3 Fornecedor owner tries to update description (Forbidden)
    print("2.3 Fornecedor owner trying to update description...")
    status, res = make_request(
        item_url, "PUT", headers=headers_fornecedor_acme,
        data={"descricao_especificacao": "Hacked specification"}
    )
    assert status == 403, f"Expected 403, got {status}: {res}"
    print("Success: Forbidden error received as expected.")

    # 2.4 Fornecedor owner tries to update price (Forbidden)
    print("2.4 Fornecedor owner trying to update price...")
    status, res = make_request(
        item_url, "PUT", headers=headers_fornecedor_acme,
        data={"valor_unitario": 10.00}
    )
    assert status == 403, f"Expected 403, got {status}: {res}"
    print("Success: Forbidden error received as expected.")

    # 2.5 Different Admin trying to update item (Forbidden)
    print("2.5 Different Admin trying to update item...")
    status, res = make_request(
        item_url, "PUT", headers=headers_admin_mec,
        data={"marca_modelo": "MEC Hack"}
    )
    assert status == 403, f"Expected 403, got {status}: {res}"
    print("Success: Forbidden error received as expected.")

    # 2.6 Different Supplier trying to update item (Forbidden)
    print("2.6 Different Supplier trying to update item...")
    status, res = make_request(
        item_url, "PUT", headers=headers_fornecedor_design,
        data={"marca_modelo": "Design Hack"}
    )
    assert status == 403, f"Expected 403, got {status}: {res}"
    print("Success: Forbidden error received as expected.")

    print("\n=== ALL RBAC TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    main()
