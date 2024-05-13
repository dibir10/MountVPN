from aiogram import Dispatcher, Router, F
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery, Message
from aiogram.filters import BaseFilter

# Фильтр, который проверяет получение сообщения от админов
class IsAdmin(BaseFilter):
    def __init__(self, admin_ids: list[int]) -> None:
        self.admin_ids = admin_ids
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in self.admin_ids

class AdminCallback(CallbackData, prefix="adm"):
    action: str
    user_id: int

router = Router()
# Этот хендлер принимает от админа сообщение о том что оплата не подтверждается
@router.callback_query(AdminCallback.filter(F.action=='payment_inconfirm'), IsAdmin)
async def process_confirm_from_admin(callback: CallbackQuery, callback_data: AdminCallback):
    # await message.answer(text='Ваш ключ <ПРИМЕР КЛЮЧА>')
    await bot.send_message(chat_id=callback_data.user_id, text='Оплата не подтвердилась. '
                                                            'Скиньте фото чека снова или обратитесь к админу @dibir10')
    # await bot.send_message(chat_id=callback.data, text='Ваш ключ <ПРИМЕР КЛЮЧА>')

# Этот хендлер принимает подтверждение оплаты от админа и
# отправляет инструкцию по настройке Outline клиента
@router.callback_query(AdminCallback.filter(F.action == 'payment_confirm'), IsAdmin)
async def process_confirm_from_admin(callback: CallbackQuery, callback_data: AdminCallback):
    # await message.answer(text='Ваш ключ <ПРИМЕР КЛЮЧА>')
    new_key = client.create_key()
    client.rename_key(new_key.key_id, str(callback_data.user_id))
    access_url = new_key.access_url

    await bot.send_message(chat_id=callback_data.user_id, text=F'Вот твой ключ к Outline: ')
    await bot.send_message(chat_id=callback_data.user_id, text=F'{access_url}')