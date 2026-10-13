from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Comment, Favorite, Like, Product, ProductImage, User
from app.schemas import OutletClick, ProductCreate, ProductOut, ProductUpdate, SearchOut
from app.search import parecidos_do_produto, pesquisar

router = APIRouter(prefix="/products", tags=["Produtos"])


def _exige_anunciante(user: User) -> None:
    if user.account_type != "anunciante":
        raise HTTPException(
            status_code=403,
            detail="Ative sua conta de anunciante para publicar produtos",
        )


def _produto_do_dono(db: Session, product_id: int, user: User) -> Product:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    if product.seller_id != user.id:
        raise HTTPException(status_code=403, detail="Este produto pertence a outro anunciante")
    return product


@router.get("/feed", response_model=list[ProductOut])
def feed_intuitivo(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """Scroll vertical estilo Instagram/Reels — sem filtro de categoria."""
    return (
        db.query(Product)
        .order_by(Product.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/busca", response_model=list[ProductOut])
def buscar(q: str, skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """Busca por texto no título e na descrição."""
    termo = f"%{q.strip()}%"
    return (
        db.query(Product)
        .filter(or_(Product.title.ilike(termo), Product.description.ilike(termo)))
        .order_by(Product.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/pesquisar", response_model=SearchOut)
def pesquisar_produtos(q: str, limit: int = 20, db: Session = Depends(get_db)):
    """Pesquisa inteligente: `resultados` (batem com o texto) e `parecidos`
    (mesma categoria dos melhores resultados, ordenados por semelhança e preço)."""
    q = q.strip()
    if len(q) < 2:
        raise HTTPException(status_code=422, detail="Digite pelo menos 2 letras para pesquisar")
    limit = max(1, min(limit, 50))
    resultados, parecidos = pesquisar(db, q, limit)
    return SearchOut(query=q, resultados=resultados, parecidos=parecidos)


@router.get("/me/favoritos", response_model=list[ProductOut])
def meus_favoritos(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return [
        f.product
        for f in db.query(Favorite).filter(Favorite.user_id == current_user.id).all()
    ]


@router.get("/meus", response_model=list[ProductOut])
def meus_produtos(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Painel do anunciante: seus produtos, com curtidas, comentários e cliques no link."""
    return (
        db.query(Product)
        .filter(Product.seller_id == current_user.id)
        .order_by(Product.created_at.desc())
        .all()
    )


@router.get("/categoria/{category_id}", response_model=list[ProductOut])
def produtos_por_categoria(
    category_id: int, skip: int = 0, limit: int = 20, db: Session = Depends(get_db)
):
    return (
        db.query(Product)
        .filter(Product.category_id == category_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{product_id}", response_model=ProductOut)
def detalhe_produto(product_id: int, db: Session = Depends(get_db)):
    """Página do Produto: galeria, preço, vendedor, link do site, avaliações."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return product


@router.get("/{product_id}/parecidos", response_model=list[ProductOut])
def produtos_parecidos(product_id: int, limit: int = 10, db: Session = Depends(get_db)):
    """"Você também pode gostar": mesma categoria, com palavras e preço próximos."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return parecidos_do_produto(db, product, max(1, min(limit, 30)))


@router.post("", response_model=ProductOut, status_code=201)
def criar_produto(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _exige_anunciante(current_user)

    product = Product(
        title=payload.title,
        description=payload.description,
        price=payload.price,
        outlet_link=payload.outlet_link,
        category_id=payload.category_id,
        seller_id=current_user.id,
    )
    db.add(product)
    db.flush()

    for i, url in enumerate(payload.image_urls):
        db.add(ProductImage(product_id=product.id, url=url, position=i))

    db.commit()
    db.refresh(product)
    return product


@router.put("/{product_id}", response_model=ProductOut)
def editar_produto(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = _produto_do_dono(db, product_id, current_user)
    dados = payload.model_dump(exclude_unset=True)

    novas_imagens = dados.pop("image_urls", None)
    for campo, valor in dados.items():
        setattr(product, campo, valor)

    if novas_imagens is not None:
        db.query(ProductImage).filter(ProductImage.product_id == product.id).delete()
        for i, url in enumerate(novas_imagens):
            db.add(ProductImage(product_id=product.id, url=url, position=i))

    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=204)
def excluir_produto(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = _produto_do_dono(db, product_id, current_user)
    db.query(Comment).filter(Comment.product_id == product.id).delete()
    db.query(Like).filter(Like.product_id == product.id).delete()
    db.query(Favorite).filter(Favorite.product_id == product.id).delete()
    db.query(ProductImage).filter(ProductImage.product_id == product.id).delete()
    db.delete(product)
    db.commit()
    return Response(status_code=204)


@router.post("/{product_id}/clique", response_model=OutletClick)
def registrar_clique(product_id: int, db: Session = Depends(get_db)):
    """Chame ao tocar em "Ir até o site": conta o clique do anunciante e devolve o link."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product or not product.outlet_link:
        raise HTTPException(status_code=404, detail="Produto sem link disponível")
    product.outlet_clicks = (product.outlet_clicks or 0) + 1
    db.commit()
    return OutletClick(outlet_link=product.outlet_link)


@router.post("/{product_id}/favoritar")
def favoritar_produto(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exists = (
        db.query(Favorite)
        .filter(Favorite.user_id == current_user.id, Favorite.product_id == product_id)
        .first()
    )
    if exists:
        db.delete(exists)
        db.commit()
        return {"status": "removido_dos_favoritos"}

    db.add(Favorite(user_id=current_user.id, product_id=product_id))
    db.commit()
    return {"status": "adicionado_aos_favoritos"}
