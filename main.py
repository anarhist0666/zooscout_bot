import asyncio
from aiogram.filters import Command, CommandStart
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

bot = Bot('8025131403:AAGFSmTIO5do4UXS5_kWWdsNXr7trpS3Plo')
dp = Dispatcher()

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Организация'),
            KeyboardButton(text='Физическое лицо')
        ]
    ],
    resize_keyboard=True,
    input_field_placeholder='Выберите пункт меню...'
)

catalog_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text='Лайк', callback_data='laik'),
        InlineKeyboardButton(text='Жалоба', callback_data='jaloba')
    ],
    [
        InlineKeyboardButton(text='Дальше', callback_data='dalee')
    ]
])

@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer(text='Кем вы являетесь?', reply_markup=main_keyboard)

@dp.message(F.text == "Физическое лицо")
async def physical_person_handler(message: Message):
    await message.answer('Выберите категорию', reply_markup=catalog_keyboard)

@dp.message(Command("alina"))
async def alina_traktor_handler(message: Message):
    await message.reply(text='TRACTOR')

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот выключен')