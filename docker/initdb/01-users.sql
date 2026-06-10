-- usuário utilizado pela aplicação

CREATE USER arphub_user
WITH PASSWORD 'arp_user123!@#';

-- acesso ao banco

GRANT CONNECT ON DATABASE arphub TO arphub_user;

-- acesso ao schema public

GRANT USAGE ON SCHEMA public TO arphub_user;

-- permissões nas tabelas existentes

GRANT SELECT, INSERT, UPDATE, DELETE
ON ALL TABLES IN SCHEMA public
TO arphub_user;

-- permissões em sequences

GRANT USAGE, SELECT
ON ALL SEQUENCES IN SCHEMA public
TO arphub_user;

-- permissões futuras

ALTER DEFAULT PRIVILEGES
IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE
ON TABLES
TO arphub_user;

ALTER DEFAULT PRIVILEGES
IN SCHEMA public
GRANT USAGE, SELECT
ON SEQUENCES
TO arphub_user;

CREATE EXTENSION IF NOT EXISTS "pgcrypto";
