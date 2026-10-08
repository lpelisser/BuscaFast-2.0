from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

from app.database import Base, engine
from app.routers import assistant, auth, feed, products, users

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Busca Fast 2.0 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrinja ao domínio do Cloudflare Pages em produção
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(products.router)
app.include_router(feed.router)
app.include_router(assistant.router)


@app.get("/")
def health_check():
    return {"status": "ok"}
