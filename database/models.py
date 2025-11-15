# Импорт необходимых компонентов SQLAlchemy для работы с базой данных
from sqlalchemy import BigInteger, String, Text, Integer, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from datetime import datetime
from sqlalchemy import LargeBinary

# Создание асинхронного движка для подключения к SQLite базе данных
engine = create_async_engine("sqlite+aiosqlite:///database.db")

# Создание фабрики асинхронных сессий для работы с базой данных
async_session = async_sessionmaker(engine, expire_on_commit=False)

# Базовый класс для всех моделей (таблиц) в базе данных
class Base(AsyncAttrs, DeclarativeBase):
    pass

# Модель пользователя Telegram
class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    username: Mapped[str | None] = mapped_column(String(100))
    full_name: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    
    # Отношения
    physical_entities: Mapped[list["PhysicalEntity"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    organizations: Mapped[list["Organization"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    animals: Mapped[list["Animal"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    favorites: Mapped[list["Favorite"]] = relationship(back_populates="user", cascade="all, delete-orphan")

# Модель физического лица (анкета пользователя как физ. лица)
class PhysicalEntity(Base):
    __tablename__ = "physical_entities"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(100))
    age: Mapped[int] = mapped_column(Integer)
    phone: Mapped[str] = mapped_column(String(20))
    email: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    
    # Отношения
    user: Mapped["User"] = relationship(back_populates="physical_entities")
    animals: Mapped[list["Animal"]] = relationship(back_populates="physical_entity")

# Модель организации (анкета пользователя как организации)
class Organization(Base):
    __tablename__ = "organizations"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(200))
    phone: Mapped[str] = mapped_column(String(20))
    email: Mapped[str] = mapped_column(String(100))
    address: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    
    # Отношения
    user: Mapped["User"] = relationship(back_populates="organizations")
    animals: Mapped[list["Animal"]] = relationship(back_populates="organization")

# Модель животного (анкета животного) с привязкой к профилю
class Animal(Base):
    __tablename__ = "animals"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    category: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    photo_data: Mapped[bytes] = mapped_column(LargeBinary)
    telegram_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Новые поля для привязки к конкретному профилю
    physical_entity_id: Mapped[int | None] = mapped_column(ForeignKey("physical_entities.id"), nullable=True)
    organization_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    
    # Отношения
    user: Mapped["User"] = relationship(back_populates="animals")
    physical_entity: Mapped["PhysicalEntity | None"] = relationship(back_populates="animals")
    organization: Mapped["Organization | None"] = relationship(back_populates="animals")
    favorites: Mapped[list["Favorite"]] = relationship(back_populates="animal", cascade="all, delete-orphan")

# Модель избранного (лайков)
class Favorite(Base):
    __tablename__ = "favorites"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    animal_id: Mapped[int] = mapped_column(ForeignKey("animals.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    
    # Отношения
    user: Mapped["User"] = relationship(back_populates="favorites")
    animal: Mapped["Animal"] = relationship(back_populates="favorites")

# Асинхронная функция для создания всех таблиц в базе данных
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)