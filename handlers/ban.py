from typing import Callable, Awaitable, Any
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from database.users import get_user

class BanMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:
        if isinstance(event, Message) and event.from_user:
            user = await get_user(event.from_user.id)
            if user and user.get('is_banned'):
                await event.reply("🚫 Вы заблокированы в боте.")
                return
        return await handler(event, data)
