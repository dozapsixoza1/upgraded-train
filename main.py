import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from middlewares.ban import BanMiddleware
from database.db import init_db
from handlers import common, profile, duels, bosses, clans, shop, transfer, leaderboard, admin

logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    dp.include_router(common.router)
    dp.include_router(profile.router)
    dp.include_router(transfer.router)
    dp.include_router(duels.router)
    dp.include_router(bosses.router)
    dp.include_router(clans.router)
    dp.include_router(shop.router)
    dp.include_router(leaderboard.router)
    dp.include_router(admin.router)

    dp.message.middleware(BanMiddleware())
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
