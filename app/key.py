import asyncio
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Основная клавиатура для выбора типа регистрации при старте бота
# Появляется когда пользователь впервые запускает бота
main = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Организация'),        # Кнопка для регистрации как организация
            KeyboardButton(text='Физическое лицо')     # Кнопка для регистрации как физическое лицо
        ]
    ],
    resize_keyboard=True,           # Автоматически подстраивает размер клавиатуры под экран
    one_time_keyboard=True,         # Клавиатура скрывается после нажатия на кнопку
    input_field_placeholder='Выберите пункт меню...'  # Подсказка в поле ввода
)

# Основная клавиатура после регистрации - главное меню бота
# Показывается пользователям, которые уже зарегистрированы
search = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Поиск'),                 # Кнопка для поиска животных
         KeyboardButton(text='Заполнение анкеты')],    # Кнопка для создания анкеты животного
        [KeyboardButton(text='Мои анкеты')]            # Кнопка для просмотра своих анкет
    ],
    resize_keyboard=True,
    input_field_placeholder='Выберите пункт меню...'
)

# Клавиатура для выбора категории животного при создании анкеты
animal_category = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Собака'),             # Категория "Собака"
            KeyboardButton(text='Кошка')               # Категория "Кошка"
        ],
        [
            KeyboardButton(text='Другие животные')     # Категория для остальных животных
        ]
    ],
    resize_keyboard=True,
    one_time_keyboard=True            # Скрывается после выбора категории
)

# Клавиатура для отмены текущего действия
# Используется во время заполнения форм для прерывания процесса
cancel_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Отмена')]                # Единственная кнопка "Отмена"
    ],
    resize_keyboard=True,
    one_time_keyboard=True            # Скрывается после нажатия
)

# Клавиатура действий после показа анкеты животного в поиске
# Появляется после того как пользователь увидел найденное животное
search_actions = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Следующая анкета')],     # Показать следующую анкету
        [KeyboardButton(text='В главное меню')]        # Вернуться в главное меню
    ],
    resize_keyboard=True,
    input_field_placeholder='Выберите действие...'
)

# Главное меню поиска - выбор типа поиска животных
search_main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Показывать всех')],      # Поиск без фильтрации по категориям
        [KeyboardButton(text='Выбрать категорию')],    # Поиск с выбором конкретной категории
        [KeyboardButton(text='В главное меню')]        # Возврат в основное меню
    ],
    resize_keyboard=True,
    one_time_keyboard=True,           # Скрывается после выбора типа поиска
    input_field_placeholder='Выберите тип поиска...'
)

# Инлайн клавиатура для выбора категории животных в поиске
# Отображается как кнопки под сообщением, не скрывает основную клавиатуру
category_search = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='🐶 Собаки', callback_data='search_dogs')],        # Кнопка поиска собак
        [InlineKeyboardButton(text='🐱 Кошки', callback_data='search_cats')],         # Кнопка поиска кошек
        [InlineKeyboardButton(text='🐾 Другие животные', callback_data='search_others')]  # Кнопка поиска других животных
    ]
)

# Функция для создания инлайн клавиатуры с кнопкой удаления анкеты
# Генерирует уникальную кнопку для каждого животного на основе его ID
def get_delete_keyboard(animal_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='🗑️ Удалить анкету', callback_data=f'delete_animal_{animal_id}')]
            # Создает кнопку с callback_data содержащей ID животного для идентификации
        ]
    )