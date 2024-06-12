from aiogram import Bot, Router, F
from aiogram.filters import BaseFilter, CommandStart, StateFilter
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from VPNbot.config import settings
from VPNbot.models import User_table
from VPNbot.outline import client
from VPNbot.states import FSMForm, FSMContext, default_state

class IsAdmin(BaseFilter):
    def __init__(self, admin_ids: list[int]) -> None:
        self.admin_ids = admin_ids
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in self.admin_ids

class AdminCallback(CallbackData, prefix="adm"):
    action: str
    user_id: int
    username: str

user_handlers_router = Router()

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
                text=button,
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
@user_handlers_router.message(CommandStart())  # noqa: E999
async def process_start_command(message: Message, state: FSMContext):  # noqa: E999
    keyboard = create_inline_kb(1, 'Подключить VPN')
    await message.answer(
        text=f"Привет, <b>{message.from_user.full_name}</b>.\n\n"
             f"Добро пожаловать в один из самых быстрых и надежных VPN на основе Outline,"
             f" который позволит тебе пользоваться интернетом без цензуры.",
        parse_mode='HTML',
        reply_markup=keyboard
    )
    await state.set_state(default_state)


# Этот хэндлер будет срабатывать на апдейт типа CallbackQuery
# с data 'big_button_1_pressed'
@user_handlers_router.callback_query(F.data == 'Подключить VPN', StateFilter(default_state))
async def process_choose_tariff(callback: CallbackQuery, state: FSMContext):
    keyboard = create_inline_kb(2, price1='1 месяц - 100 руб.', price2='3 месяца - 200 руб.')
    await callback.message.edit_text(
        text='Выберите тариф: ',
        reply_markup=keyboard
    )
    await state.set_state(FSMForm.choose_tariff)


# Этот хэндлер будет срабатывать на апдейт типа CallbackQuery
# с data 'price1'
@user_handlers_router.callback_query(F.data == 'price1', StateFilter(FSMForm.choose_tariff))
async def process_price1(callback: CallbackQuery, state: FSMContext):
    keyboard = create_inline_kb(1, ready100='Готово!', cancel='Отмена.')
    await callback.message.edit_text(
        text='Сделайте перевод на карту 2200 7001 6143 8105 сумму в размере 100 руб.\n'
             'Прикрепите скрин чека и нажмите "Готово!"',
        reply_markup=keyboard
    )
    await state.set_state(FSMForm.upload_photo)

# Этот хэндлер будет срабатывать на апдейт типа CallbackQuery
# с data 'price2'
@user_handlers_router.callback_query(F.data == 'price2', StateFilter(FSMForm.choose_tariff))
async def process_price2(callback: CallbackQuery, state: FSMContext):
    keyboard = create_inline_kb(1, ready200='Готово!', cancel='Отмена.')
    await callback.message.edit_text(
        text='Сделайте перевод на карту 2200 7001 6143 8105 сумму в размере 200 руб.\n'
             'Прикрепите скрин чека и нажмите "Готово!"',
        reply_markup=keyboard
    )
    await state.set_state(FSMForm.upload_photo)


# этот хендлер принимает фото чека и отправляет его админу
@user_handlers_router.message(F.photo, StateFilter(FSMForm.upload_photo))
async def send_photo_to_admin(message: Message, bot: Bot):
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
    text = f"""Пользователь: {message.from_user.full_name}\nID: {message.from_user.id}\nUsername: @{message.from_user.username}\nВремя: {message.date}\n"""
    await bot.send_photo(chat_id=settings.ADMIN_IDS[0], photo=message.photo[-1].file_id, caption=text, reply_markup=keyboard)
    # await bot.send_message(chat_id=settings.ADMIN_IDS[0], text=text, reply_markup=keyboard)
    await message.answer(text='Ждем проверки оплаты...')

# этот хендлер принимает фото чека и отправляет его админу
@user_handlers_router.message(F.document, StateFilter(FSMForm.upload_photo))
async def send_file_to_admin(message: Message, bot: Bot):
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
    text = f'''Пользователь: {message.from_user.full_name}\nID: {message.from_user.id}\nUsername: @{message.from_user.username}\nВремя: {message.date}\n'''

    await bot.send_document(chat_id=settings.ADMIN_IDS[0], document=message.document.file_id, caption=text, reply_markup=keyboard)
    # await bot.send_message(chat_id=settings.ADMIN_IDS[0], text=text, reply_markup=keyboard)
    await message.answer(text='Ждем проверки оплаты...')


# Этот хендлер принимает сообщение о подтверждении оплаты от юзера
@user_handlers_router.callback_query(F.data.in_({'ready100', 'ready200'}))
async def process_confirm_from_user(callback: CallbackQuery):
    await callback.message.answer(text='Админ проверяет оплату и вышлет вам ключ!')

# Этот хендлер принимает сообщеине об отмене от юзера
@user_handlers_router.callback_query(F.data == 'cancel')
async def process_cancel_from_user(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(text='Отменили ваш счет! Надеюсь на ваше возвращение к нам!'
                                       'Чтобы попробовать заново наберите команду /start.')
    await callback.message.delete()
    await state.clear()



# Этот хендлер принимает от админа сообщение о том что оплата не подтверждается
@user_handlers_router.callback_query(AdminCallback.filter(F.action=='payment_inconfirm'), IsAdmin(settings.ADMIN_IDS))
async def process_denied_from_admin(callback: CallbackQuery, callback_data: AdminCallback, bot: Bot):
    await bot.send_message(chat_id=callback_data.user_id, text='Оплата не подтвердилась. '
                                                            'Скиньте фото чека снова или обратитесь к админу @dibir10')

# Этот хендлер принимает подтверждение оплаты от админа и
# отправляет инструкцию по настройке Outline клиента
@user_handlers_router.callback_query(AdminCallback.filter(F.action == 'payment_confirm'), IsAdmin(settings.ADMIN_IDS))
async def process_confirm_from_admin(callback: CallbackQuery, callback_data: AdminCallback, bot: Bot, session: AsyncSession):
    new_key = client.create_key()
    client.rename_key(new_key.key_id, str(callback_data.user_id))
    access_url = new_key.access_url
    # access_url='какой-то ключ' # временная заглушка для ключа Outline
    await bot.send_message(chat_id=callback_data.user_id, text=F'Вот твой ключ к Outline\n(нажмите чтобы скопировать): \n')
    await bot.send_message(chat_id=callback_data.user_id, text=F'`{access_url}`', parse_mode='MarkdownV2')


    session.add(User_table(
        tg_id=callback_data.user_id,
        username=callback_data.username,
        vpn_key=access_url,
        ends_at=datetime.now() + timedelta(days=30),
    ))
    await session.commit()

    print('Админ подтвердил оплату. Запись об оплате сохранена в базе данных')


