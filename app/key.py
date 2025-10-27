import asyncio
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

main = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Организация'),
            KeyboardButton(text='Физическое лицо')
        ]
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder='Выберите пункт меню...'
)

search = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Поиск'),
    KeyboardButton(text='Заполнение анкеты')]],resize_keyboard=True,input_field_placeholder='Выерите пункт меню...')