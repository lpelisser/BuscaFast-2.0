"""Pesquisa de produtos com resultados diretos + produtos parecidos (mesma categoria).

Sem dependências extras: normaliza acentos/plural e pontua por palavras em comum.
Adequado para MVP; para catálogos grandes, migrar para busca full-text do Postgres.
"""
import re
import unicodedata

from sqlalchemy.orm import Session

from app.models import Category, Product

STOPWORDS = {
    "de", "da", "do", "das", "dos", "para", "com", "sem", "por", "uma", "uns",
    "umas", "que", "the", "and", "em", "na", "no", "nas", "nos", "pra",
}
MAX_CANDIDATOS = 1000


def normaliza(texto: str | None) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode()
    return sem_acento.lower()


def tokens(texto: str | None) -> set[str]:
    saida = set()
    for t in re.findall(r"[a-z0-9]+", normaliza(texto)):
        if len(t) < 3 or t in STOPWORDS:
            continue
        if len(t) > 3 and t.endswith("s"):  # plural simples: mouses -> mouse
            t = t[:-1]
        saida.add(t)
    return saida


def _pontua(produto: Product, q_norm: str, q_tokens: set[str]) -> int:
    titulo = tokens(produto.title)
    descricao = tokens(produto.description)
    pontos = 3 * len(q_tokens & titulo) + len(q_tokens & descricao)
    if q_norm and q_norm in normaliza(produto.title):
        pontos += 5
    return pontos


def _distancia_preco(produto: Product, referencia: float | None) -> float:
    if referencia is None:
        return 0.0
    return abs(float(produto.price) - referencia)


def pesquisar(db: Session, q: str, limite: int = 20) -> tuple[list[Product], list[Product]]:
    q_norm = normaliza(q).strip()
    q_tokens = tokens(q)

    candidatos = db.query(Product).order_by(Product.created_at.desc()).limit(MAX_CANDIDATOS).all()

    pontuados = [(p, _pontua(p, q_norm, q_tokens)) for p in candidatos]
    resultados = [p for p, pts in sorted(pontuados, key=lambda x: (-x[1], -x[0].id)) if pts > 0][:limite]

    # categorias de interesse: as dos melhores resultados; se não houver, as que o texto menciona
    categorias = {p.category_id for p in resultados[:3]}
    if not categorias and q_tokens:
        for cat in db.query(Category).all():
            if tokens(cat.name) & q_tokens:
                categorias.add(cat.id)

    preco_ref = None
    if resultados:
        precos = sorted(float(p.price) for p in resultados[:3])
        preco_ref = precos[len(precos) // 2]

    ids_resultados = {p.id for p in resultados}
    parecidos = [p for p in candidatos if p.category_id in categorias and p.id not in ids_resultados]
    parecidos.sort(
        key=lambda p: (
            -len(q_tokens & (tokens(p.title) | tokens(p.description))),
            _distancia_preco(p, preco_ref),
            -p.id,
        )
    )
    return resultados, parecidos[:limite]


def parecidos_do_produto(db: Session, produto: Product, limite: int = 10) -> list[Product]:
    base = tokens(produto.title) | tokens(produto.description)
    candidatos = (
        db.query(Product)
        .filter(Product.category_id == produto.category_id, Product.id != produto.id)
        .order_by(Product.created_at.desc())
        .limit(MAX_CANDIDATOS)
        .all()
    )
    preco = float(produto.price)
    candidatos.sort(
        key=lambda p: (
            -len(base & (tokens(p.title) | tokens(p.description))),
            abs(float(p.price) - preco),
            -p.id,
        )
    )
    return candidatos[:limite]
