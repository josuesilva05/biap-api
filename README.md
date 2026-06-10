# BIAP - Plataforma de Gestão de Atas de Registro de Preços (Marketplace B2G)

A **BIAP** é uma plataforma desenvolvida para transformar o processo tradicional de gestão de **Atas de Registro de Preços** em uma experiência de e-commerce público (**Business to Government - B2G**). O sistema funciona como uma vitrine digital onde órgãos gerenciadores publicam atas, fornecedores expõem suas propostas ganhas no catálogo, e órgãos compradores navegam pelos itens, consultam saldos físicos e solicitam adesões (compras diretas ou caronas).

---

## 💻 Tecnologias do Projeto

* **Backend Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11)
* **Banco de Dados**: [PostgreSQL 18](https://www.postgresql.org/) (Alpine)
* **ORM / Conectores**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/) & `psycopg2-binary`
* **Containerização**: [Docker](https://www.docker.com/) & [Docker Compose](https://docs.docker.com/compose/)
* **Padrão de API**: REST API documentada interativamente via Swagger UI (`/docs`)

---

## 🏛️ Arquitetura do Banco de Dados (`app/models.py`)

A modelagem de dados foi desenhada para garantir consistência e rastreabilidade total de todas as ações de compras públicas:

1. **`fornecedor`**: Empresas detentoras dos itens vencidos em licitação.
2. **`orgao`**: Órgãos públicos cadastrados (com especificação de esfera: `FEDERAL`, `ESTADUAL`, `MUNICIPAL`). Pode atuar tanto como órgão gerenciador da ata quanto órgão comprador (aderente).
3. **`usuario`**: Armazena credenciais e papéis administrativos (`ADMIN_GERENCIADOR`, `COMPRADOR`, `FORNECEDOR`).
4. **`ata`**: Cabeçalho do registro de preço com número da ata, processo administrativo, número do pregão e vigência.
5. **`grupo_lote`**: Agrupamento lógico dos itens de licitação.
6. **`item_ata`**: Itens homologados contendo descrição, marca, preço unitário e quantidade original adjudicada.
7. **`regra_limite_carona`**: Percentuais máximos permitidos para adesões de caronas externas sobre as quantidades de cada item da ATA.
8. **`pedido` & `item_pedido`**: Registram o checkout de compras, tipo de adesão (`DIRETA` ou `CARONA`) e o status do pedido (`PENDENTE`, `AUTORIZADO`, `REJEITADO`, `EMITIDO`).
9. **`vw_saldo_item_ata` (View SQL)**: View dinâmica que calcula em tempo real o saldo disponível descontando os pedidos já aprovados ou emitidos.

---

## 🛠️ Regras de Negócio e Mecanismos do Backend

### 1. Prevenção de Concorrência e Sobrevenda (Race Conditions)
Durante a criação de um pedido (`POST /orders`), múltiplos compradores podem tentar consumir saldo do mesmo item de forma simultânea. Para evitar estouro de saldo, o backend utiliza um **bloqueio pessimista de linhas (`FOR UPDATE`)** na tabela de itens de atas dentro de uma transação isolada, garantindo que o saldo seja recalculado sequencialmente de maneira 100% segura.

### 2. Trava Automática de Carona
Se a modalidade de compra for do tipo `CARONA`, o backend valida dinamicamente se a quantidade solicitada infringe o limite máximo permitido pela regra da respectiva ATA (ex: limite de $50\%$ da quantidade total da ata). Se o limite for excedido, o pedido é revertido (rollback) e uma mensagem detalhada de erro é retornada para o usuário.

### 3. Workflow de Aprovação de Pedidos
Pedidos de compra entram no banco de dados como `PENDENTE`. 
* **Aprovação (`AUTORIZADO`)**: Exige a identificação de um usuário administrador ou comprador elegível.
* **Rejeição (`REJEITADO`)**: Exige obrigatoriamente uma justificativa textual detalhando o motivo do cancelamento do pedido.

---

## 🗺️ Mapa de Rotas e Endpoints da API

Toda a documentação da API e as validações de erros estão totalmente traduzidas e localizadas em **Português**:

### Autenticação (Login & Cadastro)
* **`POST /auth/login`**: Realiza o login do usuário autenticando por formulário padrão OAuth2 (e-mail no campo `username` e senha). Retorna o token JWT e as informações do usuário (ideal para o Swagger UI).
* **`POST /auth/login/json`**: Realiza o login do usuário autenticando via corpo JSON contendo e-mail e senha. Retorna o token JWT e as informações do usuário (ideal para consumo em SPAs).
* **`POST /auth/register`**: Permite a criação de novos usuários no portal. Esta rota é restrita (exige token de usuário `ADMIN_GERENCIADOR`) e só permite criar administradores ou compradores para o seu próprio órgão público (Modelo 1 - Gestão Descentralizada).

### Geral / Início
* **`GET /`**: Retorna uma mensagem de boas-vindas e o status de funcionamento da API.

### Catálogo e Marketplace (Módulo 1)
* **`GET /items/search`**: Busca e filtra itens no catálogo da vitrine B2G por palavra-chave na descrição, preço mínimo/máximo, marca/modelo, fornecedor e ATA. Retorna os itens e seus respectivos saldos físicos disponíveis calculados em tempo real.

### Pedidos e Checkout (Módulo 2 & 3)
* **`POST /orders`**: Cria e efetua um novo pedido de compra (Checkout) aplicando travas de limite de carona e concorrência pessimista.
* **`GET /orders`**: Lista todos os pedidos cadastrados na base por ordem cronológica decrescente.
* **`GET /orders/{order_id}`**: Detalha um pedido específico por ID, exibindo os itens comprados e o órgão comprador.
* **`PUT /orders/{order_id}/status`**: Atualiza o status de aprovação de um pedido específico (Workflow de autorização e justificativa de rejeição).

### Atas de Registro de Preços (Módulo 3)
* **`POST /atas`**: Realiza o cadastro aninhado (carga completa) de uma nova ATA, contendo grupos, itens e regras de carona em uma única transação atômica.
* **`GET /atas`**: Lista todas as Atas cadastradas.
* **`GET /atas/{ata_id}`**: Detalha uma Ata de Registro de Preços específica (incluindo grupos, itens e regras de carona).
* **`GET /atas/{ata_id}/balances`**: Consulta os saldos físicos disponíveis de todos os itens de uma determinada ATA.
* **`GET /atas/balances/item/{item_ata_id}`**: Consulta o saldo físico disponível de um único item específico.

### Fornecedores (Módulo 4)
* **`GET /suppliers`**: Lista todos os fornecedores cadastrados.
* **`POST /suppliers`**: Cadastra um novo fornecedor.
* **`GET /suppliers/{supplier_id}`**: Detalha um fornecedor por ID.
* **`GET /suppliers/{supplier_id}/items`**: Lista todos os itens ganhos por um fornecedor específico, incluindo o saldo físico disponível em tempo real.
* **`GET /suppliers/{supplier_id}/orders`**: Central de Notificações do Fornecedor contendo a lista de pedidos recebidos com seus itens.

### Órgãos Públicos
* **`GET /organs`**: Lista todos os órgãos públicos cadastrados.
* **`POST /organs`**: Cadastra um novo órgão público.
* **`GET /organs/{organ_id}`**: Detalha um órgão público por ID.

---

## 🎨 Estrutura do Frontend (Telas Necessárias)

Para interagir com o backend acima, a aplicação frontend necessita das seguintes telas:

### Telas Gerais
1. **Login**: Autenticação com e-mail e senha, redirecionando o usuário para a área adequada baseado no seu papel.

### Visão do Órgão Comprador (Marketplace)
2. **Vitrine de Itens (Catálogo)**: Lista itens com busca avançada e barra de progresso do consumo de saldos de cada produto.
3. **Carrinho e Checkout**: Configuração das quantidades de compra e escolha da modalidade de adesão (Direta vs. Carona) com validação de limites.
4. **Meus Pedidos**: Lista de pedidos efetuados pelo órgão com o status de andamento e as justificativas de rejeição, se houver.

### Visão do Órgão Gerenciador (Administrativo)
5. **Cadastro e Upload de ATAs**: Importação ou formulário aninhado de novas Atas, regras de caronas e seus itens de licitação.
6. **Dashboard de Autorizações**: Painel contendo solicitações de adesões pendentes dos compradores. Contém opções interativas de aprovar ou rejeitar (exigindo justificativa).
7. **Monitoramento Geral de Atas**: Acompanhamento do consumo global de todos os saldos físicos das Atas criadas.

### Visão do Fornecedor
8. **Central de Saldos do Licitante**: Listagem dos itens vencidos em licitação com o saldo disponível e consumido.
9. **Central de Notificações de Vendas**: Lista de pedidos contendo produtos do fornecedor, para controle de emissão de Notas Fiscais e logística de entrega.

---

## 🚀 Como Executar o Projeto

Certifique-se de possuir o **Docker** e o **Docker Compose** instalados em sua máquina.

1. Configure as variáveis de ambiente no arquivo `.env` localizado na raiz do projeto.
2. Inicie os containers e execute o build do backend:
   ```bash
   docker compose up --build -d
   ```
3. A documentação interativa estará disponível em:
   * **Swagger UI (OpenAPI)**: http://localhost:8000/docs
   * **Redoc**: http://localhost:8000/redoc
   * **Esquema OpenAPI JSON**: http://localhost:8000/openapi.json
