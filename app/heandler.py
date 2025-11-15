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
from app.key import main_with_cancel, cancel_profile_kb, restart_registration_kb
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
            '🐾 С возвращением! Рады снова вас видеть.\n\n'
            'Чем могу помочь?',
            reply_markup=kb.search
        )
    else:
        # Новый пользователь - предлагаем регистрацию с кнопкой отмены
        await message.answer(
            text='🐾 Добро пожаловать в сервис поиска домашних питомцев!\n\n'
                 'Здесь вы можете найти нового друга или помочь животному обрести любящую семью. '
                 'Для начала работы нам нужно создать ваш профиль.\n\n'
                 'Вы представляете физическое лицо или организацию?', 
            reply_markup=kb.main_with_cancel  # Используем обновленную клавиатуру
        )

@router.message(F.text == "Начать регистрацию заново")
async def restart_registration(message: Message, state: FSMContext):
    # Сбрасываем состояние
    await state.clear()
    
    # Показываем начальное сообщение с выбором типа профиля
    await message.answer(
        text='🐾 Давайте начнем регистрацию заново.\n\n'
             'Вы представляете физическое лицо или организацию?', 
        reply_markup=kb.main_with_cancel
    )

@router.message(F.text == "Отмена")
async def cancel_registration(message: Message, state: FSMContext):
    # Получаем текущее состояние
    current_state = await state.get_state()
    
    # Сбрасываем состояние
    await state.clear()
    
    # Проверяем, в каком состоянии был пользователь
    if current_state in [RegisterPhysicalEntity.name.state, 
                        RegisterPhysicalEntity.age.state,
                        RegisterPhysicalEntity.contacts.state,
                        RegisterPhysicalEntity.mail.state,
                        RegisterPhysicalOrganization.organization.state,
                        RegisterPhysicalOrganization.contacts.state,
                        RegisterPhysicalOrganization.mail.state,
                        RegisterPhysicalOrganization.address.state]:
        
        # Пользователь был в процессе регистрации профиля
        await message.answer(
            "❌ Регистрация профиля отменена.\n\n"
            "Вы можете начать заново в любое время через раздел «Заполнение анкеты».",
            reply_markup=kb.search
        )
    else:
        # Пользователь был на начальном этапе
        await message.answer(
            "❌ Регистрация отменена.\n\n"
            "Вы можете начать регистрацию в любое время через раздел «Заполнение анкеты».",
            reply_markup=kb.search
        )


# Обработчик выбора "Физическое лицо" - начало регистрации
@router.message(F.text == "Физическое лицо")
async def nice(message: Message, state: FSMContext):
    await state.set_state(RegisterPhysicalEntity.name)
    await message.answer(
        '👤 Регистрация физического лица\n\nПожалуйста, укажите ваши ФИО полностью.',
        reply_markup=kb.cancel_profile_kb  # Добавляем кнопку отмены
    )

# Обработчик выбора "Организация" - начало регистрации
@router.message(F.text == "Организация")
async def nice2(message: Message, state: FSMContext):
    await state.set_state(RegisterPhysicalOrganization.organization)
    await message.answer(
        "🏢 Регистрация организации\n\nПожалуйста, укажите официальное название вашей организации.",
        reply_markup=kb.cancel_profile_kb  # Добавляем кнопку отмены
    )

# Обработчики для пошаговой регистрации организации
@router.message(RegisterPhysicalOrganization.organization)
async def register_org(message: Message, state: FSMContext):
    if message.text == 'Отмена':
        await cancel_registration(message, state)
        return
        
    await state.update_data(organization=message.text)
    await state.set_state(RegisterPhysicalOrganization.contacts)
    await message.answer("→ Укажите ваш контактный номер телефона", reply_markup=kb.cancel_profile_kb)

@router.message(RegisterPhysicalOrganization.contacts)
async def register_contacts_org(message: Message, state: FSMContext):
    if message.text == 'Отмена':
        await cancel_registration(message, state)
        return
        
    await state.update_data(contacts=message.text)
    await state.set_state(RegisterPhysicalOrganization.mail)
    await message.answer("→ Укажите ваш адрес электронной почты", reply_markup=kb.cancel_profile_kb)

@router.message(RegisterPhysicalOrganization.mail)
async def register_mail_org(message: Message, state: FSMContext):
    if message.text == 'Отмена':
        await cancel_registration(message, state)
        return
        
    await state.update_data(mail=message.text)
    await state.set_state(RegisterPhysicalOrganization.address)
    await message.answer("→ Укажите юридический адрес организации", reply_markup=kb.cancel_profile_kb)

@router.message(RegisterPhysicalOrganization.address)
async def register_mail_org(message: Message, state: FSMContext):
    if message.text == 'Отмена':
        await cancel_registration(message, state)
        return
        
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
        '✅ Регистрация успешно завершена!\n\n'
        'Ваши данные сохранены в системе. Теперь вы можете создавать анкеты питомцев или начать поиск.',
        reply_markup=kb.search
    )

# Обработчики для пошаговой регистрации физического лица
@router.message(RegisterPhysicalEntity.name)
async def register_name(message: Message, state: FSMContext):
    if message.text == 'Отмена':
        await cancel_registration(message, state)
        return
        
    await state.update_data(name=message.text)
    await state.set_state(RegisterPhysicalEntity.age)
    await message.answer('→ Укажите ваш возраст', reply_markup=kb.cancel_profile_kb)

@router.message(RegisterPhysicalEntity.age)
async def register_age(message: Message, state: FSMContext):
    if message.text == 'Отмена':
        await cancel_registration(message, state)
        return
        
    await state.update_data(age=message.text)
    await state.set_state(RegisterPhysicalEntity.contacts)
    await message.answer('→ Укажите ваш контактный номер телефона', reply_markup=kb.cancel_profile_kb)

@router.message(RegisterPhysicalEntity.contacts)
async def register_number_with_contact(message: Message, state: FSMContext):
    if message.text == 'Отмена':
        await cancel_registration(message, state)
        return
        
    await state.update_data(contacts=message.text)
    await state.set_state(RegisterPhysicalEntity.mail)
    await message.answer('→ Укажите ваш адрес электронной почты', reply_markup=kb.cancel_profile_kb)

@router.message(RegisterPhysicalEntity.mail)
async def register_number_with_contact2(message: Message, state: FSMContext):
    if message.text == 'Отмена':
        await cancel_registration(message, state)
        return
        
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
        '✅ Регистрация успешно завершена!\n\n'
        'Ваши данные сохранены в системе. Теперь вы можете создавать анкеты питомцев или начать поиск.',
        reply_markup=kb.search
    )


# Обработчик кнопки "Заполнение анкеты" - новое меню
@router.message(F.text == "Заполнение анкеты")
async def fill_form_menu_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "📝 Управление анкетами\n\n"
        "Выберите, что вы хотите создать или настроить:",
        reply_markup=kb.fill_form_menu
    )

@router.message(F.text == "Начать регистрацию заново")
async def handle_restart_registration(message: Message, state: FSMContext):
    await restart_registration(message, state)

# Обработчик кнопки "Создание нового профиля" - регистрация физ. лица или организации
@router.message(F.text == "Создание нового профиля")
async def create_new_profile(message: Message, state: FSMContext):
    await message.answer(
        text='Вы представляете физическое лицо или организацию?', 
        reply_markup=kb.main_with_cancel  # Используем клавиатуру с кнопкой отмены
    )

# Обработчик кнопки "Создание анкеты животного"
@router.message(F.text == "Создание анкеты животного")
async def start_animal_form(message: Message, state: FSMContext):
    await state.set_state(AnimalForm.category)
    await message.answer(
        "🐕‍🦺 Создание анкеты питомца\n\n"
        "Выберите категорию животного:",
        reply_markup=kb.animal_category
    )

# Обработчики для шагов создания анкеты животного (категория, имя, описание)
@router.message(AnimalForm.category, F.text.in_(['Собака', 'Кошка', 'Другие животные']))
async def process_category(message: Message, state: FSMContext):
    await state.update_data(category=message.text)
    await state.set_state(AnimalForm.name)
    await message.answer(
        "→ Введите кличку животного:",
        reply_markup=kb.cancel_kb
    )

@router.message(AnimalForm.name)
async def process_name(message: Message, state: FSMContext):
    if message.text == 'Отмена':
        await state.clear()
        await message.answer("❌ Создание анкеты отменено", reply_markup=kb.search)
        return
        
    await state.update_data(name=message.text)
    await state.set_state(AnimalForm.description)
    await message.answer("→ Опишите питомца: укажите породу, возраст, характер, особенности здоровья и т.д.")

@router.message(AnimalForm.description)
async def process_description(message: Message, state: FSMContext):
    if message.text == 'Отмена':
        await state.clear()
        await message.answer("❌ Создание анкеты отменено", reply_markup=kb.search)
        return
        
    await state.update_data(description=message.text)
    await state.set_state(AnimalForm.photo)
    await message.answer("→ Загрузите качественное фото животного:")

# Обработчик фото животного - теперь с логикой выбора профиля
@router.message(AnimalForm.photo, F.photo)
async def process_photo(message: Message, state: FSMContext, bot: Bot):
    if message.text == 'Отмена':
        await state.clear()
        await message.answer("❌ Создание анкеты отменено", reply_markup=kb.search)
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
            caption=f"✅ Анкета питомца опубликована!\n\n"
                    f"Теперь вашего питомца увидят пользователи в поиске. Хорошего дня!",
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
        await message.answer("👥 Привязка к профилю\n\nК какому из ваших профилей следует привязать этого питомца?")
        
        # Показываем физические лица
        if physical_entities:
            for entity in physical_entities:
                await message.answer(
                    f"👤 Физ. лицо\n"
                    f"ФИО: {entity.name}\n"
                    f"Возраст: {entity.age}\n"
                    f"Телефон: {entity.phone}\n"
                    f"Email: {entity.email}",
                    reply_markup=kb.get_attach_profile_keyboard(entity.id, "physical")
                )
                await asyncio.sleep(0.3)
        
        # Показываем организации
        if organizations:
            for org in organizations:
                await message.answer(
                    f"🏢 Организация\n"
                    f"Название: {org.name}\n"
                    f"Телефон: {org.phone}\n"
                    f"Email: {org.email}\n"
                    f"Адрес: {org.address}",
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
        caption=f"✅ Анкета питомца опубликована!\n\n"
                f"Теперь вашего питомца увидят пользователи в поиске. Хорошего дня!",
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
            "📂 У вас пока нет созданных анкет.\n\n"
            "Раздел «Заполнение анкеты» позволит вам создать профиль и добавить питомцев.",
            reply_markup=kb.search
        )
        return
    
    # Отправляем физические лица с кнопками удаления
    if physical_entities:
        await message.answer("📋 Ваши профили (Физ. лица):")
        for entity in physical_entities:
            await message.answer(
                f"👤 Физ. лицо\n"
                f"ФИО: {entity.name}\n"
                f"Возраст: {entity.age}\n"
                f"Телефон: {entity.phone}\n"
                f"Email: {entity.email}\n"
                f"Создано: {entity.created_at.strftime('%d.%m.%Y %H:%M')}",
                reply_markup=kb.get_delete_physical_entity_keyboard(entity.id)
            )
        await asyncio.sleep(0.5)
    
    # Отправляем организации с кнопками удаления
    if organizations:
        await message.answer("📋 Ваши профили (Организации):")
        for org in organizations:
            await message.answer(
                f"🏢 Организация\n"
                f"Название: {org.name}\n"
                f"Телефон: {org.phone}\n"
                f"Email: {org.email}\n"
                f"Адрес: {org.address}\n"
                f"Создано: {org.created_at.strftime('%d.%m.%Y %H:%M')}",
                reply_markup=kb.get_delete_organization_keyboard(org.id)
            )
        await asyncio.sleep(0.5)
    
    # Отправляем животных с кнопками удаления
    if animals:
        await message.answer("🐾 Ваши питомцы:")
        for animal in animals:
            try:
                if animal.telegram_file_id:
                    await message.answer_photo(
                        photo=animal.telegram_file_id,
                        caption=(
                            f"🐾 Животное\n"
                            f"Категория: {animal.category}\n"
                            f"Имя: {animal.name}\n"
                            f"Описание: {animal.description}\n"
                            f"Создано: {animal.created_at.strftime('%d.%m.%Y %H:%M')}"
                        ),
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
                            f"🐾 Животное\n"
                            f"Категория: {animal.category}\n"
                            f"Имя: {animal.name}\n"
                            f"Описание: {animal.description}\n"
                            f"Создано: {animal.created_at.strftime('%d.%m.%Y %H:%M')}"
                        ),
                        reply_markup=kb.get_delete_keyboard(animal.id)
                    )
            except Exception as e:
                await message.answer(
                    f"🐾 Животное\n"
                    f"Категория: {animal.category}\n"
                    f"Имя: {animal.name}\n"
                    f"Описание: {animal.description}\n"
                    f"Создано: {animal.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                    f"⚠️ Фото недоступно",
                    reply_markup=kb.get_delete_keyboard(animal.id)
                )
            await asyncio.sleep(0.5)


# Обработчик кнопки "Поиск" - основное меню поиска
@router.message(F.text == "Поиск")
async def search_menu(message: Message, state: FSMContext):
    # Сбрасываем состояние при новом поиска
    await state.clear()
    await message.answer(
        "🔍 Расширенный поиск\n\n"
        "Вы можете просматривать все анкеты подряд или выбрать определенную категорию.",
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
        "→ Выберите интересующую вас категорию:",
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
            f"✅ Просмотр завершен!\n\n"
            f"Вы увидели все анкеты в выбранной категории.",
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
    # Проверяем, что состояние поиска активнo
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
            f"🐾 Найден питомец!\n\n"
            f"*Животное:*\n"
            f"• Имя: {animal.name}\n"
        )
        
        # Показываем категорию только если show_category=True
        if show_category:
            animal_caption += f"• Категория: {animal.category}\n"
        
        animal_caption += f"• Описание: {animal.description}\n\n"
        
        # Добавляем информацию о владельце
        animal_caption += f"*Контактная информация владельца:*\n"
        
        # Если есть привязанные физические лица
        if physical_entities and physical_entities[0]:
            entity = physical_entities[0]
            animal_caption += (
                f"👤 *Физ. лицо*\n"
                f"• ФИО: {entity.name}\n"
                f"• Возраст: {entity.age}\n"
                f"• Телефон: {entity.phone}\n"
                f"• Email: {entity.email}\n"
            )
        
        # Если есть привязанные организации
        elif organizations and organizations[0]:
            org = organizations[0]
            animal_caption += (
                f"🏢 *Организация*\n"
                f"• Название: {org.name}\n"
                f"• Адрес: {org.address}\n"
                f"• Телефон: {org.phone}\n"
                f"• Email: {org.email}\n"
            )
        
        else:
            animal_caption += "⚠️ Контактная информация не указана\n"
        
        
        # Отправляем фото животного с кнопками лайка
        if animal.telegram_file_id:
            await message.answer_photo(
                photo=animal.telegram_file_id,
                caption=animal_caption,
                parse_mode='Markdown',
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
                parse_mode='Markdown',
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
@router.callback_query(F.data.startswith('like_'))
async def handle_like(callback: CallbackQuery, bot: Bot, state: FSMContext):
    animal_id = int(callback.data.replace('like_', ''))
        
    # Получаем пользователя
    user = await get_or_create_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        full_name=callback.from_user.full_name
    )
        
    # Добавляем в избранное
    success = await add_to_favorites(user.id, animal_id)
        
    if success:
        # Обновляем сообщение с измененной кнопкой
        try:
            await callback.message.edit_reply_markup(
                reply_markup=get_like_keyboard(animal_id, True)
            )
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
        
    # Получаем все избранные животные пользователя (передаем user_id из базы)
    favorites_data = await get_user_favorites_with_owners(user.id)
    
    
    if not favorites_data:
        await message.answer(
            "💝 В избранном пока пусто.\n\n"
            "Нажимайте ❤️ на понравившихся анкетах в поиске, чтобы добавлять их сюда.",
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
                
        try:
            # Формируем описание животного
            animal_caption = (
                f"⭐ Избранное (#{i})\n\n"
                f"*Животное:*\n"
                f"• Имя: {animal.name}\n"
                f"• Категория: {animal.category}\n"
                f"• Описание: {animal.description}\n\n"
            )
            
            # Добавляем информацию о владельце
            animal_caption += f"*Контактная информация:*\n"
            
            # Если есть привязанные физические лица
            if physical_entities and physical_entities[0]:
                entity = physical_entities[0]
                animal_caption += (
                    f"👤 *Физ. лицо*\n"
                    f"• ФИО: {entity.name}\n"
                    f"• Возраст: {entity.age}\n"
                    f"• Телефон: {entity.phone}\n"
                    f"• Email: {entity.email}\n"
                )
            
            # Если есть привязанные организации
            elif organizations and organizations[0]:
                org = organizations[0]
                animal_caption += (
                    f"🏢 *Организация*\n"
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
                    parse_mode='Markdown',
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
                    parse_mode='Markdown',
                    reply_markup=get_remove_favorite_keyboard(favorite_id)
                )
        except Exception as e:
            await message.answer(
                f"🐾 Животное (#{i})\n"
                f"Имя: {animal.name}\n"
                f"Категория: {animal.category}\n"
                f"Описание: {animal.description}\n\n"
                f"⚠️ Фото недоступно\n\n"
                f"⭐ Избранное",
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

# Обработчик команды /help - объяснение структуры и навигации бота
@router.message(Command("help"))
async def help_command(message: Message):
    help_text = (
        "🆘 *Помощь по навигации в боте*\n\n"
        
        "🏠 *Главное меню:*\n"
        "• *Поиск* - найти питомцев по категориям или просмотреть всех\n"
        "• *Заполнение анкеты* - создать профиль или добавить животное\n"
        "• *Мои анкеты* - управление вашими профилями и питомцами\n"
        "• *Избранное* - сохраненные понравившиеся анкеты\n\n"
        
        "🔍 *Как пользоваться поиском:*\n"
        "1. Нажмите «Поиск» в главном меню\n"
        "2. Выберите «Показывать всех» или «Выбрать категорию»\n"
        "3. Листайте анкеты кнопкой «Следующая анкета»\n"
        "4. Нажимайте ❤️ чтобы сохранить в избранное\n\n"
        
        "📝 *Создание анкет:*\n"
        "• *Профиль* - требуется для привязки животных\n"
        "• *Животное* - фото, описание и контактные данные\n"
        "• Можно создать несколько профилей разных типов\n\n"
        
        "⭐ *Избранное:*\n"
        "• Сохраняйте понравившихся питомцев\n"
        "• Просматривайте в любое время\n"
        "• Удаляйте ненужные анкеты\n\n"
        
        "🔄 *Основные команды:*\n"
        "• /start - перезапустить бота\n"
        "• /help - показать эту справку\n\n"
        
        "🧑‍💻👩‍💻 *Администрация:*\n"
        "• @Ventor0666 - Александр\n"
        "• @alinamurad0va - Алина\n"
    )
    
    await message.answer(help_text, parse_mode='Markdown')


# Пасхалка
@router.message(Command("alina"))
async def alinaTraktor(message: Message):
    await message.reply(text='🚜 Трактор')