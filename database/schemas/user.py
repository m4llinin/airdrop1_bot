from sqlalchemy import Column, BigInteger, Integer, String, sql
from database.db_gino import TimedBaseModel


class User(TimedBaseModel):
    __tablename__ = 'users'
    user_id = Column(BigInteger, primary_key=True)
    referral_id = Column(BigInteger, default=None)
    level_1 = Column(Integer, default=0)
    level_2 = Column(Integer, default=0)
    tokens = Column(Integer, default=5000)
    wallet = Column(String, default=None)
    wallet_verif = Column(Integer, default=0)

    query: sql.select
