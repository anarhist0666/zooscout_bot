from aiogram.filters import Command, CommandStart
from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import app.key as kb


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
    await message.answer(text='Кем Вы являетесь?', reply_markup=kb.main)

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
    await message.answer("Введите свою электронную почту")

@router.message(RegisterPhysicalOrganization.address)
async def register_mail_org(message: Message, state: FSMContext):
    await state.update_data(address=message.text)
    data = await state.get_data()
    await state.clear()
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
    await message.answer(
        f'Регистрация завершена!\n\n'
        f'Ваше имя: {data["name"]}\n'
        f'Ваш возраст: {data["age"]}\n'
        f'Номер: {data["contacts"]}\n'
        f'Почта: {data["mail"]}'
    ,reply_markup=kb.search)




@router.message(Command("alina"))
async def alinaTraktor(message: Message):
    await message.reply(text='TRACTOR')