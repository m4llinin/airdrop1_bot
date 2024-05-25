import aiosqlite
from config import DATABASE_PATH, logger, INITIAL_REFERRAL_TOKENS, SECOND_LEVEL_REFERRAL_TOKENS


class Database:
    db = None

    @classmethod
    async def db_init(cls):
        cls.db = await aiosqlite.connect(DATABASE_PATH)

        if cls.db:
            logger.info("Database was connected")
        else:
            logger.error("Database was not connected")

        await cls.db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                referral_id INTEGER,
                level_1 INTEGER DEFAULT 0,
                level_2 INTEGER DEFAULT 0,
                tokens INTEGER DEFAULT 5000,
                wallet TEXT,
                wallet_verif INTEGER DEFAULT 0
            )
        ''')
        await cls.db.execute('''
            CREATE TABLE IF NOT EXISTS transactions_list (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_hash TEXT UNIQUE
            )
        ''')
        await cls.db.commit()

    @classmethod
    async def get_user(cls, user_id: int):
        async with await cls.db.execute("SELECT * FROM users WHERE user_id=?", (user_id,)) as cursor:
            return await cursor.fetchone()

    @classmethod
    async def update_referrals(cls, user_id: int, level: int, tokens: int):
        await cls.db.execute(
            f'UPDATE users SET level_{level} = level_{level} + 1, tokens = tokens + ? WHERE user_id = ?',
            (tokens, user_id))
        await cls.db.commit()

        referral_id = await cls.db.execute('SELECT referral_id FROM users WHERE user_id = ?', (user_id,))
        referral_id = await referral_id.fetchone()
        if referral_id and referral_id[0] and level == 1:
            await cls.update_referrals(referral_id[0], 2, SECOND_LEVEL_REFERRAL_TOKENS)

    @classmethod
    async def insert_user(cls, user_id: int, referral_id: int):
        async with await cls.db.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,)) as cursor:
            data = await cursor.fetchone()
            if data is None:
                query = 'INSERT INTO users (user_id, referral_id) VALUES (?, ?)' if referral_id else 'INSERT INTO users (user_id) VALUES (?)'
                params = (user_id, referral_id) if referral_id else (user_id,)
                await cls.db.execute(query, params)
                await cls.db.commit()
                if referral_id:
                    await cls.update_referrals(referral_id, 1, INITIAL_REFERRAL_TOKENS)

    @classmethod
    async def update_wallet(cls, user_id: int, wallet: str | None, wallet_verif: int):
        await cls.db.execute("UPDATE users SET wallet = ?, wallet_verif=? WHERE user_id = ?",
                             (wallet, wallet_verif, user_id))
        await cls.db.commit()
