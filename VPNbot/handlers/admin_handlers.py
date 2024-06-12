from aiogram import  Router, F
from aiogram.filters import BaseFilter
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from VPNbot.config import settings
from VPNbot.outline import client

# Фильтр, который проверяет получение сообщения от админов
class IsAdmin(BaseFilter):
    def __init__(self, admin_ids: list[int]) -> None:
        self.admin_ids = admin_ids
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in self.admin_ids


admin_handlers_router = Router()

# Этот хендлер принимает от админа запрос списка ключей
@admin_handlers_router.message(F.text=='keys', IsAdmin(settings.ADMIN_IDS))
async def admin_show_all_keys_request(message: Message, session: AsyncSession):
    keys = client.get_keys()
    for key in keys:
        await message.answer(text=f'{key}')
        print(key)

# Этот хендлер принимает от админа запрос  на удаление ключа
@admin_handlers_router.message(F.text.startswith('delete'), IsAdmin(settings.ADMIN_IDS))
async def admin_delete_key_request(message: Message, session: AsyncSession):
    text = message.text
    id = text.split()[1]
    client.delete_key(key_id=id)
    await message.answer(text=f'Удален ключ {id}')