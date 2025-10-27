from sqlalchemy import BigInteger, String, ForeignKey
from sqlalchemy.orm import DeclarativeDase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker

engine = create_async_engine(url='sqlite+aiosqlite:///db.sqlite3')

async_session = async_sessionmaker(engine)

class Base(AsyncAttrs, DeclarativeDase):
    pass

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: mapped_column(BigInteger)


class Category(Base):
    _tabkename__ = 'categories'

    id: Mapped[int] = mapped_column(primary_key= True)
    name: Mapped[str] = mapped_column(String(25))

class Item(Base):
    _tabkename__ = 'items'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(25))
    description: Mapped[str] = mapped_column(String(120))
    price: Mapped[int] = mapped_column()
    category: Mapped[int] = mapped_column(ForeignKey('categories.id'))


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)