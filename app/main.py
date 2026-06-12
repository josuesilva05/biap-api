from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import suppliers, organs, atas, orders, items, auth
from app.config import settings

app = FastAPI(
    title="BIAP - API da Plataforma de Business Intelligence e Contratações",
    description="API para gerenciamento de Atas de Registro de Preços, Órgãos Públicos, Fornecedores e Pedidos de Compra.",
    version="1.0.0",
)

# Configurar CORS para permitir acessos de frontends
origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
if "*" in origins:
    origins = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rotas
app.include_router(auth.router)
app.include_router(suppliers.router)
app.include_router(organs.router)
app.include_router(atas.router)
app.include_router(orders.router)
app.include_router(items.router)

@app.get("/", tags=["Geral"], summary="Obter status da API")
def read_root():
    """
    Retorna uma mensagem de boas-vindas e o status de funcionamento da API.
    """
    return {
        "message": "Bem-vindo à API do portal BIAP!",
        "status": "online",
        "docs_url": "/docs"
    }
