from config import logger, INITIAL_REFERRAL_TOKENS, SECOND_LEVEL_REFERRAL_TOKENS
from .db_gino import db, on_startup
from .schemas.user import User
from .schemas.airdrop import Airdrop


class Database:
    @classmethod
    async def db_init(cls):
        await on_startup()
        # await db.gino.drop_all()
        # await db.gino.create_all()
        if db:
            logger.info("Database was connected")
        else:
            logger.error("Database was not connected")
            exit(1)

    @classmethod
    async def get_user(cls, user_id: int):
        return await User.query.where(User.user_id == user_id).gino.first()

    @classmethod
    async def update_referrals(cls, user_id: int, level: int, tokens: int):
        user = await cls.get_user(user_id)
        if level == 1:
            await User.update.values(level_1=user.level_1 + 1, tokens=user.tokens + tokens).where(
                User.user_id == user_id).gino.apply()
        elif level == 2:
            await User.update.values(level_2=user.level_2 + 1, tokens=user.tokens + tokens).where(
                User.user_id == user_id).gino.apply()

        if user.referral_id and level == 1:
            await cls.update_referrals(user.referral_id, 2, SECOND_LEVEL_REFERRAL_TOKENS)

    @classmethod
    async def insert_user(cls, user_id: int, referral_id: int):
        data = await cls.get_user(user_id)
        if data is None:
            if referral_id:
                await User(user_id=user_id, referral_id=referral_id).create()
            else:
                await User(user_id=user_id).create()

            if referral_id:
                await cls.update_referrals(referral_id, 1, INITIAL_REFERRAL_TOKENS)

    @classmethod
    async def update_wallet(cls, user_id: int, wallet: str | None, wallet_verif: int):
        await User.update.values(wallet=wallet, wallet_verif=wallet_verif).where(User.user_id == user_id).gino.status()

    @classmethod
    async def get_airdrops(cls):
        return await Airdrop.query.gino.all()

    @classmethod
    async def update_users_airdrop(cls, airdrop_id: int, users: list[int]):
        await Airdrop.update.values(users_got=users).where(Airdrop.id == airdrop_id).gino.status()

    @classmethod
    async def update_balance(cls, user_id: int, amount: int | float):
        await User.update.values(balance=amount).where(User.user_id == user_id).gino.status()
