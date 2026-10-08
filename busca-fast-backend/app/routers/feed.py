from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Comment, Follow, Like, Product, User
from app.schemas import CommentCreate, CommentOut

router = APIRouter(prefix="/feed", tags=["Feed Social"])


@router.post("/produtos/{product_id}/comentarios", response_model=CommentOut, status_code=201)
def comentar(
    product_id: int,
    payload: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    comment = Comment(product_id=product_id, user_id=current_user.id, content=payload.content)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@router.get("/produtos/{product_id}/comentarios", response_model=list[CommentOut])
def listar_comentarios(product_id: int, db: Session = Depends(get_db)):
    return db.query(Comment).filter(Comment.product_id == product_id).all()


@router.post("/produtos/{product_id}/curtir")
def curtir(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = (
        db.query(Like)
        .filter(Like.product_id == product_id, Like.user_id == current_user.id)
        .first()
    )
    if existing:
        db.delete(existing)
        db.commit()
        return {"status": "curtida_removida"}

    db.add(Like(product_id=product_id, user_id=current_user.id))
    db.commit()
    return {"status": "curtido"}


@router.post("/vendedores/{seller_id}/seguir")
def seguir_vendedor(
    seller_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if seller_id == current_user.id:
        raise HTTPException(status_code=400, detail="Não é possível seguir a si mesmo")

    existing = (
        db.query(Follow)
        .filter(Follow.follower_id == current_user.id, Follow.seller_id == seller_id)
        .first()
    )
    if existing:
        db.delete(existing)
        db.commit()
        return {"status": "deixou_de_seguir"}

    db.add(Follow(follower_id=current_user.id, seller_id=seller_id))
    db.commit()
    return {"status": "seguindo"}
