import asyncio
from aiogram import Bot, Dispatcher
from DB import Database
from Tbot import Tbot
import config


async def main():
    db = Database()
    bot = Bot(token=config.TOKEN)
    dp = Dispatcher(bot)
    Tbot(db, bot, dp)
    await dp.start_polling()


if __name__ == '__main__':
    asyncio.run(main())
