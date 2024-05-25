import logging
import betterlogging as bl

from os import environ as env

from aiogram.enums import ParseMode
from dotenv import load_dotenv
from aiogram import Dispatcher, Bot

load_dotenv()

logger = logging.getLogger(__name__)
bl.basic_colorized_config(level=logging.INFO)

INITIAL_REFERRAL_TOKENS = env['INITIAL_REFERRAL_TOKENS']
SECOND_LEVEL_REFERRAL_TOKENS = env['SECOND_LEVEL_REFERRAL_TOKENS']
BOT_API_TOKEN = env['BOT_API_TOKEN']
WALLET_PAY = env['WALLET_PAY']
LINK_BOT = env['LINK_BOT']
DATABASE_PATH = env['DATABASE_PATH']
AUTHORIZATION_TOKEN = env['AUTHORIZATION_TOKEN']
TON_API_URL = env['TON_API_URL'].format(WALLET_PAY=WALLET_PAY)
COMAND_STATISTINK = env['COMAND_STATISTINK']
MANIFEST_URL = env['MANIFEST_URL']

bot = Bot(token=BOT_API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
