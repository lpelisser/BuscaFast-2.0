import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Product
from app.schemas import AssistantAnswer, AssistantQuestion

router = APIRouter(prefix="/assistant", tags=["Assistente de IA"])

SYSTEM_PROMPT = """Você é o assistente do Busca Fast. Responda APENAS perguntas sobre
o produto informado no contexto abaixo ou sobre como usar a interface do app
(busca, favoritos, feed, avaliações, como seguir um vendedor, etc.).

Se a pergunta fugir desse escopo (assuntos gerais, outros sites, opiniões
pessoais, notícias, etc.), responda educadamente que só pode ajudar com
dúvidas sobre produtos e uso do app. Seja direto e responda em português.

Contexto do produto atual:
{contexto_produto}
"""


def _build_context(product: Product) -> str:
    return (
        f"Nome: {product.title}\n"
        f"Descrição: {product.description or 'não informada'}\n"
        f"Preço: R$ {product.price}\n"
        f"Link para outlet: {product.outlet_link or 'não informado'}\n"
    )


async def _call_groq(system_prompt: str, question: str) -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            json={
                "model": settings.groq_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question},
                ],
                "temperature": 0.3,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def _call_gemini(system_prompt: str, question: str) -> str:
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.gemini_model}:generateContent?key={settings.gemini_api_key}"
    )
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            url,
            json={
                "system_instruction": {"parts": [{"text": system_prompt}]},
                "contents": [{"role": "user", "parts": [{"text": question}]}],
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]


@router.post("/perguntar", response_model=AssistantAnswer)
async def perguntar(payload: AssistantQuestion, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    system_prompt = SYSTEM_PROMPT.format(contexto_produto=_build_context(product))

    if settings.groq_api_key:
        answer = await _call_groq(system_prompt, payload.question)
    elif settings.gemini_api_key:
        answer = await _call_gemini(system_prompt, payload.question)
    else:
        raise HTTPException(
            status_code=500,
            detail="Nenhuma chave de IA configurada (GROQ_API_KEY ou GEMINI_API_KEY)",
        )

    return AssistantAnswer(answer=answer)
