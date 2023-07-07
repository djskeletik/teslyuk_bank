from aiogram import types
import config


class Tbot:
    def __init__(self, db, bot, dp):
        self.db = db
        self.bot = bot
        self.dp = dp
        self.admin_mode = False

        self.dp.register_message_handler(self.balance, commands=['balance'])
        self.dp.register_message_handler(self.transfer, commands=['transfer'])
        self.dp.register_message_handler(self.admin_on, commands=['admin_on'])
        self.dp.register_message_handler(self.admin_off, commands=['admin_off'])

    async def balance(self, message: types.Message):
        balance = self.db.get_balance(message.from_user.id)
        await message.reply(f"Your balance: {balance}")

    async def transfer(self, message: types.Message):
        if not self.admin_mode:
            await message.reply("Access denied.")
            return

        _, to_id, amount = map(int, message.text.split())

        if self.db.transfer(message.from_user.id, to_id, amount):
            await message.reply("Transfer completed.")
        else:
            await message.reply("Transfer failed.")

    async def admin_on(self, message: types.Message):
        if len(message.text.split()) == 2 and message.text.split()[1] == config.ADMIN_PASSWORD:
            self.admin_mode = True
            await message.reply("Admin mode activated.")
        else:
            await message.reply("Access denied.")

    async def admin_off(self, message: types.Message):
        self.admin_mode = False
        await message.reply("Admin mode deactivated.")
