from aiogram import Bot, Router, F
from aiogram.filters import BaseFilter, CommandStart
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from lexicon.lexicon import LEXICON
from config import settings
from models import User_table
from outline import client

class IsAdmin(BaseFilter):
    def __init__(self, admin_ids: list[int]) -> None:
        self.admin_ids = admin_ids
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in self.admin_ids

class AdminCallback(CallbackData, prefix="adm"):
    action: str
    user_id: int
    username: str

handlers_router = Router()

# Функция для генерации инлайн-клавиатур "на лету"
def create_inline_kb(width: int,
                     *args: str,
                     **kwargs: str) -> InlineKeyboardMarkup:
    # Инициализируем билдер
    kb_builder = InlineKeyboardBuilder()
    # Инициализируем список для кнопок
    buttons: list[InlineKeyboardButton] = []

    # Заполняем список кнопками из аргументов args и kwargs
    if args:
        for button in args:
            buttons.append(InlineKeyboardButton(
                text=LEXICON[button] if button in LEXICON else button,
                callback_data=button))
    if kwargs:
        for button, text in kwargs.items():
            buttons.append(InlineKeyboardButton(
                text=text,
                callback_data=button))
    # Распаковываем список с кнопками в билдер методом row c параметром width
    kb_builder.row(*buttons, width=width)
    # Возвращаем объект инлайн-клавиатуры
    return kb_builder.as_markup()

# Этот хэндлер будет срабатывать на команду "/start"
# и отправлять в чат клавиатуру с инлайн-кнопками
@handlers_router.message(CommandStart())  # noqa: E999
async def process_start_command(message: Message):  # noqa: E999
    keyboard = create_inline_kb(1, 'Подключить VPN')
    await message.answer(
        text=f"Привет, <b>{message.from_user.full_name}</b>.\n\n"
             f"Добро пожаловать в один из самых быстрых и надежных VPN на основе Outline,"
             f" который позволит тебе пользоваться интернетом без цензуры.",
        parse_mode='HTML',
        reply_markup=keyboard
    )

# Этот хэндлер будет срабатывать на апдейт типа CallbackQuery
# с data 'big_button_1_pressed'
@handlers_router.callback_query(F.data == 'Подключить VPN')
async def process_choose_tariff(callback: CallbackQuery):
    keyboard = create_inline_kb(2, price1='1 месяц - 100 руб.', price2='3 месяца - 200 руб.')
    await callback.message.answer(
        text='Выберите тариф: ',
        reply_markup=keyboard
    )


# Этот хэндлер будет срабатывать на апдейт типа CallbackQuery
# с data 'price1'
@handlers_router.callback_query(F.data == 'price1')
async def process_price1(callback: CallbackQuery):
    keyboard = create_inline_kb(1, ready100='Готово!', cancel='Отмена.')
    await callback.message.answer(
        text='Сделайте перевод на карту 2222 2222 2222 2222 сумму в размере 100 руб.\n'
             'Прикрепите скрин чека и нажмите "Готово!"',
        reply_markup=keyboard
    )
# Этот хэндлер будет срабатывать на апдейт типа CallbackQuery
# с data 'price2'
@handlers_router.callback_query(F.data == 'price2')
async def process_price2(callback: CallbackQuery):
    keyboard = create_inline_kb(1, ready300='Готово!', cancel='Отмена.')
    await callback.message.answer(
        text='Сделайте перевод на карту 2222 2222 2222 2222 сумму в размере 300 руб.\n'
             'Прикрепите скрин чека и нажмите "Готово!"',
        reply_markup=keyboard
    )

# этот хендлер принимает фото чека и отправляет его админу
@handlers_router.message(F.photo)
async def send_to_admin(message: Message, bot: Bot):
    button_1 = InlineKeyboardButton(
        text='Оплата подтверждена',
        # callback_data=f'{message.from_user.id}'
        callback_data=AdminCallback(action='payment_confirm', user_id=message.from_user.id, username=message.from_user.username).pack()
    )
    button_2 = InlineKeyboardButton(
        text='Не прошла оплата',
        callback_data=AdminCallback(action='payment_inconfirm', user_id=message.from_user.id, username=message.from_user.username).pack()
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[button_1],
                         [button_2]]
    )
    # keyboard = create_inline_kb(1, user_id='Оплата подтверждена!', payment_inconfirm='Не прошла оплата.')
    text = (f'''Пользователь: {message.from_user.full_name}\n
            ID: {message.from_user.id}\n
            Username: @{message.from_user.username}\n
            Время: {message.date}\n'''
            )
    await bot.send_photo(chat_id=settings.ADMIN_IDS[0], photo=message.photo[-1].file_id)
    await bot.send_message(chat_id=settings.ADMIN_IDS[0], text=text,
                           reply_markup=keyboard)
    await message.answer(text='Ждем проверки оплаты...')


# Этот хендлер принимает сообщение о подтверждении оплаты от юзера
@handlers_router.callback_query(F.data.in_({'ready100', 'ready300'}))
async def process_confirm_from_user(callback: CallbackQuery):
    await callback.message.answer(text='Админ проверяет оплату и вышлет вам ключ!')

# Этот хендлер принимает сообщеине об отмене от юзера
@handlers_router.callback_query(F.data == 'cancel')
async def process_cancel_from_user(callback: CallbackQuery):
    await callback.message.answer(text='Отменили ваш счет! Надеюсь на ваше возвращение к нам!'
                                       'Чтобы попробовать заново наберите команду /start.')
    await callback.message.delete()


# Этот хендлер принимает от админа сообщение о том что оплата не подтверждается
@handlers_router.callback_query(AdminCallback.filter(F.action=='payment_inconfirm'), IsAdmin(settings.ADMIN_IDS))
async def process_denied_from_admin(callback: CallbackQuery, callback_data: AdminCallback, bot: Bot):
    await bot.send_message(chat_id=callback_data.user_id, text='Оплата не подтвердилась. '
                                                            'Скиньте фото чека снова или обратитесь к админу @dibir10')

# Этот хендлер принимает подтверждение оплаты от админа и
# отправляет инструкцию по настройке Outline клиента
@handlers_router.callback_query(AdminCallback.filter(F.action == 'payment_confirm'), IsAdmin(settings.ADMIN_IDS))
async def process_confirm_from_admin(callback: CallbackQuery, callback_data: AdminCallback, bot: Bot, session: AsyncSession):
    new_key = client.create_key()
    client.rename_key(new_key.key_id, str(callback_data.user_id))
    access_url = new_key.access_url
    # access_url='какой-то ключ' # временная заглушка для ключа Outline
    await bot.send_message(chat_id=callback_data.user_id, text=F'Вот твой ключ к Outline: \n')
    await bot.send_message(chat_id=callback_data.user_id, text=F'{access_url}')


    session.add(User_table(
        tg_id=callback_data.user_id,
        username=callback_data.username,
        vpn_key=access_url,
        ends_at=datetime.now() + timedelta(days=30),
    ))
    await session.commit()

    print('Админ подтвердил оплату. Запись об оплате сохранена в базе данных')
