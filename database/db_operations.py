from sqlalchemy import select
from database.models import async_session, User, PhysicalEntity, Organization
from datetime import datetime

async def get_or_create_user(telegram_id: int, username: str, full_name: str):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        
        user = result.scalar_one_or_none()
        
        if user is None:
            user = User(
                telegram_id=telegram_id,
                username=username,
                full_name=full_name
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        
        return user

async def create_physical_entity(user_id: int, name: str, age: int, phone: str, email: str):
    async with async_session() as session:
        physical_entity = PhysicalEntity(
            user_id=user_id,
            name=name,
            age=age,
            phone=phone,
            email=email
        )
        session.add(physical_entity)
        await session.commit()
        return physical_entity

async def create_organization(user_id: int, name: str, phone: str, email: str, address: str):
    async with async_session() as session:
        organization = Organization(
            user_id=user_id,
            name=name,
            phone=phone,
            email=email,
            address=address
        )
        session.add(organization)
        await session.commit()
        return organization

async def get_user_physical_entities(telegram_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(PhysicalEntity)
            .join(User)
            .where(User.telegram_id == telegram_id)
        )
        return result.scalars().all()

async def get_user_organizations(telegram_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Organization)
            .join(User)
            .where(User.telegram_id == telegram_id)
        )
        return result.scalars().all()