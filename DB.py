import pymysql.cursors
import config
from datetime import datetime
import secrets


class Database:
    def __init__(self):
        self.connection = pymysql.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            db=config.DATABASE,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        self.create_tables()

    def create_tables(self):
        with self.connection.cursor() as cursor:
            # Transactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    token VARCHAR(255) UNIQUE,
                    date DATETIME,
                    sender_token VARCHAR(255),
                    receiver_token VARCHAR(255),
                    amount FLOAT
                )
            """)

            # Bank accounts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bank_accounts (
                    token VARCHAR(255) PRIMARY KEY,
                    username VARCHAR(255),
                    join_date DATETIME,
                    transaction_count INT DEFAULT 0,
                    last_transaction_date DATETIME
                )
            """)
            self.connection.commit()

    def get_balance(self, user_token):
        with self.connection.cursor() as cursor:
            cursor.execute("""
                SELECT CASE WHEN sender_token = %s THEN -amount ELSE amount END AS amount 
                FROM transactions 
                WHERE sender_token = %s OR receiver_token = %s
            """, (user_token, user_token, user_token))
            transactions = cursor.fetchall()
            balance = sum(transaction["amount"] for transaction in transactions)
            return balance

    def get_user_token(self, username):
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT token FROM bank_accounts WHERE username=%s", (username,))
            result = cursor.fetchone()
            return result["token"] if result else None

    def get_transaction_token(self, sender_token, receiver_token, amount):
        token = secrets.token_hex(16)
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT token FROM transactions WHERE token=%s", (token,))
            result = cursor.fetchone()
            if result:
                return self.get_transaction_token(sender_token, receiver_token, amount)
            return token

    def transaction(self, from_token, to_token, amount):
        from_username = self.get_username(from_token)
        to_username = self.get_username(to_token)

        if not from_username or not to_username:
            return False

        # For transfer operation we need to check if sender has enough balance
        if from_username != "admin":
            from_balance = self.get_balance(from_token)
            if from_balance < amount:
                return False

        # Create a new transaction
        transaction_token = self.get_transaction_token(from_token, to_token, amount)
        with self.connection.cursor() as cursor:
            cursor.execute("INSERT INTO transactions (token, date, sender_token, receiver_token, amount) VALUES (%s, %s, %s, %s, %s)",
                           (transaction_token, datetime.now(), from_token, to_token, amount))
            self.connection.commit()

        # Update transaction info in bank accounts table
        with self.connection.cursor() as cursor:
            # Increase transaction_count and update last_transaction_date for both users
            for user_token in [from_token, to_token]:
                cursor.execute("""
                    UPDATE bank_accounts
                    SET transaction_count = transaction_count + 1,
                        last_transaction_date = %s
                    WHERE token = %s
                """, (datetime.now(), user_token))
            self.connection.commit()

        return True

    def get_username(self, user_token):
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT username FROM bank_accounts WHERE token=%s", (user_token,))
            result = cursor.fetchone()
            return result["username"] if result else None

    def add_user(self, username):
        user_token = secrets.token_hex(16)
        with self.connection.cursor() as cursor:
            cursor.execute("INSERT INTO bank_accounts (token, username, join_date) VALUES (%s, %s, %s)",
                           (user_token, username, datetime.now()))
            self.connection.commit()
        return user_token

    def find_user(self, **kwargs):
        if not kwargs:
            raise ValueError("No search parameters provided.")

        query = "SELECT * FROM bank_accounts WHERE "
        params = []
        for key, value in kwargs.items():
            query += f"{key}=%s AND "
            params.append(value)

        # Remove last ' AND '
        query = query[:-5]

        with self.connection.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def sort_users(self, by, order="ASC"):
        if by not in {"transaction_count", "last_transaction_date", "join_date"}:
            raise ValueError(f"Cannot sort by '{by}'")

        with self.connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM bank_accounts ORDER BY {by} {order}")
            return cursor.fetchall()