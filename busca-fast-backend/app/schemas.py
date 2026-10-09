import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator


# --- Auth ---

class UserCreate(BaseModel):
    username: str
    full_name: str
    email: EmailStr
    cpf: str
    phone: str
    password: str
    password_confirm: str
    accepted_terms: bool


class UserLogin(BaseModel):
    login: str  # aceita username ou email
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str
    email: EmailStr
    is_verified_seller: bool
    account_type: str = "comprador"
    store_name: Optional[str] = None


class AdvertiserActivate(BaseModel):
    store_name: str = Field(min_length=2, max_length=120)


# --- Preferências / Onboarding ---

class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    icon: Optional[str] = None


class PreferencesUpdate(BaseModel):
    category_ids: list[int]


# --- Produtos ---

class ProductImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    url: str
    position: int


def _valida_link(v: Optional[str]) -> Optional[str]:
    if v is None:
        return v
    v = v.strip()
    if not (v.startswith("http://") or v.startswith("https://")):
        raise ValueError("O link do produto deve começar com http:// ou https://")
    return v


class ProductCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: Optional[str] = None
    price: float = Field(gt=0)
    outlet_link: str  # link do produto no site do anunciante (obrigatório)
    category_id: int
    image_urls: list[str] = Field(default_factory=list, max_length=5)

    @field_validator("outlet_link")
    @classmethod
    def valida_outlet_link(cls, v):
        return _valida_link(v)


class ProductUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=200)
    description: Optional[str] = None
    price: Optional[float] = Field(default=None, gt=0)
    outlet_link: Optional[str] = None
    category_id: Optional[int] = None
    image_urls: Optional[list[str]] = Field(default=None, max_length=5)

    @field_validator("outlet_link")
    @classmethod
    def valida_outlet_link(cls, v):
        return _valida_link(v)


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str]
    price: float
    outlet_link: Optional[str]
    outlet_clicks: int = 0
    seller_id: int
    seller_name: str = ""
    seller_verified: bool = False
    category_id: int
    likes_count: int = 0
    comments_count: int = 0
    images: list[ProductImageOut] = []
    created_at: datetime.datetime


class OutletClick(BaseModel):
    outlet_link: str


# --- Feed Social ---

class CommentCreate(BaseModel):
    content: str


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    content: str
    created_at: datetime.datetime


# --- Assistente de IA ---

class AssistantQuestion(BaseModel):
    product_id: Optional[int] = None  # sem produto = dúvidas gerais sobre o app
    question: str = Field(min_length=1, max_length=500)


class AssistantAnswer(BaseModel):
    answer: str


# --- Upload de fotos (Cloudinary, upload assinado) ---

class UploadSignature(BaseModel):
    upload_url: str
    api_key: str
    timestamp: int
    folder: str
    signature: str
