import asyncio
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

main = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Организация'),
KeyboardButton(text='Физическое лицо')]], 
resize_keyboard=True,
input_field_placeholder='Выберите пункт меню...')

catalog = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Лайк', 
    callback_data='laik'), 
    InlineKeyboardButton(text='Жалоба', 
    callback_data='jaloba')],
    [InlineKeyboardButton(text='Дальше', 
    callback_data='dalee')]])