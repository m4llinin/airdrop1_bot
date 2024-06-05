import asyncio

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pytonconnect import TonConnect

from utils import load_texts


class InlineKeyboard:
    __texts = asyncio.run(load_texts())

    @classmethod
    async def start_kb(cls, is_wallet: bool, link: str) -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton(text=cls.__texts['invite_friends'], url=f'https://t.me/share/url?url={link}')],
            [InlineKeyboardButton(text=cls.__texts['bind_wallet'] if not is_wallet else cls.__texts['unbind_wallet'],
                                  callback_data='wallets' if not is_wallet else 'disconnect'),
             InlineKeyboardButton(text=cls.__texts['withdraw_funds'], callback_data='airdrop')],
            [InlineKeyboardButton(text=cls.__texts['refresh'], callback_data='menu')]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @classmethod
    async def list_wallets(cls) -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton(text="Wallet", callback_data=f'connect:Wallet')],
            [InlineKeyboardButton(text="Tonkeeper", callback_data=f'connect:Tonkeeper')],
            [InlineKeyboardButton(text="MyTonWallet", callback_data=f'connect:MyTonWallet')],
            [InlineKeyboardButton(text=cls.__texts['back'], callback_data='menu')]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @classmethod
    async def connect_kb(cls, url: str) -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton(text=cls.__texts['connect_kb'], url=url)],
            [InlineKeyboardButton(text=cls.__texts['back'], callback_data='wallets')],
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @classmethod
    async def payment(cls, wallet: str) -> InlineKeyboardMarkup:
        if wallet == "Wallet":
            url = "https://t.me/wallet?attach=wallet"
        elif wallet == "Tonkeeper":
            url = "https://app.tonkeeper.com"
        elif wallet == "MyTonWallet":
            url = "https://mytonwallet.app"
        else:
            url = "https://tonhub.com"

        keyboard = [
            [InlineKeyboardButton(text=cls.__texts['went_wallet'], url=url)],
            [InlineKeyboardButton(text=cls.__texts['back'], callback_data='menu')]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @classmethod
    async def subscribe_kb(cls):
        keyboard = [
            [InlineKeyboardButton(text=cls.__texts['subscribe_channel_1'], url=cls.__texts['subscribe_channel_1_url'])],
            [InlineKeyboardButton(text=cls.__texts['subscribe_channel_2'], url=cls.__texts['subscribe_channel_2_url'])],
            [InlineKeyboardButton(text=cls.__texts['subscribed_button'], callback_data='menu')]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
