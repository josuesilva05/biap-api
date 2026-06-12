import os
import glob
import time
import sys
import psycopg2
from app.config import settings

def main():
    db_user = os.environ.get("POSTGRES_USER")
    db_pass = os.environ.get("POSTGRES_PASSWORD")
    db_name = os.environ.get("POSTGRES_DB")
    
    # Configura conexão usando credenciais de admin se disponíveis
    if db_user and db_pass and db_name:
        connect_kwargs = {
            "host": "postgres",
            "port": 5432,
            "user": db_user,
            "password": db_pass,
            "database": db_name
        }
        print(f"Conectando ao banco de dados como admin ({db_user})...")
    else:
        connect_kwargs = {"dsn": settings.database_url}
        print("Conectando ao banco de dados com a URL padrão...")
        
    # Aguarda o postgres estar pronto para conexões
    conn = None
    for i in range(30):
        try:
            conn = psycopg2.connect(**connect_kwargs)
            break
        except Exception as e:
            print(f"Banco de dados não está pronto... ({e})")
            time.sleep(1)
            
    if conn is None:
        print("Erro: Banco de dados inacessível após 30 segundos.")
        sys.exit(1)
        
    print("Conectado ao banco de dados. Verificando migrations...")
    cur = conn.cursor()
    
    try:
        # Criar tabela de controle de migrations se não existir
        cur.execute("""
            CREATE TABLE IF NOT EXISTS applied_migrations (
                filename VARCHAR(255) PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        
        # Obter lista de migrations já aplicadas
        cur.execute("SELECT filename FROM applied_migrations;")
        applied = {row[0] for row in cur.fetchall()}
        
        # Encontrar arquivos de migration no diretório docker/initdb/
        migrations_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docker", "initdb")
        sql_pattern = os.path.join(migrations_dir, "*migration*.sql")
        migration_files = sorted(glob.glob(sql_pattern))
        
        if not migration_files:
            print(f"Aviso: Nenhuma migration encontrada no diretório {migrations_dir}")
            return
            
        for f in migration_files:
            filename = os.path.basename(f)
            if filename not in applied:
                print(f"Aplicando migration: {filename}")
                with open(f, "r", encoding="utf-8") as file:
                    sql_content = file.read()
                
                # Executa o SQL da migration
                cur.execute(sql_content)
                
                # Garante que a migration seja registrada na tabela (caso não tenha feito isso internamente)
                cur.execute(
                    "INSERT INTO applied_migrations (filename) VALUES (%s) ON CONFLICT DO NOTHING;",
                    (filename,)
                )
                conn.commit()
                print(f"Migration {filename} aplicada com sucesso.")
            else:
                print(f"Migration já aplicada: {filename}")
                
        print("Todas as migrations estão atualizadas!")
    except Exception as e:
        conn.rollback()
        print(f"Erro ao aplicar migrations: {e}")
        sys.exit(1)
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()
