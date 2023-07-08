from utils import TransferState, AddMoneyState
from aiogram import types
import config


class Tbot:
    def __init__(self, db, bot, dp):
        self.db = db
        self.bot = bot
        self.dp = dp
        self.admin_mode = False

        self.dp.register_message_handler(self.start, commands=['start'])
        self.dp.register_message_handler(self.help_command, commands=['help'])
        self.dp.register_message_handler(self.balance, commands=['balance'])
        self.dp.register_message_handler(self.transfer, commands=['transfer'])
        self.dp.register_message_handler(self.add_money, commands=['add_money'])
        self.dp.register_message_handler(self.admin_on, commands=['admin_on'])
        self.dp.register_message_handler(self.admin_off, commands=['admin_off'])
        self.dp.register_message_handler(self.view_users, commands=['view_users'])
        self.dp.register_message_handler(self.view_transactions, commands=['view_transactions'])
        self.dp.register_message_handler(self.top_users, commands=['top_users'])
        self.dp.register_message_handler(self.view_user_info, commands=['view_user_info'])

    async def start(self, message: types.Message):
        user_token = self.db.get_user_token(message.from_user.username)
        if not user_token:
            user_token = self.db.add_user(message.from_user.username)
        await message.reply(
            f"Hello, {message.from_user.full_name}! This is a mini bank bot. Type /help to get the list of available commands.",
            reply_markup=self.get_main_menu_keyboard(user_token)
        )

    async def help_command(self, message: types.Message):
        help_text = """
    Available commands:
    /balance - Get your balance
    /transfer - Transfer money to another user (only available in admin mode)
    /add_money - Add money to a user's account (admin mode)
    /view_users - View the list of users (admin mode)
    /view_transactions - View the list of transactions (admin mode)
    /top_users - View the top users by money (admin mode)
    /view_user_info - View information about a user (admin mode)
    """
        await message.reply(help_text, reply_markup=self.get_main_menu_keyboard(message.from_user.username))

    async def balance(self, message: types.Message):
        balance = self.db.get_balance(message.from_user.username)
        await message.reply(f"Your balance: {balance}", reply_markup=self.get_main_menu_keyboard(message.from_user.username))

    async def transfer(self, message: types.Message):
        if not self.admin_mode:
            await message.reply("Access denied.", reply_markup=self.get_main_menu_keyboard(message.from_user.username))
            return

        await message.reply(
            "Please enter the details of the transfer in the format: /transfer from_token to_token amount",
            reply_markup=self.get_cancel_keyboard())
        await TransferState.FromToken.set()

    async def add_money(self, message: types.Message):
        if not self.admin_mode:
            await message.reply("Access denied.", reply_markup=self.get_main_menu_keyboard(message.from_user.username))
            return

        await message.reply("Please enter the details of the money addition in the format: /add_money to_token amount",
                            reply_markup=self.get_cancel_keyboard())
        await AddMoneyState.ToToken.set()

    async def admin_on(self, message: types.Message):
        if len(message.text.split()) == 2 and message.text.split()[1] == config.ADMIN_PASSWORD:
            self.admin_mode = True
            await message.reply("Admin mode activated.", reply_markup=self.get_main_menu_keyboard(message.from_user.username))
        else:
            await message.reply("Access denied.")

    async def admin_off(self, message: types.Message):
        self.admin_mode = False
        await message.reply("Admin mode deactivated.", reply_markup=self.get_main_menu_keyboard(message.from_user.username))

    async def view_users(self, message: types.Message):
        if not self.admin_mode:
            await message.reply("Access denied.", reply_markup=self.get_main_menu_keyboard(message.from_user.username))
            return

        users = self.db.sort_users("join_date")
        users_list = "List of users:\n"
        for user in users:
            users_list += f"{user['username']} - {user['join_date']}\n"
        await message.reply(users_list, reply_markup=self.get_main_menu_keyboard(message.from_user.username))

    async def view_transactions(self, message: types.Message):
        if not self.admin_mode:
            await message.reply("Access denied.", reply_markup=self.get_main_menu_keyboard(message.from_user.username))
            return

        transactions = self.db.sort_transactions("date")
        transactions_list = "List of transactions:\n"
        for transaction in transactions:
            sender = self.db.get_username(transaction["sender_token"])
            receiver = self.db.get_username(transaction["receiver_token"])
            transactions_list += f"{sender} -> {receiver}: {transaction['amount']} - {transaction['date']}\n"
        await message.reply(transactions_list, reply_markup=self.get_main_menu_keyboard(message.from_user.username))

    async def top_users(self, message: types.Message):
        if not self.admin_mode:
            await message.reply("Access denied.", reply_markup=self.get_main_menu_keyboard(message.from_user.username))
            return

        users = self.db.sort_users("transaction_count", order="DESC")
        users_list = "Top users by transaction count:\n"
        for user in users:
            users_list += f"{user['username']} - {user['transaction_count']} transactions\n"
        await message.reply(users_list, reply_markup=self.get_main_menu_keyboard(message.from_user.username))

    async def view_user_info(self, message: types.Message):
        if not self.admin_mode:
            await message.reply("Access denied.", reply_markup=self.get_main_menu_keyboard(message.from_user.username))
            return

        await message.reply("Please enter the username of the user you want to view the information for:",
                            reply_markup=self.get_cancel_keyboard())
        await AddMoneyState.ToToken.set()

    def get_main_menu_keyboard(self, username):
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = [
            types.KeyboardButton('balance'),
            types.KeyboardButton('transfer'),
        ]
        if self.admin_mode:
            buttons.append(types.KeyboardButton('add_money'))
            buttons.append(types.KeyboardButton('view_users'))
            buttons.append(types.KeyboardButton('view_transactions'))
            buttons.append(types.KeyboardButton('top_users'))
            buttons.append(types.KeyboardButton('view_user_info'))
        keyboard.add(*buttons)
        return keyboard

    def get_cancel_keyboard(self):
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_button = types.KeyboardButton('Cancel')
        keyboard.add(cancel_button)
        return keyboard