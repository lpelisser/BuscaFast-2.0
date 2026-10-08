from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Category, User, UserPreference
from app.schemas import CategoryOut, PreferencesUpdate, UserOut

router = APIRouter(prefix="/users", tags=["Usuário e Preferências"])


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    """Tags clicáveis exibidas na Interface Inicial (ex: Tecnologia, Moda, Casa)."""
    return db.query(Category).all()


@router.post("/me/preferences")
def set_preferences(
    payload: PreferencesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pref = (
        db.query(UserPreference)
        .filter(UserPreference.user_id == current_user.id)
        .first()
    )
    if not pref:
        pref = UserPreference(user_id=current_user.id)
        db.add(pref)

    categories = db.query(Category).filter(Category.id.in_(payload.category_ids)).all()
    pref.categories = categories
    pref.onboarding_completed = True
    db.commit()
    return {"status": "preferencias_salvas"}


@router.post("/me/preferences/skip")
def skip_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Permite pular o onboarding e ir direto para o feed."""
    pref = (
        db.query(UserPreference)
        .filter(UserPreference.user_id == current_user.id)
        .first()
    )
    if not pref:
        pref = UserPreference(user_id=current_user.id)
        db.add(pref)
    pref.onboarding_completed = True
    db.commit()
    return {"status": "onboarding_pulado"}
