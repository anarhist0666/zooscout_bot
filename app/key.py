import asyncio
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Основная клавиатура для выбора типа регистрации при старте бота
main_with_cancel = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Организация'),
            KeyboardButton(text='Физическое лицо')
        ],
        [KeyboardButton(text='Отмена')]
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder='Выберите пункт меню...'
)

# Основная клавиатура после регистрации - главное меню бота
search = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Поиск'),
         KeyboardButton(text='Заполнение анкеты')],
        [KeyboardButton(text='Мои анкеты'),
         KeyboardButton(text='Избранное')]  # Добавлена кнопка Избранное
    ],
    resize_keyboard=True,
    input_field_placeholder='Выберите пункт меню...'
)

# Новая клавиатура для выбора типа анкеты
fill_form_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Создание нового профиля')],
        [KeyboardButton(text='Создание анкеты животного')],
        [KeyboardButton(text='В главное меню')]
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder='Выберите тип анкеты...'
)

# Клавиатура для выбора категории животного при создании анкеты
animal_category = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Собака'),
            KeyboardButton(text='Кошка')
        ],
        [
            KeyboardButton(text='Другие животные')
        ]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

# Клавиатура для отмены текущего действия
cancel_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Отмена')]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

# Клавиатура действий после показа анкеты животного в поиске
search_actions = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Следующая анкета')],
        [KeyboardButton(text='В главное меню')]
    ],
    resize_keyboard=True,
    input_field_placeholder='Выберите действие...'
)

# Клавиатура когда все анкеты просмотрены
all_animals_viewed = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Начать заново')],
        [KeyboardButton(text='Главное меню')]
    ],
    resize_keyboard=True,
    input_field_placeholder='Выберите действие...'
)

# Главное меню поиска - выбор типа поиска животных
search_main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='📋 Просмотреть все анкеты')],
        [KeyboardButton(text='⚙️ Настроить фильтры')],
        [KeyboardButton(text='В главное меню')]
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder='Выберите тип поиска...'
)

# Клавиатура выбора категории для фильтрации
filter_category_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='🐶 Собаки'), KeyboardButton(text='🐱 Кошки')],
        [KeyboardButton(text='🐾 Другие животные')],
        [KeyboardButton(text='▶️ Пропустить')]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

# Клавиатура для города
filter_city_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='🏙️ Указать город')],
        [KeyboardButton(text='▶️ Пропустить')]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

# Клавиатура для пола
filter_gender_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='♂️ Мужской'), KeyboardButton(text='♀️ Женский')],
        [KeyboardButton(text='▶️ Пропустить')]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

# Клавиатура для возраста
filter_age_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='🐣 До 5 лет'), KeyboardButton(text='🐕 Старше 5 лет')],
        [KeyboardButton(text='▶️ Пропустить')]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

# Клавиатура для размера
filter_size_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='📏 Маленький'), KeyboardButton(text='📐 Средний')],
        [KeyboardButton(text='📏 Большой'), KeyboardButton(text='▶️ Пропустить')]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

# Клавиатура для запуска поиска после настройки фильтров
start_search_with_filters_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='🔍 Найти по фильтрам')],
        [KeyboardButton(text='↩️ Назад к фильтрам')],
        [KeyboardButton(text='В главное меню')] 
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

# Инлайн клавиатура для выбора категории животных в поиске
category_search = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='🐶 Собаки', callback_data='search_dogs')],
        [InlineKeyboardButton(text='🐱 Кошки', callback_data='search_cats')],
        [InlineKeyboardButton(text='🐾 Другие животные', callback_data='search_others')]
    ]
)

def get_like_keyboard(animal_id: int, is_liked: bool = False):
    if is_liked:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text='💔 Убрать из избранного', callback_data=f'unlike_{animal_id}')]
            ]
        )
    else:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text='❤️ Добавить в избранное', callback_data=f'like_{animal_id}')]
            ]
        )

# Функция для создания инлайн клавиатуры с кнопкой удаления из избранного
def get_remove_favorite_keyboard(favorite_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='🗑️ Удалить из избранного', callback_data=f'remove_favorite_{favorite_id}')]
        ]
    )

# Функция для создания инлайн клавиатуры с кнопкой удаления животного
def get_delete_keyboard(animal_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='🗑️ Удалить анкету', callback_data=f'delete_animal_{animal_id}')]
        ]
    )

# Функция для создания инлайн клавиатуры с кнопкой удаления физического лица
def get_delete_physical_entity_keyboard(entity_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='🗑️ Удалить анкету', callback_data=f'delete_physical_{entity_id}')]
        ]
    )

# Функция для создания инлайн клавиатуры с кнопкой удаления организации
def get_delete_organization_keyboard(org_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='🗑️ Удалить анкету', callback_data=f'delete_org_{org_id}')]
        ]
    )

# Функция для создания инлайн клавиатуры с кнопкой привязки профиля к животному
def get_attach_profile_keyboard(profile_id: int, profile_type: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='✅ Привязать анкету', callback_data=f'attach_{profile_type}_{profile_id}')]
        ]
    )

# Клавиатура для повторной регистрации (для первого пользователя)
restart_registration_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Начать регистрацию заново')]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

# Клавиатура для отмены регистрации профиля
cancel_profile_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Отмена')]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)
