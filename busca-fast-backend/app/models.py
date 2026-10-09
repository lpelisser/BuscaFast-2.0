import datetime

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, ForeignKey, DateTime, Numeric, Table
)
from sqlalchemy.orm import relationship

from app.database import Base


# --- Módulo de Cadastro / Login ---

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    cpf = Column(String(14), unique=True, nullable=False)
    phone = Column(String(20), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    accepted_terms = Column(Boolean, default=False, nullable=False)
    is_verified_seller = Column(Boolean, default=False)
    account_type = Column(String(20), nullable=False, default="comprador", server_default="comprador")
    store_name = Column(String(120), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    preferences = relationship("UserPreference", back_populates="user", uselist=False)
    favorites = relationship("Favorite", back_populates="user")
    comments = relationship("Comment", back_populates="user")
    likes = relationship("Like", back_populates="user")
    following = relationship("Follow", foreign_keys="Follow.follower_id", back_populates="follower")


# --- Interface Inicial & Preferências (Onboarding) ---

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(80), unique=True, nullable=False)
    icon = Column(String(50), nullable=True)  # nome do ícone/emoji para a tag clicável


user_preference_categories = Table(
    "user_preference_categories",
    Base.metadata,
    Column("preference_id", ForeignKey("user_preferences.id"), primary_key=True),
    Column("category_id", ForeignKey("categories.id"), primary_key=True),
)


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    onboarding_completed = Column(Boolean, default=False)

    user = relationship("User", back_populates="preferences")
    categories = relationship("Category", secondary=user_preference_categories)


# --- Tela Primária: Produtos ---

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    outlet_link = Column(String(500), nullable=True)
    outlet_clicks = Column(Integer, nullable=False, default=0, server_default="0")
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    seller = relationship("User")
    category = relationship("Category")
    images = relationship("ProductImage", back_populates="product")
    comments = relationship("Comment", back_populates="product")
    likes = relationship("Like", back_populates="product")

    @property
    def seller_name(self) -> str:
        if self.seller is None:
            return ""
        return self.seller.store_name or self.seller.full_name

    @property
    def seller_verified(self) -> bool:
        return bool(self.seller and self.seller.is_verified_seller)

    @property
    def likes_count(self) -> int:
        return len(self.likes)

    @property
    def comments_count(self) -> int:
        return len(self.comments)


class ProductImage(Base):
    __tablename__ = "product_images"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    url = Column(String(500), nullable=False)
    position = Column(Integer, default=0)

    product = relationship("Product", back_populates="images")


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="favorites")
    product = relationship("Product")


# --- Feed Social ---

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    product = relationship("Product", back_populates="comments")
    user = relationship("User", back_populates="comments")


class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    product = relationship("Product", back_populates="likes")
    user = relationship("User", back_populates="likes")


class Follow(Base):
    __tablename__ = "follows"

    id = Column(Integer, primary_key=True, index=True)
    follower_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    follower = relationship("User", foreign_keys=[follower_id], back_populates="following")
    seller = relationship("User", foreign_keys=[seller_id])
