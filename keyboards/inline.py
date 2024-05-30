import asyncio

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pytonconnect import TonConnect

from utils import load_texts


class InlineKeyboard:
    __texts = asyncio.run(load_texts())

    @classmethod
    async def start_kb(cls, is_wallet: bool) -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton(text=cls.__texts['bind_wallet'] if not is_wallet else cls.__texts['unbind_wallet'],
                                  callback_data='wallets' if not is_wallet else 'disconnect'),
             InlineKeyboardButton(text=cls.__texts['withdraw_funds'], callback_data='airdrop')],
            [InlineKeyboardButton(text=cls.__texts['payment'], callback_data='payment')]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @classmethod
    async def list_wallets(cls) -> InlineKeyboardMarkup:
        keyboard = []
        wallets_list = TonConnect.get_wallets()
        for wallet in wallets_list:
            keyboard.append([InlineKeyboardButton(text=wallet['name'], callback_data=f'connect:{wallet["name"]}')])
        keyboard.append([InlineKeyboardButton(text=cls.__texts['back'], callback_data='menu')])
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @classmethod
    async def connect_kb(cls, url: str) -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton(text=cls.__texts['connect_kb'], url=url)],
            [InlineKeyboardButton(text=cls.__texts['back'], callback_data='wallets')],
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @classmethod
    async def check_payment(cls):
        keyboard = [
            [InlineKeyboardButton(text=cls.__texts['check_payment'], callback_data='check_payment')],
            [InlineKeyboardButton(text=cls.__texts['back'], callback_data='menu')]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
