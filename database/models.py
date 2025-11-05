# Импорт необходимых компонентов SQLAlchemy для работы с базой данных
from sqlalchemy import BigInteger, String, Text, Integer, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from datetime import datetime
from sqlalchemy import LargeBinary  # Для хранения бинарных данных (фото)

# Создание асинхронного движка для подключения к SQLite базе данных
# "sqlite+aiosqlite:///database.db" - строка подключения к файлу database.db
engine = create_async_engine("sqlite+aiosqlite:///database.db")

# Создание фабрики асинхронных сессий для работы с базой данных
# expire_on_commit=False - объекты не теряют состояние после коммита
async_session = async_sessionmaker(engine, expire_on_commit=False)

# Базовый класс для всех моделей (таблиц) в базе данных
# AsyncAttrs - добавляет асинхронные методы для работы с отношениями
# DeclarativeBase - базовый класс для декларативного стиля SQLAlchemy
class Base(AsyncAttrs, DeclarativeBase):
    pass

# Модель пользователя Telegram
class User(Base):
    __tablename__ = "users"  # Название таблицы в базе данных
    
    id: Mapped[int] = mapped_column(primary_key=True)  # Уникальный идентификатор (автоинкремент)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True)  # ID пользователя в Telegram (уникальный)
    username: Mapped[str | None] = mapped_column(String(100))  # Имя пользователя в Telegram (может быть None)
    full_name: Mapped[str] = mapped_column(String(200))  # Полное имя пользователя
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)  # Дата создания с автоматическим заполнением

# Модель физического лица (анкета пользователя как физ. лица)
class PhysicalEntity(Base):
    __tablename__ = "physical_entities"  # Название таблицы
    
    id: Mapped[int] = mapped_column(primary_key=True)  # Уникальный идентификатор
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))  # Внешний ключ к таблице users
    name: Mapped[str] = mapped_column(String(100))  # Имя физического лица
    age: Mapped[int] = mapped_column(Integer)  # Возраст
    phone: Mapped[str] = mapped_column(String(20))  # Номер телефона
    email: Mapped[str] = mapped_column(String(100))  # Электронная почта
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)  # Дата создания

# Модель организации (анкета пользователя как организации)
class Organization(Base):
    __tablename__ = "organizations"  # Название таблицы
    
    id: Mapped[int] = mapped_column(primary_key=True)  # Уникальный идентификатор
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))  # Внешний ключ к таблице users
    name: Mapped[str] = mapped_column(String(200))  # Название организации
    phone: Mapped[str] = mapped_column(String(20))  # Номер телефона организации
    email: Mapped[str] = mapped_column(String(100))  # Электронная почта организации
    address: Mapped[str] = mapped_column(Text)  # Адрес организации (Text для длинного текста)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)  # Дата создания

# Модель животного (анкета животного)
class Animal(Base):
    __tablename__ = "animals"  # Название таблицы
    
    id: Mapped[int] = mapped_column(primary_key=True)  # Уникальный идентификатор
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))  # Внешний ключ к таблице users (владелец животного)
    category: Mapped[str] = mapped_column(String(50))  # Категория животного (собака, кошка, др.)
    name: Mapped[str] = mapped_column(String(100))  # Имя животного
    description: Mapped[str] = mapped_column(Text)  # Описание животного
    photo_data: Mapped[bytes] = mapped_column(LargeBinary)  # Бинарные данные фото животного
    telegram_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)  # File_id фото в Telegram (может быть None)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)  # Дата создания

# Асинхронная функция для создания всех таблиц в базе данных
async def create_tables():
    # Создание контекстного менеджера для работы с соединением
    async with engine.begin() as conn:
        # Синхронный вызов для создания всех таблиц на основе моделей
        # Base.metadata.create_all - создает все таблицы, которые еще не существуют
        await conn.run_sync(Base.metadata.create_all)