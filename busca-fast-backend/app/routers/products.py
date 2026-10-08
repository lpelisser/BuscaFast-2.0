from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Favorite, Product, ProductImage, User
from app.schemas import ProductCreate, ProductOut

router = APIRouter(prefix="/products", tags=["Produtos"])


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


@router.get("/me/favoritos", response_model=list[ProductOut])
def meus_favoritos(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return [
        f.product
        for f in db.query(Favorite).filter(Favorite.user_id == current_user.id).all()
    ]


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
    """Página do Produto: galeria, preço, vendedor, link outlet, avaliações (via /feed comments)."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return product


@router.post("", response_model=ProductOut, status_code=201)
def criar_produto(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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
