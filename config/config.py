import asyncio
import logging
from pathlib import Path

import aiohttp
import pytz
import betterlogging as bl

from os import environ as env

import requests
from aiogram.enums import ParseMode
from dotenv import load_dotenv
from aiogram import Dispatcher, Bot

from tonsdk.contract.wallet import Wallets, WalletVersionEnum

load_dotenv()

logger = logging.getLogger(__name__)
bl.basic_colorized_config(level=logging.INFO)

INITIAL_REFERRAL_TOKENS = env['INITIAL_REFERRAL_TOKENS']
SECOND_LEVEL_REFERRAL_TOKENS = env['SECOND_LEVEL_REFERRAL_TOKENS']
BOT_API_TOKEN = env['BOT_API_TOKEN']
LINK_BOT = env['LINK_BOT']
AUTHORIZATION_TOKEN = env['AUTHORIZATION_TOKEN']
COMAND_STATISTINK = env['COMAND_STATISTINK']
MANIFEST_URL = env['MANIFEST_URL']
MNEMONICS = env['MNEMONICS'].split(",")
TIMEZONE = pytz.timezone('Europe/Moscow')

MAIN_CHANNEL_ID = env['MAIN_CHANNEL_ID']
SECOND_CHANNEL_ID = env['SECOND_CHANNEL_ID']

POSTGRES_URI = f"postgresql://{env['DATABASE_USER']}:{env['DATABASE_PASS']}@{env['DATABASE_HOST']}/{env['DATABASE_NAME']}"

bot = Bot(token=BOT_API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

keystore_dir = '/tmp/ton_keystore'
Path(keystore_dir).mkdir(parents=True, exist_ok=True)

ton_config = requests.get("https://ton.org/testnet-global.config.json").json()

mnemonics, pub_k, priv_k, wallet = Wallets.from_mnemonics(mnemonics=MNEMONICS, version=WalletVersionEnum.v3r2)
