from aiogram.filters import Command, CommandStart
from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import app.key as kb
from database.db_operations import get_or_create_user, create_physical_entity, create_organization
from database.db_operations import check_user_has_data 

router = Router()

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


@router.message(F.text == "Физическое лицо")
async def nice(message: Message, state: FSMContext):
    await state.set_state(RegisterPhysicalEntity.name)
    await message.answer('Как Вас зовут?')

@router.message(F.text == "Организация")
async def nice2(message: Message, state: FSMContext):
    await state.set_state(RegisterPhysicalOrganization.organization)
    await message.answer("Введите азвание Вашей организации")

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




@router.message(Command("alina"))
async def alinaTraktor(message: Message):
    await message.reply(text='трактор')