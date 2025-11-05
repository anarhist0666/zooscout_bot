# Импорт необходимых компонентов из aiogram для работы с Telegram ботом
from aiogram.filters import Command, CommandStart
from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import PhotoSize
from aiogram import Bot
import asyncio
from app.key import search_main, category_search
from io import BytesIO
from database.db_operations import delete_animal, get_user_animals_with_photos_and_ids
from app.key import get_delete_keyboard

# Импорт функций для работы с базой данных
from database.db_operations import (
    get_or_create_user, 
    create_physical_entity, 
    create_organization,
    check_user_has_data, 
    create_animal, 
    download_photo_as_bytes,
    get_user_physical_entities, 
    get_user_organizations, 
    get_user_animals_with_photos_and_ids,
    get_random_animal_with_owner,
    get_random_animal_by_category,
    delete_animal
)
import app.key as kb

# Создание роутера для обработки сообщений
router = Router()

# Классы состояний для хранения данных между шагами диалога
class SearchState(StatesGroup):
    selected_category = State()  # Состояние для хранения выбранной категории поиска

class RegisterPhysicalEntity(StatesGroup):
    name = State()      # Имя физического лица
    age = State()       # Возраст
    contacts = State()  # Контактные данные
    mail = State()      # Электронная почта

class RegisterPhysicalOrganization(StatesGroup):
    organization = State()  # Название организации
    contacts = State()      # Контактные данные
    mail = State()          # Электронная почта
    address = State()       # Адрес организации

class AnimalForm(StatesGroup):
    category = State()      # Категория животного
    name = State()          # Имя животного
    description = State()   # Описание животного
    photo = State()         # Фото животного


# Обработчик команды /start - начальная точка взаимодействия с ботом
@router.message(CommandStart())
async def st(message: Message):
    # Создаем/получаем пользователя
    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name
    )
    
    # Проверяем, есть ли у пользователя данные
    has_data = await check_user_has_data(message.from_user.id)
    
    if has_data:
        # У пользователя уже есть данные - показываем кнопки поиска
        await message.answer(
            f'С возвращением 👋\n'
            f'Выберите действие:',
            reply_markup=kb.search
        )
    else:
        # Новый пользователь - предлагаем регистрацию
        await message.answer(
            text='Добро пожаловать! Кем Вы являетесь?', 
            reply_markup=kb.main
        )


# Обработчик выбора "Физическое лицо" - начало регистрации
@router.message(F.text == "Физическое лицо")
async def nice(message: Message, state: FSMContext):
    await state.set_state(RegisterPhysicalEntity.name)
    await message.answer('Как Вас зовут?')

# Обработчик выбора "Организация" - начало регистрации
@router.message(F.text == "Организация")
async def nice2(message: Message, state: FSMContext):
    await state.set_state(RegisterPhysicalOrganization.organization)
    await message.answer("Введите название Вашей организации")

# Обработчики для пошаговой регистрации организации
@router.message(RegisterPhysicalOrganization.organization)
async def register_org(message: Message, state: FSMContext):
    await state.update_data(organization=message.text)
    await state.set_state(RegisterPhysicalOrganization.contacts)
    await message.answer("Введите свой номер телефона")

@router.message(RegisterPhysicalOrganization.contacts)
async def register_contacts_org(message: Message, state: FSMContext):
    await state.update_data(contacts=message.text)
    await state.set_state(RegisterPhysicalOrganization.mail)
    await message.answer("Введите свою электронную почту")

@router.message(RegisterPhysicalOrganization.mail)
async def register_mail_org(message: Message, state: FSMContext):
    await state.update_data(mail=message.text)
    await state.set_state(RegisterPhysicalOrganization.address)
    await message.answer("Введите Ваш адрес организации")

@router.message(RegisterPhysicalOrganization.address)
async def register_mail_org(message: Message, state: FSMContext):
    await state.update_data(address=message.text)
    data = await state.get_data()
    await state.clear()

    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name
    )

    organization = await create_organization(
        user_id=user.id,
        name=data["organization"],
        phone=data["contacts"],
        email=data["mail"],
        address=data["address"]
    )

    await message.answer(
        f'Регистрация завершена!\n\n'
        f'Ваша организация: {data["organization"]}\n'
        f'Ваш адрес: {data["address"]}\n'
        f'Номер: {data["contacts"]}\n'
        f'Почта: {data["mail"]}'
    ,reply_markup=kb.search)

# Обработчики для пошаговой регистрации физического лица
@router.message(RegisterPhysicalEntity.name)
async def register_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(RegisterPhysicalEntity.age)
    await message.answer('Введите свой возраст')

@router.message(RegisterPhysicalEntity.age)
async def register_age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await state.set_state(RegisterPhysicalEntity.contacts)
    await message.answer('Введите свой номер телефона')

@router.message(RegisterPhysicalEntity.contacts)
async def register_number_with_contact(message: Message, state: FSMContext):
    await state.update_data(contacts=message.text)
    await state.set_state(RegisterPhysicalEntity.mail)
    await message.answer('Введите свою почту')

@router.message(RegisterPhysicalEntity.mail)
async def register_number_with_contact2(message: Message, state: FSMContext):
    await state.update_data(mail=message.text)
    data = await state.get_data()
    await state.clear()
    
    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name
    )

    physical_entity = await create_physical_entity(
        user_id=user.id,
        name=data["name"],
        age=data["age"],
        phone=data["contacts"],
        email=data["mail"]
    )

    await message.answer(
        f'Регистрация завершена!\n\n'
        f'Ваше имя: {data["name"]}\n'
        f'Ваш возраст: {data["age"]}\n'
        f'Номер: {data["contacts"]}\n'
        f'Почта: {data["mail"]}'
    ,reply_markup=kb.search)


# Обработчики для создания анкеты животного

@router.message(F.text == "Заполнение анкеты")
async def start_animal_form(message: Message, state: FSMContext):
    await state.set_state(AnimalForm.category)
    await message.answer(
        "Выберите категорию животного:",
        reply_markup=kb.animal_category
    )

@router.message(AnimalForm.category, F.text.in_(['Собака', 'Кошка', 'Другие животные']))
async def process_category(message: Message, state: FSMContext):
    await state.update_data(category=message.text)
    await state.set_state(AnimalForm.name)
    await message.answer(
        "Введите имя животного:",
        reply_markup=kb.cancel_kb
    )

@router.message(AnimalForm.name)
async def process_name(message: Message, state: FSMContext):
    if message.text == 'Отмена':
        await state.clear()
        await message.answer("Заполнение анкеты отменено", reply_markup=kb.search)
        return
        
    await state.update_data(name=message.text)
    await state.set_state(AnimalForm.description)
    await message.answer("Введите описание животного:")

@router.message(AnimalForm.description)
async def process_description(message: Message, state: FSMContext):
    if message.text == 'Отмена':
        await state.clear()
        await message.answer("Заполнение анкеты отменено", reply_markup=kb.search)
        return
        
    await state.update_data(description=message.text)
    await state.set_state(AnimalForm.photo)
    await message.answer("Загрузите фото животного:")

@router.message(AnimalForm.photo, F.photo)
async def process_photo(message: Message, state: FSMContext, bot: Bot):
    if message.text == 'Отмена':
        await state.clear()
        await message.answer("Заполнение анкеты отменено", reply_markup=kb.search)
        return

    # Получаем самое большое фото
    photo = message.photo[-1]
    file_id = photo.file_id
    
    # Скачиваем фото как bytes
    photo_bytes = await download_photo_as_bytes(bot, file_id)
    
    data = await state.get_data()
    await state.clear()

    # Получаем пользователя
    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name
    )

    # Создаем запись животного
    animal = await create_animal(
        user_id=user.id,
        category=data["category"],
        name=data["name"],
        description=data["description"],
        photo_data=photo_bytes,
        telegram_file_id=file_id
    )

    # Отправляем подтверждение (используем оригинальное фото из сообщения)
    await message.answer_photo(
        photo=file_id,
        caption=f"Анкета создана! ✅\n\n"
                f"Категория: {data['category']}\n"
                f"Имя: {data['name']}\n"
                f"Описание: {data['description']}",
        reply_markup=kb.search
    )

# Обработчики некорректного ввода при заполнении анкеты животного
@router.message(AnimalForm.category)
async def incorrect_category(message: Message):
    await message.answer("Пожалуйста, выберите категорию из предложенных:", reply_markup=kb.animal_category)

@router.message(AnimalForm.photo)
async def incorrect_photo(message: Message):
    await message.answer("Пожалуйста, загрузите фото животного:")


# Обработчик кнопки "Мои анкеты" - показывает все созданные пользователем анкеты
@router.message(F.text == "Мои анкеты")
async def show_my_profiles(message: Message, bot: Bot):
    user_id = message.from_user.id
    
    # Получаем все данные пользователя
    physical_entities = await get_user_physical_entities(user_id)
    organizations = await get_user_organizations(user_id)
    animals = await get_user_animals_with_photos_and_ids(user_id)  # Используем обновленную функцию
    
    # Проверяем, есть ли вообще анкеты
    if not physical_entities and not organizations and not animals:
        await message.answer(
            "У вас пока нет созданных анкет.\n"
            "Создайте свою первую анкету через 'Заполнение анкеты'",
            reply_markup=kb.search
        )
        return
    
    # Отправляем физические лица
    if physical_entities:
        await message.answer("📋 <b>Ваши физические лица:</b>", parse_mode='HTML')
        for entity in physical_entities:
            await message.answer(
                f"👤 <b>Физ. лицо</b>\n"
                f"Имя: {entity.name}\n"
                f"Возраст: {entity.age}\n"
                f"Телефон: {entity.phone}\n"
                f"Email: {entity.email}\n"
                f"Создано: {entity.created_at.strftime('%d.%m.%Y %H:%M')}",
                parse_mode='HTML'
            )
        await asyncio.sleep(0.5)
    
    # Отправляем организации
    if organizations:
        await message.answer("🏢 <b>Ваши организации:</b>", parse_mode='HTML')
        for org in organizations:
            await message.answer(
                f"🏢 <b>Организация</b>\n"
                f"Название: {org.name}\n"
                f"Телефон: {org.phone}\n"
                f"Email: {org.email}\n"
                f"Адрес: {org.address}\n"
                f"Создано: {org.created_at.strftime('%d.%m.%Y %H:%M')}",
                parse_mode='HTML'
            )
        await asyncio.sleep(0.5)
    
    # Отправляем животных с кнопками удаления
    if animals:
        await message.answer("🐾 <b>Ваши животные:</b>", parse_mode='HTML')
        for animal in animals:
            try:
                # Пробуем использовать telegram_file_id - это самый надежный способ
                if animal.telegram_file_id:
                    await message.answer_photo(
                        photo=animal.telegram_file_id,
                        caption=(
                            f"🐾 <b>Животное</b>\n"
                            f"Категория: {animal.category}\n"
                            f"Имя: {animal.name}\n"
                            f"Описание: {animal.description}\n"
                            f"Создано: {animal.created_at.strftime('%d.%m.%Y %H:%M')}"
                        ),
                        parse_mode='HTML',
                        reply_markup=get_delete_keyboard(animal.id)  # Добавляем кнопку удаления
                    )
                else:
                    # Используем BufferedInputFile если нет file_id
                    photo_file = BufferedInputFile(
                        animal.photo_data, 
                        filename=f"{animal.name}.jpg"
                    )
                    await message.answer_photo(
                        photo=photo_file,
                        caption=(
                            f"🐾 <b>Животное</b>\n"
                            f"Категория: {animal.category}\n"
                            f"Имя: {animal.name}\n"
                            f"Описание: {animal.description}\n"
                            f"Создано: {animal.created_at.strftime('%d.%m.%Y %H:%M')}"
                        ),
                        parse_mode='HTML',
                        reply_markup=get_delete_keyboard(animal.id)  # Добавляем кнопку удаления
                    )
            except Exception as e:
                # Если возникла ошибка с фото, отправляем без фото
                await message.answer(
                    f"🐾 <b>Животное</b>\n"
                    f"Категория: {animal.category}\n"
                    f"Имя: {animal.name}\n"
                    f"Описание: {animal.description}\n"
                    f"Создано: {animal.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                    f"⚠️ Фото недоступно",
                    parse_mode='HTML',
                    reply_markup=get_delete_keyboard(animal.id)  # Добавляем кнопку удаления
                )
            await asyncio.sleep(0.5)

from app.key import search_main, category_search

# Обработчик кнопки "Поиск" - основное меню поиска
@router.message(F.text == "Поиск")
async def search_menu(message: Message, state: FSMContext):
    # Сбрасываем состояние при новом поиске
    await state.clear()
    await message.answer(
        "🔍 <b>Выберите тип поиска:</b>",
        parse_mode='HTML',
        reply_markup=search_main
    )

# Обработчик для "Показывать всех" - поиск без фильтрации по категории
@router.message(F.text == "Показывать всех")
async def show_all_animals(message: Message, bot: Bot, state: FSMContext):
    # Сохраняем, что выбрана категория "все"
    await state.update_data(selected_category="all")
    await search_random_animal(message, bot, state)

# Обработчик для "Выбрать категорию" - показывает инлайн кнопки с категориями
@router.message(F.text == "Выбрать категорию")
async def choose_category(message: Message):
    await message.answer(
        "🐾 <b>Выберите категорию животных:</b>",
        parse_mode='HTML',
        reply_markup=category_search
    )

# Обработчик для инлайн кнопок категорий
@router.callback_query(F.data.startswith('search_'))
async def handle_category_search(callback: CallbackQuery, bot: Bot, state: FSMContext):
    category_map = {
        'search_dogs': 'Собака',
        'search_cats': 'Кошка', 
        'search_others': 'Другие животные'
    }
    
    category = category_map.get(callback.data)
    if not category:
        await callback.answer("Категория не найдена")
        return
    
    # Сохраняем выбранную категорию в состоянии
    await state.update_data(selected_category=category)
    
    # Получаем случайное животное выбранной категории
    animal_data = await get_random_animal_by_category(category)
    
    if not animal_data:
        await callback.message.answer(
            f"😔 В категории '{category}' пока нет анкет.",
            reply_markup=kb.search_actions
        )
        await callback.answer()
        return
    
    # При поиске по категории НЕ показываем категорию животного
    await send_animal_profile(callback.message, animal_data, bot, show_category=False)
    await callback.answer()

# Функция для случайного поиска (обновленная)
async def search_random_animal(message: Message, bot: Bot, state: FSMContext):
    # Получаем сохраненную категорию из состояния
    data = await state.get_data()
    selected_category = data.get('selected_category')
    
    if selected_category == "all":
        # Ищем любое случайное животное и показываем категорию
        animal_data = await get_random_animal_with_owner()
        show_category = True
    else:
        # Ищем по конкретной категории и НЕ показываем категорию
        animal_data = await get_random_animal_by_category(selected_category)
        show_category = False
    
    if not animal_data:
        category_name = "всех категорий" if selected_category == "all" else selected_category
        await message.answer(
            f"😔 В категории '{category_name}' пока нет анкет.",
            reply_markup=kb.search_actions
        )
        return
    
    await send_animal_profile(message, animal_data, bot, show_category)

# Обработчик для кнопки "Следующая анкета" - продолжает поиск в выбранной категории
@router.message(F.text == "Следующая анкета")
async def next_animal(message: Message, bot: Bot, state: FSMContext):
    # Проверяем, есть ли сохраненная категория
    data = await state.get_data()
    selected_category = data.get('selected_category')
    
    if selected_category:
        # Если категория сохранена, сразу показываем следующую анкету
        await search_random_animal(message, bot, state)
    else:
        # Если категория не сохранена, показываем меню выбора
        await message.answer(
            "🔍 <b>Выберите тип поиска:</b>",
            parse_mode='HTML',
            reply_markup=search_main
        )

# Обработчик для кнопки "В главное меню" - возврат к основному функционалу
@router.message(F.text == "В главное меню")
async def back_to_main_menu(message: Message, state: FSMContext):
    # Сбрасываем состояние при возврате в главное меню
    await state.clear()
    await message.answer(
        "Возвращаемся в главное меню",
        reply_markup=kb.search
    )

# Общая функция для отправки анкеты животного
async def send_animal_profile(message: Message, animal_data: dict, bot: Bot, show_category: bool = False):
    animal = animal_data['animal']
    user = animal_data['user']
    physical_entities = animal_data['physical_entities']
    organizations = animal_data['organizations']
    
    try:
        # Формируем описание животного
        animal_caption = (
            f"🐾 <b>Найдено животное!</b>\n\n"
            f"<b>Животное:</b>\n"
            f"• Имя: {animal.name}\n"
        )
        
        # Показываем категорию только если show_category=True
        if show_category:
            animal_caption += f"• Категория: {animal.category}\n"
        
        animal_caption += f"• Описание: {animal.description}\n\n"
        
        # Добавляем информацию о владельце
        animal_caption += f"<b>Контактная информация:</b>\n"
        
        # Если есть физические лица
        if physical_entities:
            for entity in physical_entities:
                animal_caption += (
                    f"👤 <b>Физ. лицо</b>\n"
                    f"• Имя: {entity.name}\n"
                    f"• Возраст: {entity.age}\n"
                    f"• Телефон: {entity.phone}\n"
                    f"• Email: {entity.email}\n"
                )
                break
        
        # Если есть организации
        elif organizations:
            for org in organizations:
                animal_caption += (
                    f"🏢 <b>Организация</b>\n"
                    f"• Название: {org.name}\n"
                    f"• Адрес: {org.address}\n"
                    f"• Телефон: {org.phone}\n"
                    f"• Email: {org.email}\n"
                )
                break
        
        else:
            animal_caption += "⚠️ Контактная информация не указана\n"
        
        # Отправляем фото животного
        if animal.telegram_file_id:
            await message.answer_photo(
                photo=animal.telegram_file_id,
                caption=animal_caption,
                parse_mode='HTML',
                reply_markup=kb.search_actions
            )
        else:
            photo_file = BufferedInputFile(
                animal.photo_data, 
                filename=f"{animal.name}.jpg"
            )
            await message.answer_photo(
                photo=photo_file,
                caption=animal_caption,
                parse_mode='HTML',
                reply_markup=kb.search_actions
            )
            
    except Exception as e:
        await message.answer(
            f"Произошла ошибка при поиске: {str(e)}",
            reply_markup=kb.search_actions
        )

# Обработчик для кнопки удаления анкеты животного
@router.callback_query(F.data.startswith('delete_animal_'))
async def handle_delete_animal(callback: CallbackQuery, bot: Bot):
    # Извлекаем ID животного из callback_data
    animal_id = int(callback.data.replace('delete_animal_', ''))
    
    # Получаем пользователя
    user = await get_or_create_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        full_name=callback.from_user.full_name
    )
    
    # Пытаемся удалить животное
    success = await delete_animal(animal_id, user.id)
    
    if success:
        # Удаляем сообщение с анкетой
        await callback.message.delete()
        await callback.answer("✅ Анкета успешно удалена")
        
        # Отправляем подтверждение
        await callback.message.answer(
            "✅ Анкета животного была удалена",
            reply_markup=kb.search
        )
    else:
        await callback.answer("❌ Не удалось удалить анкету. Возможно, она уже была удалена.")

# Пасхолка
@router.message(Command("alina"))
async def alinaTraktor(message: Message):
    await message.reply(text='трактор')