import pymysql.cursors
import config

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
        self.create_table()

    def create_table(self):
        with self.connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bank_accounts (
                    id INT PRIMARY KEY,
                    balance FLOAT DEFAULT 0
                )
            """)
            self.connection.commit()

    def get_balance(self, user_id):
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT balance FROM bank_accounts WHERE id=%s", (user_id,))
            result = cursor.fetchone()
            return result["balance"] if result else None

    def set_balance(self, user_id, balance):
        with self.connection.cursor() as cursor:
            cursor.execute("INSERT INTO bank_accounts (id, balance) VALUES (%s, %s) ON DUPLICATE KEY UPDATE balance=%s", (user_id, balance, balance))
            self.connection.commit()

    def transfer(self, from_id, to_id, amount):
        from_balance = self.get_balance(from_id)
        to_balance = self.get_balance(to_id)

        if from_balance is None or to_balance is None:
            return False

        if from_balance < amount:
            return False

        self.set_balance(from_id, from_balance - amount)
        self.set_balance(to_id, to_balance + amount)

        return True
