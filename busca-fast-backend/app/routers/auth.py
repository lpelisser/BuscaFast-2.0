from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models import User
from app.schemas import Token, UserCreate, UserLogin, UserOut

router = APIRouter(prefix="/auth", tags=["Cadastro e Login"])


@router.post("/cadastro", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def cadastro(payload: UserCreate, db: Session = Depends(get_db)):
    if payload.password != payload.password_confirm:
        raise HTTPException(status_code=400, detail="As senhas não coincidem")

    if not payload.accepted_terms:
        raise HTTPException(status_code=400, detail="É necessário aceitar os Termos de Uso")

    existing = (
        db.query(User)
        .filter(
            or_(
                User.username == payload.username,
                User.email == payload.email,
                User.cpf == payload.cpf,
            )
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Usuário, e-mail ou CPF já cadastrado")

    user = User(
        username=payload.username,
        full_name=payload.full_name,
        email=payload.email,
        cpf=payload.cpf,
        phone=payload.phone,
        hashed_password=hash_password(payload.password),
        accepted_terms=payload.accepted_terms,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = (
        db.query(User)
        .filter(or_(User.username == payload.login, User.email == payload.login))
        .first()
    )
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Usuário/e-mail ou senha incorretos")

    token = create_access_token({"sub": str(user.id)})
    return Token(access_token=token)
