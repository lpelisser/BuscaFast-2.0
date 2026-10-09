import hashlib
import time

from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_user
from app.config import settings
from app.models import User
from app.schemas import UploadSignature

router = APIRouter(prefix="/uploads", tags=["Upload de fotos"])

FOLDER = "buscafast"


def assinar(params: dict, api_secret: str) -> str:
    """Assinatura do Cloudinary: SHA-1 dos parâmetros em ordem alfabética + API secret."""
    a_assinar = "&".join(f"{k}={params[k]}" for k in sorted(params) if params[k] not in (None, ""))
    return hashlib.sha1((a_assinar + api_secret).encode("utf-8")).hexdigest()


@router.get("/assinatura", response_model=UploadSignature)
def assinatura_upload(current_user: User = Depends(get_current_user)):
    """Gera a assinatura para o navegador enviar a foto direto ao Cloudinary,
    sem expor o API secret e sem precisar de upload preset."""
    if current_user.account_type != "anunciante":
        raise HTTPException(status_code=403, detail="Ative sua conta de anunciante para enviar fotos")

    if not (settings.cloudinary_cloud_name and settings.cloudinary_api_key and settings.cloudinary_api_secret):
        raise HTTPException(status_code=500, detail="Upload de fotos não configurado no servidor")

    timestamp = int(time.time())
    signature = assinar({"folder": FOLDER, "timestamp": timestamp}, settings.cloudinary_api_secret)

    return UploadSignature(
        upload_url=f"https://api.cloudinary.com/v1_1/{settings.cloudinary_cloud_name}/image/upload",
        api_key=settings.cloudinary_api_key,
        timestamp=timestamp,
        folder=FOLDER,
        signature=signature,
    )
