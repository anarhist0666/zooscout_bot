# Импорт необходимых компонентов SQLAlchemy и других модулей
from sqlalchemy import select, delete, and_
from database.models import async_session, User, PhysicalEntity, Organization, Animal, Favorite  # Добавлен Favorite
from datetime import datetime
from sqlalchemy import select, func

# Функция проверки наличия данных у пользователя (физические лица или организации)
async def check_user_has_data(telegram_id: int) -> bool:
    async with async_session() as session:
        # Проверяем наличие физ. лиц пользователя
        physical_result = await session.execute(
            select(PhysicalEntity)
            .join(User)
            .where(User.telegram_id == telegram_id)
        )
        has_physical = physical_result.scalar_one_or_none() is not None
        
        # Проверяем наличие организаций пользователя
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
            await session.refresh(user)
        
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
        await session.refresh(physical_entity)
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
        await session.refresh(organization)
        return organization

# Функция получения всех физических лиц пользователя
async def get_user_physical_entities(telegram_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(PhysicalEntity)
            .join(User)
            .where(User.telegram_id == telegram_id)
        )
        return result.scalars().all()

# Функция получения всех организаций пользователя
async def get_user_organizations(telegram_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Organization)
            .join(User)
            .where(User.telegram_id == telegram_id)
        )
        return result.scalars().all()

# Функция создания записи животного с привязкой к профилю
async def create_animal(user_id: int, category: str, name: str, description: str, photo_data: bytes, telegram_file_id: str = None, physical_entity_id: int = None, organization_id: int = None):
    async with async_session() as session:
        animal = Animal(
            user_id=user_id,
            category=category,
            name=name,
            description=description,
            photo_data=photo_data,
            telegram_file_id=telegram_file_id,
            physical_entity_id=physical_entity_id,
            organization_id=organization_id
        )
        session.add(animal)
        await session.commit()
        await session.refresh(animal)
        return animal

# Функция скачивания фото из Telegram и преобразования в bytes
async def download_photo_as_bytes(bot, file_id: str) -> bytes:
    try:
        # Получаем информацию о файле из Telegram
        file = await bot.get_file(file_id)
        # Скачиваем файл как поток байтов
        photo_bytes = await bot.download_file(file.file_path)
        return photo_bytes.getvalue()
    except Exception as e:
        print(f"Ошибка скачивания фото: {e}")
        return b''

# Функция получения всех животных пользователя с их ID
async def get_user_animals_with_photos_and_ids(telegram_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Animal)
            .join(User)
            .where(User.telegram_id == telegram_id)
        )
        return result.scalars().all()

# Функция получения всех животных для поочередного показа
async def get_all_animals_with_owners():
    async with async_session() as session:
        # Получаем всех животных
        result = await session.execute(
            select(Animal)
            .order_by(Animal.created_at.desc())
        )
        animals = result.scalars().all()
        
        animals_data = []
        for animal in animals:
            # Получаем информацию о владельце животного
            user_result = await session.execute(
                select(User).where(User.id == animal.user_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                continue
            
            # Получаем привязанный профиль
            physical_entity = None
            organization = None
            
            if animal.physical_entity_id:
                physical_result = await session.execute(
                    select(PhysicalEntity).where(PhysicalEntity.id == animal.physical_entity_id)
                )
                physical_entity = physical_result.scalar_one_or_none()
            elif animal.organization_id:
                org_result = await session.execute(
                    select(Organization).where(Organization.id == animal.organization_id)
                )
                organization = org_result.scalar_one_or_none()
            else:
                # Если привязки нет, получаем первый доступный профиль
                physical_result = await session.execute(
                    select(PhysicalEntity).where(PhysicalEntity.user_id == user.id)
                )
                physical_entities = physical_result.scalars().all()
                if physical_entities:
                    physical_entity = physical_entities[0]
                else:
                    org_result = await session.execute(
                        select(Organization).where(Organization.user_id == user.id)
                    )
                    organizations = org_result.scalars().all()
                    if organizations:
                        organization = organizations[0]
            
            animals_data.append({
                'animal': animal,
                'user': user,
                'physical_entities': [physical_entity] if physical_entity else [],
                'organizations': [organization] if organization else []
            })
        
        return animals_data

# Функция получения всех животных определенной категории для поочередного показа
async def get_all_animals_by_category(category: str):
    async with async_session() as session:
        # Получаем всех животных по категории
        result = await session.execute(
            select(Animal)
            .where(Animal.category == category)
            .order_by(Animal.created_at.desc())
        )
        animals = result.scalars().all()
        
        animals_data = []
        for animal in animals:
            # Получаем информацию о владельце
            user_result = await session.execute(
                select(User).where(User.id == animal.user_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                continue
            
            # Получаем привязанный профиль
            physical_entity = None
            organization = None
            
            if animal.physical_entity_id:
                physical_result = await session.execute(
                    select(PhysicalEntity).where(PhysicalEntity.id == animal.physical_entity_id)
                )
                physical_entity = physical_result.scalar_one_or_none()
            elif animal.organization_id:
                org_result = await session.execute(
                    select(Organization).where(Organization.id == animal.organization_id)
                )
                organization = org_result.scalar_one_or_none()
            else:
                # Если привязки нет, получаем первый доступный профиль
                physical_result = await session.execute(
                    select(PhysicalEntity).where(PhysicalEntity.user_id == user.id)
                )
                physical_entities = physical_result.scalars().all()
                if physical_entities:
                    physical_entity = physical_entities[0]
                else:
                    org_result = await session.execute(
                        select(Organization).where(Organization.user_id == user.id)
                    )
                    organizations = org_result.scalars().all()
                    if organizations:
                        organization = organizations[0]
            
            animals_data.append({
                'animal': animal,
                'user': user,
                'physical_entities': [physical_entity] if physical_entity else [],
                'organizations': [organization] if organization else []
            })
        
        return animals_data

# Функция удаления животного с проверкой прав доступа
async def delete_animal(animal_id: int, user_id: int):
    async with async_session() as session:
        # Проверяем, что животное принадлежит пользователю
        result = await session.execute(
            select(Animal)
            .where(Animal.id == animal_id)
            .where(Animal.user_id == user_id)
        )
        animal = result.scalar_one_or_none()
        
        if not animal:
            return False
        
        # Удаляем животное из базы данных
        await session.delete(animal)
        await session.commit()
        return True

# Функция удаления физического лица с проверкой прав доступа
async def delete_physical_entity(entity_id: int, user_id: int):
    async with async_session() as session:
        # Проверяем, что физическое лицо принадлежит пользователю
        result = await session.execute(
            select(PhysicalEntity)
            .where(PhysicalEntity.id == entity_id)
            .where(PhysicalEntity.user_id == user_id)
        )
        entity = result.scalar_one_or_none()
        
        if not entity:
            return False
        
        # Удаляем запись из базы данных
        await session.delete(entity)
        await session.commit()
        return True

# Функция удаления организации с проверкой прав доступа
async def delete_organization(org_id: int, user_id: int):
    async with async_session() as session:
        # Проверяем, что организация принадлежит пользователю
        result = await session.execute(
            select(Organization)
            .where(Organization.id == org_id)
            .where(Organization.user_id == user_id)
        )
        organization = result.scalar_one_or_none()
        
        if not organization:
            return False
        
        # Удаляем запись из базы данных
        await session.delete(organization)
        await session.commit()
        return True

    
# Функция добавления животного в избранное
# Функция добавления животного в избранное
async def add_to_favorites(user_id: int, animal_id: int):
    async with async_session() as session:
        # Проверяем, не добавлено ли уже в избранное
        existing_favorite = await session.execute(
            select(Favorite)
            .where(Favorite.user_id == user_id)
            .where(Favorite.animal_id == animal_id)
        )
        existing = existing_favorite.scalar_one_or_none()
                
        if existing:
            return False  # Уже в избранном
        
        # Добавляем в избранное
        favorite = Favorite(
            user_id=user_id,
            animal_id=animal_id
        )
        session.add(favorite)
        await session.commit()
        await session.refresh(favorite)
        return True

# Функция удаления животного из избранного
async def remove_from_favorites(user_id: int, animal_id: int):
    async with async_session() as session:
        # Находим запись в избранном
        favorite_result = await session.execute(
            select(Favorite)
            .where(and_(Favorite.user_id == user_id, Favorite.animal_id == animal_id))
        )
        favorite = favorite_result.scalar_one_or_none()
        
        if not favorite:
            return False  # Не было в избранном
        
        # Удаляем из избранного
        await session.delete(favorite)
        await session.commit()
        return True


# Функция проверки, находится ли животное в избранном у пользователя
async def is_animal_in_favorites(telegram_id: int, animal_id: int):
    async with async_session() as session:
        # Сначала находим user_id по telegram_id
        user_result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            return False
        
        # Затем ищем в избранном по user_id
        result = await session.execute(
            select(Favorite)
            .where(Favorite.user_id == user.id)
            .where(Favorite.animal_id == animal_id)
        )
        favorite = result.scalar_one_or_none()
        return favorite is not None

# Функция получения всех избранных животных пользователя (новая версия)
async def get_user_favorites_with_owners(user_id: int):
    async with async_session() as session:
        try:
            # Простой запрос для получения избранных с животными
            favorites_result = await session.execute(
                select(Favorite, Animal)
                .join(Animal, Favorite.animal_id == Animal.id)
                .where(Favorite.user_id == user_id)
                .order_by(Favorite.created_at.desc())
            )
            
            results = favorites_result.all()
            
            favorites_data = []
            
            for favorite, animal in results:
                
                # Получаем владельца животного
                owner_result = await session.execute(
                    select(User).where(User.id == animal.user_id)
                )
                owner = owner_result.scalar_one_or_none()
                
                if not owner:
                    continue
                
                # Получаем профили владельца
                physical_entities = []
                organizations = []
                
                # Получаем физические лица
                physical_result = await session.execute(
                    select(PhysicalEntity).where(PhysicalEntity.user_id == owner.id)
                )
                physical_entities = physical_result.scalars().all()
                
                # Получаем организации
                org_result = await session.execute(
                    select(Organization).where(Organization.user_id == owner.id)
                )
                organizations = org_result.scalars().all()
                
                # Используем привязанный профиль или первый доступный
                used_physical_entity = None
                used_organization = None
                
                if animal.physical_entity_id:
                    # Ищем конкретное привязанное физическое лицо
                    for entity in physical_entities:
                        if entity.id == animal.physical_entity_id:
                            used_physical_entity = entity
                            break
                elif animal.organization_id:
                    # Ищем конкретную привязанную организацию
                    for org in organizations:
                        if org.id == animal.organization_id:
                            used_organization = org
                            break
                else:
                    # Берем первый доступный профиль
                    if physical_entities:
                        used_physical_entity = physical_entities[0]
                    elif organizations:
                        used_organization = organizations[0]
                
                favorites_data.append({
                    'animal': animal,
                    'user': owner,
                    'physical_entities': [used_physical_entity] if used_physical_entity else [],
                    'organizations': [used_organization] if used_organization else [],
                    'favorite_id': favorite.id
                })
            
            return favorites_data
            
        except Exception as e:
            return []
