-- Rode no SQL Editor do Neon ANTES de publicar a nova versão do backend.
-- (O create_all não altera tabelas que já existem.)
ALTER TABLE users    ADD COLUMN IF NOT EXISTS account_type VARCHAR(20) NOT NULL DEFAULT 'comprador';
ALTER TABLE users    ADD COLUMN IF NOT EXISTS store_name   VARCHAR(120);
ALTER TABLE products ADD COLUMN IF NOT EXISTS outlet_clicks INTEGER NOT NULL DEFAULT 0;
