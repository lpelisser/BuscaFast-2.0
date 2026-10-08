import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict


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


class ProductCreate(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    outlet_link: Optional[str] = None
    category_id: int
    image_urls: list[str] = []


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str]
    price: float
    outlet_link: Optional[str]
    seller_id: int
    category_id: int
    images: list[ProductImageOut] = []
    created_at: datetime.datetime


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
    product_id: int
    question: str


class AssistantAnswer(BaseModel):
    answer: str
