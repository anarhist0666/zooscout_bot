from aiogram.filters import Command, CommandStart
from aiogram import F, Router
from aiogram.types import Message
import app.key as kb


router = Router()

@router.message(Command('start'))
async def st(message: Message):
    await message.answer(text='Кем вы являетесь?', reply_markup=kb.main)

@router.message(F.text == "Физическое лицо")
async def nice(message: Message):
    await message.answer('Выберите категорию', reply_markup=kb.catalog)

@router.message(Command("alina"))
async def alinaTraktor(message: Message):
    await message.reply(text='TRACTOR')