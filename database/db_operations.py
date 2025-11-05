# Импорт необходимых компонентов SQLAlchemy и других модулей
from sqlalchemy import select
from database.models import async_session, User, PhysicalEntity, Organization
from datetime import datetime
from database.models import Animal
from sqlalchemy import select
from sqlalchemy import func

# Функция проверки наличия данных у пользователя (физические лица или организации)
async def check_user_has_data(telegram_id: int) -> bool:
    async with async_session() as session:
        # Проверяем наличие физ. лиц пользователя
        # JOIN с таблицей User чтобы найти физ. лица по telegram_id
        physical_result = await session.execute(
            select(PhysicalEntity)
            .join(User)
            .where(User.telegram_id == telegram_id)
        )
        has_physical = physical_result.scalar_one_or_none() is not None
        
        # Проверяем наличие организаций пользователя
        # JOIN с таблицей User чтобы найти организации по telegram_id
        org_result = await session.execute(
            select(Organization)
            .join(User)
            .where(User.telegram_id == telegram_id)
        )
        has_organizations = org_result.scalar_one_or_none() is not None
        
        # Возвращаем True если есть хоть какие-то данные
        return has_physical or has_organizations

        
# Функция для получения существующего пользователя или создания нового
async def get_or_create_user(telegram_id: int, username: str, full_name: str):
    async with async_session() as session:
        # Ищем пользователя по telegram_id
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        
        user = result.scalar_one_or_none()
        
        if user is None:
            # Если пользователь не найден, создаем нового
            user = User(
                telegram_id=telegram_id,
                username=username,
                full_name=full_name
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)  # Обновляем объект чтобы получить сгенерированный ID
        
        return user

# Функция создания записи физического лица
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

# Функция создания записи организации
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

# Функция получения всех физических лиц пользователя
async def get_user_physical_entities(telegram_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(PhysicalEntity)
            .join(User)
            .where(User.telegram_id == telegram_id)
        )
        return result.scalars().all()  # Возвращаем все записи в виде списка

# Функция получения всех организаций пользователя
async def get_user_organizations(telegram_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Organization)
            .join(User)
            .where(User.telegram_id == telegram_id)
        )
        return result.scalars().all()  # Возвращаем все записи в виде списка

# Функция создания записи животного
async def create_animal(user_id: int, category: str, name: str, description: str, photo_data: bytes, telegram_file_id: str = None):
    async with async_session() as session:
        animal = Animal(
            user_id=user_id,
            category=category,
            name=name,
            description=description,
            photo_data=photo_data,  # Бинарные данные фото
            telegram_file_id=telegram_file_id  # File_id из Telegram (опционально)
        )
        session.add(animal)
        await session.commit()
        return animal

# Функция скачивания фото из Telegram и преобразования в bytes
async def download_photo_as_bytes(bot, file_id: str) -> bytes:
    try:
        # Получаем информацию о файле из Telegram
        file = await bot.get_file(file_id)
        # Скачиваем файл как поток байтов
        photo_bytes = await bot.download_file(file.file_path)
        return photo_bytes.getvalue()  # Преобразуем в bytes
    except Exception as e:
        print(f"Ошибка скачивания фото: {e}")
        return b''  # Возвращаем пустые bytes при ошибке

# Функция получения всех животных пользователя с их ID
async def get_user_animals_with_photos_and_ids(telegram_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Animal)
            .join(User)
            .where(User.telegram_id == telegram_id)
        )
        return result.scalars().all()  # Возвращаем все записи животных пользователя


# Функция получения случайного животного с информацией о владельце
async def get_random_animal_with_owner():
    async with async_session() as session:
        # Получаем случайное животное
        # func.random() - функция для случайной сортировки (зависит от СУБД)
        result = await session.execute(
            select(Animal)
            .order_by(func.random())  # Случайный порядок
            .limit(1)  # Берем только одну запись
        )
        animal = result.scalar_one_or_none()
        
        if not animal:
            return None
        
        # Получаем информацию о владельце животного
        user_result = await session.execute(
            select(User).where(User.id == animal.user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            return None
        
        # Получаем физические лица владельца (если есть)
        physical_result = await session.execute(
            select(PhysicalEntity).where(PhysicalEntity.user_id == user.id)
        )
        physical_entities = physical_result.scalars().all()
        
        # Получаем организации владельца (если есть)
        org_result = await session.execute(
            select(Organization).where(Organization.user_id == user.id)
        )
        organizations = org_result.scalars().all()
        
        # Возвращаем структурированные данные о животном и его владельце
        return {
            'animal': animal,
            'user': user,
            'physical_entities': physical_entities,
            'organizations': organizations
        }

# Функция получения случайного животного по определенной категории
async def get_random_animal_by_category(category: str):
    async with async_session() as session:
        # Получаем случайное животное по категории
        # Фильтруем по категории и сортируем случайным образом
        result = await session.execute(
            select(Animal)
            .where(Animal.category == category)
            .order_by(func.random())
            .limit(1)
        )
        animal = result.scalar_one_or_none()
        
        if not animal:
            return None
        
        # Получаем информацию о владельце
        user_result = await session.execute(
            select(User).where(User.id == animal.user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            return None
        
        # Получаем физические лица владельца
        physical_result = await session.execute(
            select(PhysicalEntity).where(PhysicalEntity.user_id == user.id)
        )
        physical_entities = physical_result.scalars().all()
        
        # Получаем организации владельца
        org_result = await session.execute(
            select(Organization).where(Organization.user_id == user.id)
        )
        organizations = org_result.scalars().all()
        
        return {
            'animal': animal,
            'user': user,
            'physical_entities': physical_entities,
            'organizations': organizations
        }

# Функция удаления животного с проверкой прав доступа
async def delete_animal(animal_id: int, user_id: int):
    async with async_session() as session:
        # Проверяем, что животное принадлежит пользователю
        # Двойное условие: по ID животного и по user_id для безопасности
        result = await session.execute(
            select(Animal)
            .where(Animal.id == animal_id)
            .where(Animal.user_id == user_id)
        )
        animal = result.scalar_one_or_none()
        
        if not animal:
            return False  # Животное не найдено или не принадлежит пользователю
        
        # Удаляем животное из базы данных
        await session.delete(animal)
        await session.commit()
        return True  # Успешное удаление