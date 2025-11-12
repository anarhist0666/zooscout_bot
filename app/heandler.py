# Импорт необходимых компонентов из aiogram для работы с Telegram ботом
from aiogram.filters import Command, CommandStart
from aiogram import F, Router, Bot
from database.models import Animal
from aiogram.types import Message, CallbackQuery, BufferedInputFile, PhotoSize
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import asyncio
from sqlalchemy import select
from database.models import Favorite, async_session
from app.key import search_main, category_search, get_delete_keyboard, get_delete_physical_entity_keyboard, get_delete_organization_keyboard, get_attach_profile_keyboard, fill_form_menu, all_animals_viewed, get_like_keyboard, get_remove_favorite_keyboard
from io import BytesIO
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
    delete_animal,
    delete_physical_entity,
    delete_organization,
    get_all_animals_with_owners,
    get_all_animals_by_category,
    add_to_favorites,         # ← ИМПОРТИРОВАННАЯ ФУНКЦИЯ
    remove_from_favorites,    
    is_animal_in_favorites,   
    get_user_favorites_with_owners 
)
import app.key as kb

# Создание роутера для обработки сообщений
router = Router()

# Классы состояний для хранения данных между шагами диалога
class SearchState(StatesGroup):
    selected_category = State()
    current_index = State()
    animals_list = State()

class RegisterPhysicalEntity(StatesGroup):
    name = State()
    age = State()
    contacts = State()
    mail = State()

class RegisterPhysicalOrganization(StatesGroup):
    organization = State()
    contacts = State()
    mail = State()
    address = State()

class AnimalForm(StatesGroup):
    category = State()
    name = State()
    description = State()
    photo = State()
    profile_selection = State()

# Временное хранилище для данных животного между шагами
animal_temp_data = {}

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


# Обработчик кнопки "Заполнение анкеты" - новое меню
@router.message(F.text == "Заполнение анкеты")
async def fill_form_menu_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "📝 <b>Выберите тип анкеты для заполнения:</b>",
        parse_mode='HTML',
        reply_markup=kb.fill_form_menu
    )

# Обработчик кнопки "Создание нового профиля" - регистрация физ. лица или организации
@router.message(F.text == "Создание нового профиля")
async def create_new_profile(message: Message, state: FSMContext):
    await message.answer(
        text='Кем Вы являетесь?', 
        reply_markup=kb.main
    )

# Обработчик кнопки "Создание анкеты животного"
@router.message(F.text == "Создание анкеты животного")
async def start_animal_form(message: Message, state: FSMContext):
    await state.set_state(AnimalForm.category)
    await message.answer(
        "Выберите категорию животного:",
        reply_markup=kb.animal_category
    )

# Обработчики для шагов создания анкеты животного (категория, имя, описание)
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

# Обработчик фото животного - теперь с логикой выбора профиля
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
    
    # Получаем пользователя
    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name
    )

    # Получаем все профили пользователя
    physical_entities = await get_user_physical_entities(message.from_user.id)
    organizations = await get_user_organizations(message.from_user.id)

    total_profiles = len(physical_entities) + len(organizations)

    if total_profiles == 0:
        # Если нет профилей - сообщаем об ошибке
        await message.answer(
            "❌ У вас нет созданных профилей. Сначала создайте профиль (физическое лицо или организацию).",
            reply_markup=kb.fill_form_menu
        )
        await state.clear()
        return
    elif total_profiles == 1:
        # Если только один профиль - автоматически привязываем его
        profile_id = physical_entities[0].id if physical_entities else organizations[0].id
        profile_type = "physical" if physical_entities else "organization"
        
        # Сохраняем данные животного и создаем его сразу
        data = await state.get_data()
        await state.clear()
        
        animal = await create_animal(
            user_id=user.id,
            category=data["category"],
            name=data["name"],
            description=data["description"],
            photo_data=photo_bytes,
            telegram_file_id=file_id,
            physical_entity_id=profile_id if profile_type == "physical" else None,
            organization_id=profile_id if profile_type == "organization" else None
        )

        # Формируем сообщение о привязке
        profile_info = ""
        if profile_type == "physical":
            profile_info = f"👤 Привязано к физ. лицу: {physical_entities[0].name}"
        else:
            profile_info = f"🏢 Привязано к организации: {organizations[0].name}"

        # Отправляем подтверждение
        await message.answer_photo(
            photo=file_id,
            caption=f"✅ <b>Анкета создана!</b>\n\n"
                    f"🐾 <b>Животное</b>\n"
                    f"Категория: {data['category']}\n"
                    f"Имя: {data['name']}\n"
                    f"Описание: {data['description']}\n\n"
                    f"{profile_info}",
            parse_mode='HTML',
            reply_markup=kb.search
        )
    else:
        # Если несколько профилей - сохраняем данные во временное хранилище
        user_data = await state.get_data()
        animal_temp_data[message.from_user.id] = {
            'category': user_data["category"],
            'name': user_data["name"],
            'description': user_data["description"],
            'photo_data': photo_bytes,
            'telegram_file_id': file_id,
            'user_id': user.id
        }
        
        await state.set_state(AnimalForm.profile_selection)
        await message.answer("👥 <b>Выберите профиль для привязки к животному:</b>", parse_mode='HTML')
        
        # Показываем физические лица
        if physical_entities:
            for entity in physical_entities:
                await message.answer(
                    f"👤 <b>Физ. лицо</b>\n"
                    f"Имя: {entity.name}\n"
                    f"Возраст: {entity.age}\n"
                    f"Телефон: {entity.phone}\n"
                    f"Email: {entity.email}",
                    parse_mode='HTML',
                    reply_markup=kb.get_attach_profile_keyboard(entity.id, "physical")
                )
                await asyncio.sleep(0.3)
        
        # Показываем организации
        if organizations:
            for org in organizations:
                await message.answer(
                    f"🏢 <b>Организация</b>\n"
                    f"Название: {org.name}\n"
                    f"Телефон: {org.phone}\n"
                    f"Email: {org.email}\n"
                    f"Адрес: {org.address}",
                    parse_mode='HTML',
                    reply_markup=kb.get_attach_profile_keyboard(org.id, "organization")
                )
                await asyncio.sleep(0.3)

# Обработчик выбора профиля для привязки
@router.callback_query(F.data.startswith('attach_'))
async def handle_profile_selection(callback: CallbackQuery, state: FSMContext, bot: Bot):
    # Извлекаем данные из callback
    data_parts = callback.data.split('_')
    profile_type = data_parts[1]  # "physical" или "organization"
    profile_id = int(data_parts[2])
    
    user_id = callback.from_user.id
    
    # Получаем данные животного из временного хранилища
    if user_id not in animal_temp_data:
        await callback.answer("❌ Данные животного не найдены. Начните заново.")
        await state.clear()
        return
    
    animal_data = animal_temp_data[user_id]
    
    # Создаем животное с привязкой к выбранному профилю
    animal = await create_animal(
        user_id=animal_data['user_id'],
        category=animal_data['category'],
        name=animal_data['name'],
        description=animal_data['description'],
        photo_data=animal_data['photo_data'],
        telegram_file_id=animal_data['telegram_file_id'],
        physical_entity_id=profile_id if profile_type == "physical" else None,
        organization_id=profile_id if profile_type == "organization" else None
    )

    # Формируем сообщение о привязке
    profile_info = ""
    if profile_type == "physical":
        physical_entities = await get_user_physical_entities(user_id)
        for entity in physical_entities:
            if entity.id == profile_id:
                profile_info = f"👤 Привязано к физ. лицу: {entity.name}"
                break
    else:
        organizations = await get_user_organizations(user_id)
        for org in organizations:
            if org.id == profile_id:
                profile_info = f"🏢 Привязано к организации: {org.name}"
                break

    # Удаляем временные данные
    del animal_temp_data[user_id]
    await state.clear()

    # Отправляем подтверждение
    await callback.message.answer_photo(
        photo=animal_data['telegram_file_id'],
        caption=f"✅ <b>Анкета создана!</b>\n\n"
                f"🐾 <b>Животное</b>\n"
                f"Категория: {animal_data['category']}\n"
                f"Имя: {animal_data['name']}\n"
                f"Описание: {animal_data['description']}\n\n"
                f"{profile_info}",
        parse_mode='HTML',
        reply_markup=kb.search
    )
    
    await callback.answer("✅ Анкета животного создана!")

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
    animals = await get_user_animals_with_photos_and_ids(user_id)
    
    # Проверяем, есть ли вообще анкеты
    if not physical_entities and not organizations and not animals:
        await message.answer(
            "У вас пока нет созданных анкет.\n"
            "Создайте свою первую анкету через 'Заполнение анкеты'",
            reply_markup=kb.search
        )
        return
    
    # Отправляем физические лица с кнопками удаления
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
                parse_mode='HTML',
                reply_markup=kb.get_delete_physical_entity_keyboard(entity.id)
            )
        await asyncio.sleep(0.5)
    
    # Отправляем организации с кнопками удаления
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
                parse_mode='HTML',
                reply_markup=kb.get_delete_organization_keyboard(org.id)
            )
        await asyncio.sleep(0.5)
    
    # Отправляем животных с кнопками удаления
    if animals:
        await message.answer("🐾 <b>Ваши животные:</b>", parse_mode='HTML')
        for animal in animals:
            try:
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
                        reply_markup=kb.get_delete_keyboard(animal.id)
                    )
                else:
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
                        reply_markup=kb.get_delete_keyboard(animal.id)
                    )
            except Exception as e:
                await message.answer(
                    f"🐾 <b>Животное</b>\n"
                    f"Категория: {animal.category}\n"
                    f"Имя: {animal.name}\n"
                    f"Описание: {animal.description}\n"
                    f"Создано: {animal.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                    f"⚠️ Фото недоступно",
                    parse_mode='HTML',
                    reply_markup=kb.get_delete_keyboard(animal.id)
                )
            await asyncio.sleep(0.5)


# Обработчик кнопки "Поиск" - основное меню поиска
@router.message(F.text == "Поиск")
async def search_menu(message: Message, state: FSMContext):
    # Сбрасываем состояние при новом поиска
    await state.clear()
    await message.answer(
        "🔍 <b>Выберите тип поиска:</b>",
        parse_mode='HTML',
        reply_markup=search_main
    )

# Обработчик для "Показывать всех" - поиск без фильтрации по категории
@router.message(F.text == "Показывать всех")
async def show_all_animals(message: Message, bot: Bot, state: FSMContext):
    # Получаем все анкеты
    animals_data = await get_all_animals_with_owners()
    
    if not animals_data:
        await message.answer(
            "😔 Пока нет созданных анкет.",
            reply_markup=kb.search_main
        )
        return
    
    # Сохраняем данные в состоянии
    await state.set_state(SearchState.selected_category)
    await state.update_data(
        selected_category="all",
        current_index=0,
        animals_list=animals_data
    )
    
    # Показываем первую анкету
    await show_next_animal(message, bot, state)

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
    
    # Получаем все анкеты по категории
    animals_data = await get_all_animals_by_category(category)
    
    if not animals_data:
        await callback.message.answer(
            f"😔 В категории '{category}' пока нет анкет.",
            reply_markup=kb.search_main
        )
        await callback.answer()
        return
    
    # Сохраняем данные в состоянии
    await state.set_state(SearchState.selected_category)
    await state.update_data(
        selected_category=category,
        current_index=0,
        animals_list=animals_data
    )
    
    # Показываем первую анкету
    await show_next_animal(callback.message, bot, state)
    await callback.answer()

# Функция для показа следующей анкеты
async def show_next_animal(message: Message, bot: Bot, state: FSMContext):
    # Получаем данные из состояния
    data = await state.get_data()
    current_index = data.get('current_index', 0)
    animals_list = data.get('animals_list', [])
    selected_category = data.get('selected_category', 'all')
    
    # Проверяем, есть ли еще анкеты для показа
    if current_index >= len(animals_list):
        # Все анкеты показаны
        category_name = "всех категорий" if selected_category == "all" else selected_category
        await message.answer(
            f"✅ <b>Вы увидели все анкеты в категории '{category_name}'.</b>\n\n"
            f"Хотите начать просмотр заново или вернуться в главное меню?",
            parse_mode='HTML',
            reply_markup=kb.all_animals_viewed
        )
        return
    
    # Получаем текущую анкету
    animal_data = animals_list[current_index]
    
    # Увеличиваем индекс для следующей анкеты
    await state.update_data(current_index=current_index + 1)
    
    # Показываем анкету
    await send_animal_profile(message, animal_data, bot, show_category=(selected_category == "all"))

# Обработчик для кнопки "Следующая анкета" - продолжает поиск в выбранной категории
@router.message(F.text == "Следующая анкета")
async def next_animal(message: Message, bot: Bot, state: FSMContext):
    # Проверяем, что состояние поиска активно
    current_state = await state.get_state()
    if current_state != SearchState.selected_category.state:
        await message.answer(
            "Сначала выберите тип поиска",
            reply_markup=kb.search_main
        )
        return
    
    await show_next_animal(message, bot, state)

# Обработчик для кнопки "Начать заново" - сбрасывает индекс и начинает сначала
@router.message(F.text == "Начать заново")
async def restart_search(message: Message, bot: Bot, state: FSMContext):
    # Проверяем, что состояние поиска активно
    current_state = await state.get_state()
    if current_state != SearchState.selected_category.state:
        await message.answer(
            "Сначала выберите тип поиска",
            reply_markup=kb.search_main
        )
        return
    
    # Получаем данные из состояния
    data = await state.get_data()
    animals_list = data.get('animals_list', [])
    selected_category = data.get('selected_category', 'all')
    
    if not animals_list:
        await message.answer(
            "Нет анкет для показа.",
            reply_markup=kb.search_main
        )
        return
    
    # Сбрасываем индекс и показываем первую анкету
    await state.update_data(current_index=0)
    await show_next_animal(message, bot, state)

# Обработчик для кнопки "В главное меню" - возврат к основному функционалу
@router.message(F.text == "В главное меню")
async def back_to_main_menu(message: Message, state: FSMContext):
    # Сбрасываем состояние при возврате в главное меню
    await state.clear()
    await message.answer(
        "Возвращаемся в главное меню",
        reply_markup=kb.search
    )

# Обработчик для кнопки "Главное меню" из меню завершения просмотра
@router.message(F.text == "Главное меню")
async def back_to_main_from_complete(message: Message, state: FSMContext):
    # Сбрасываем состояние при возврате в главное меню
    await state.clear()
    await message.answer(
        "Возвращаемся в главное меню",
        reply_markup=kb.search
    )

async def send_animal_profile(message: Message, animal_data: dict, bot: Bot, show_category: bool = False):
    animal = animal_data['animal']
    user = animal_data['user']
    physical_entities = animal_data['physical_entities']
    organizations = animal_data['organizations']
    
    # Проверяем, находится ли животное в избранном у пользователя
    is_liked = await is_animal_in_favorites(message.from_user.id, animal.id)
    
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
        
        # Если есть привязанные физические лица
        if physical_entities and physical_entities[0]:
            entity = physical_entities[0]
            animal_caption += (
                f"👤 <b>Физ. лицо</b>\n"
                f"• Имя: {entity.name}\n"
                f"• Возраст: {entity.age}\n"
                f"• Телефон: {entity.phone}\n"
                f"• Email: {entity.email}\n"
            )
        
        # Если есть привязанные организации
        elif organizations and organizations[0]:
            org = organizations[0]
            animal_caption += (
                f"🏢 <b>Организация</b>\n"
                f"• Название: {org.name}\n"
                f"• Адрес: {org.address}\n"
                f"• Телефон: {org.phone}\n"
                f"• Email: {org.email}\n"
            )
        
        else:
            animal_caption += "⚠️ Контактная информация не указана\n"
        
        # Добавляем статус избранного
        if is_liked:
            animal_caption += f"\n⭐ <b>В вашем избранном</b>"
        
        # Отправляем фото животного с кнопками лайка
        if animal.telegram_file_id:
            await message.answer_photo(
                photo=animal.telegram_file_id,
                caption=animal_caption,
                parse_mode='HTML',
                reply_markup=get_like_keyboard(animal.id, is_liked)
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
                reply_markup=get_like_keyboard(animal.id, is_liked)
            )
            
    except Exception as e:
        await message.answer(
            f"Произошла ошибка при поиске: {str(e)}",
            reply_markup=kb.search_actions
        )
    
    # Отправляем отдельное сообщение с кнопками действий
    await message.answer(
        "Выберите действие:",
        reply_markup=kb.search_actions
    )

# Обработчик для кнопки "Лайк" (добавление в избранное)
# Обработчик для кнопки "Лайк" (добавление в избранное)
@router.callback_query(F.data.startswith('like_'))
async def handle_like(callback: CallbackQuery, bot: Bot, state: FSMContext):
    animal_id = int(callback.data.replace('like_', ''))
    
    print(f"DEBUG: Like clicked - animal_id: {animal_id}, user_id: {callback.from_user.id}")
    
    # Получаем пользователя
    user = await get_or_create_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        full_name=callback.from_user.full_name
    )
    
    print(f"DEBUG: User found - user_id: {user.id}")
    
    # Добавляем в избранное
    success = await add_to_favorites(user.id, animal_id)
    
    print(f"DEBUG: Add to favorites result: {success}")
    
    if success:
        # Обновляем сообщение с измененной кнопкой
        try:
            await callback.message.edit_reply_markup(
                reply_markup=get_like_keyboard(animal_id, True)
            )
            print("DEBUG: Keyboard updated successfully")
        except Exception as e:
            print(f"DEBUG: Error updating keyboard: {e}")

    else:
        await callback.answer("⚠️ Уже в избранном", show_alert=True)

# Обработчик для кнопки "Убрать лайк" (удаление из избранного)
@router.callback_query(F.data.startswith('unlike_'))
async def handle_unlike(callback: CallbackQuery, bot: Bot, state: FSMContext):
    animal_id = int(callback.data.replace('unlike_', ''))
    
    # Получаем пользователя
    user = await get_or_create_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        full_name=callback.from_user.full_name
    )
    
    # Удаляем из избранного
    success = await remove_from_favorites(user.id, animal_id)
    
    if success:
        # Обновляем сообщение с измененной кнопкой
        try:
            await callback.message.edit_reply_markup(
                reply_markup=get_like_keyboard(animal_id, False)
            )
        except:
            pass  # Если не удалось обновить кнопку, ничего страшного
        
    else:
        await callback.answer("⚠️ Не было в избранном", show_alert=True)

# Обработчик кнопки "Избранное" в главном меню
@router.message(F.text == "Избранное")
async def show_favorites(message: Message, bot: Bot):
    # Получаем пользователя из базы
    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name
    )
    
    print(f"DEBUG show_favorites: telegram_id={message.from_user.id}, db_user_id={user.id}")
    
    # Получаем все избранные животные пользователя (передаем user_id из базы)
    favorites_data = await get_user_favorites_with_owners(user.id)
    
    print(f"DEBUG: Favorites data received: {len(favorites_data)} items")
    
    if not favorites_data:
        await message.answer(
            "💔 <b>У вас пока нет избранных анкет.</b>\n\n"
            "Чтобы добавить анкету в избранное, нажмите ❤️ под понравившейся анкетой в поиске.",
            parse_mode='HTML',
            reply_markup=kb.search
        )
        return
    
    
    # Показываем все избранные анкеты
    for i, favorite_data in enumerate(favorites_data, 1):
        animal = favorite_data['animal']
        user = favorite_data['user']
        physical_entities = favorite_data['physical_entities']
        organizations = favorite_data['organizations']
        favorite_id = favorite_data['favorite_id']
        
        print(f"DEBUG: Showing favorite {i}/{len(favorites_data)} - animal_id={animal.id}")
        
        try:
            # Формируем описание животного
            animal_caption = (
                f"⭐ <b>Избранное</b> (#{i})\n\n"
                f"<b>Животное:</b>\n"
                f"• Имя: {animal.name}\n"
                f"• Категория: {animal.category}\n"
                f"• Описание: {animal.description}\n\n"
            )
            
            # Добавляем информацию о владельце
            animal_caption += f"<b>Контактная информация:</b>\n"
            
            # Если есть привязанные физические лица
            if physical_entities and physical_entities[0]:
                entity = physical_entities[0]
                animal_caption += (
                    f"👤 <b>Физ. лицо</b>\n"
                    f"• Имя: {entity.name}\n"
                    f"• Возраст: {entity.age}\n"
                    f"• Телефон: {entity.phone}\n"
                    f"• Email: {entity.email}\n"
                )
            
            # Если есть привязанные организации
            elif organizations and organizations[0]:
                org = organizations[0]
                animal_caption += (
                    f"🏢 <b>Организация</b>\n"
                    f"• Название: {org.name}\n"
                    f"• Адрес: {org.address}\n"
                    f"• Телефон: {org.phone}\n"
                    f"• Email: {org.email}\n"
                )
            
            else:
                animal_caption += "⚠️ Контактная информация не указана\n"
            
            # Отправляем фото животного с кнопкой удаления из избранного
            if animal.telegram_file_id:
                await message.answer_photo(
                    photo=animal.telegram_file_id,
                    caption=animal_caption,
                    parse_mode='HTML',
                    reply_markup=get_remove_favorite_keyboard(favorite_id)
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
                    reply_markup=get_remove_favorite_keyboard(favorite_id)
                )
        except Exception as e:
            print(f"ERROR showing favorite {i}: {e}")
            await message.answer(
                f"🐾 <b>Животное</b> (#{i})\n"
                f"Имя: {animal.name}\n"
                f"Категория: {animal.category}\n"
                f"Описание: {animal.description}\n\n"
                f"⚠️ Фото недоступно\n\n"
                f"⭐ <b>Избранное</b>",
                parse_mode='HTML',
                reply_markup=get_remove_favorite_keyboard(favorite_id)
            )
        
        await asyncio.sleep(0.5)

# Обработчик для кнопки "Удалить из избранного"
@router.callback_query(F.data.startswith('remove_favorite_'))
async def handle_remove_favorite(callback: CallbackQuery, bot: Bot):
    favorite_id = int(callback.data.replace('remove_favorite_', ''))
    
    # Получаем пользователя
    user = await get_or_create_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        full_name=callback.from_user.full_name
    )
    
    # Находим запись в избранном и удаляем ее
    async with async_session() as session:
        favorite_result = await session.execute(
            select(Favorite).where(Favorite.id == favorite_id)
        )
        favorite = favorite_result.scalar_one_or_none()
        
        if favorite and favorite.user_id == user.id:
            await session.delete(favorite)
            await session.commit()
            
            # Удаляем сообщение с анкетой
            await callback.message.delete()
            await callback.answer("🗑️ Удалено из избранного")
            
            # Отправляем подтверждение
            await callback.message.answer(
                "✅ Анкета удалена из избранного",
                reply_markup=kb.search
            )
        else:
            await callback.answer("❌ Не удалось удалить из избранного")

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

# Обработчик для кнопки удаления физического лица
@router.callback_query(F.data.startswith('delete_physical_'))
async def handle_delete_physical_entity(callback: CallbackQuery, bot: Bot):
    # Извлекаем ID физического лица из callback_data
    entity_id = int(callback.data.replace('delete_physical_', ''))
    
    # Получаем пользователя
    user = await get_or_create_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        full_name=callback.from_user.full_name
    )
    
    # Пытаемся удалить физическое лицо
    success = await delete_physical_entity(entity_id, user.id)
    
    if success:
        # Удаляем сообщение с анкетой
        await callback.message.delete()
        await callback.answer("✅ Анкета физического лица успешно удалена")
        
        # Отправляем подтверждение
        await callback.message.answer(
            "✅ Анкета физического лица была удалена",
            reply_markup=kb.search
        )
    else:
        await callback.answer("❌ Не удалось удалить анкету. Возможно, она уже была удалена.")

# Обработчик для кнопки удаления организации
@router.callback_query(F.data.startswith('delete_org_'))
async def handle_delete_organization(callback: CallbackQuery, bot: Bot):
    # Извлекаем ID организации из callback_data
    org_id = int(callback.data.replace('delete_org_', ''))
    
    # Получаем пользователя
    user = await get_or_create_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        full_name=callback.from_user.full_name
    )
    
    # Пытаемся удалить организацию
    success = await delete_organization(org_id, user.id)
    
    if success:
        # Удаляем сообщение с анкетой
        await callback.message.delete()
        await callback.answer("✅ Анкета организации успешно удалена")
        
        # Отправляем подтверждение
        await callback.message.answer(
            "✅ Анкета организации была удалена",
            reply_markup=kb.search
        )
    else:
        await callback.answer("❌ Не удалось удалить анкету. Возможно, она уже была удалена.")

# Пасхолка
@router.message(Command("alina"))
async def alinaTraktor(message: Message):
    await message.reply(text='трактор')


# Отладочная команда для проверки избранного
@router.message(Command("debug_favorites"))
async def debug_favorites(message: Message):
    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name
    )
    
    # Получаем избранное напрямую
    async with async_session() as session:
        # Проверяем избранные записи
        favorites_result = await session.execute(
            select(Favorite)
            .where(Favorite.user_id == user.id)
        )
        favorites = favorites_result.scalars().all()
        
        response = f"🔍 <b>Отладочная информация об избранном</b>\n\n"
        response += f"User ID: {user.id}\n"
        response += f"Telegram ID: {user.telegram_id}\n"
        response += f"Всего избранных записей: {len(favorites)}\n\n"
        
        for i, favorite in enumerate(favorites, 1):
            # Получаем информацию о животном
            animal_result = await session.execute(
                select(Animal).where(Animal.id == favorite.animal_id)
            )
            animal = animal_result.scalar_one_or_none()
            
            animal_name = animal.name if animal else "Не найдено"
            response += f"{i}. Favorite ID: {favorite.id}, Animal ID: {favorite.animal_id}, Animal Name: {animal_name}\n"
        
        await message.answer(response, parse_mode='HTML')
