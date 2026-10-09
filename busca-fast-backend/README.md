# Busca Fast 2.0 — Backend (FastAPI + Neon Postgres)

## Rodar localmente
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # preencha DATABASE_URL, SECRET_KEY e a chave de IA
uvicorn app.main:app --reload
```
Documentação interativa: http://localhost:8000/docs

## Deploy
Render (backend) + Neon (banco) + Cloudflare Pages (frontend Lovable).
