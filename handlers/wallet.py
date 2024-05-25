import asyncio
from io import BytesIO

import qrcode
from aiogram.types import CallbackQuery, BufferedInputFile
from pytonconnect.storage import IStorage
from pytonconnect import TonConnect
from pytoniq_core import Address

from config import MANIFEST_URL
from database import Database
from keyboards import InlineKeyboard
from utils import load_texts

storage = {}
texts = load_texts()


class TcStorage(IStorage):
    def __init__(self, chat_id: int):
        self.chat_id = chat_id

    def _get_key(self, key: str):
        return str(self.chat_id) + key

    async def set_item(self, key: str, value: str):
        storage[self._get_key(key)] = value

    async def get_item(self, key: str, default_value: str = None):
        return storage.get(self._get_key(key), default_value)

    async def remove_item(self, key: str):
        storage.pop(self._get_key(key))


async def get_connector(chat_id: int):
    return TonConnect(MANIFEST_URL, storage=TcStorage(chat_id))


async def connect_wallet(callback: CallbackQuery):
    global texts
    await callback.message.edit_text(text=texts['connect'], reply_markup=await InlineKeyboard.list_wallets())


async def connected_wallet(callback: CallbackQuery):
    global texts
    wallet_name = callback.data.split(':')[1]
    connector = await get_connector(callback.message.chat.id)

    wallets_list = connector.get_wallets()
    wallet = None

    for w in wallets_list:
        if w['name'] == wallet_name:
            wallet = w

    if wallet is None:
        await callback.message.edit_text(text=texts['not_found_wallet'])
        return

    generated_url = await connector.connect(wallet)
    img = qrcode.make(generated_url)
    stream = BytesIO()
    img.save(stream)
    file = BufferedInputFile(file=stream.getvalue(), filename='qrcode')

    await callback.message.delete()
    msg = await callback.message.answer_photo(photo=file,
                                              reply_markup=await InlineKeyboard.connect_kb(generated_url),
                                              caption=texts['time_connect'])
    for i in range(1, 180):
        await asyncio.sleep(1)
        if connector.connected:
            if connector.account.address:
                wallet_address = connector.account.address
                wallet_address = Address(wallet_address).to_str(is_bounceable=False)
                await Database.update_wallet(callback.message.chat.id, wallet_address, 1)

                await msg.delete()
                await callback.message.answer(text=texts['wallet_connected'].format(wallet=wallet_address))
                user = await Database.get_user(callback.message.chat.id)
                await callback.message.answer(text=texts['menu_description'].format(wallet=user[5]),
                                              reply_markup=await InlineKeyboard.start_kb(user[5] is not None),
                                              disable_web_page_preview=True)
            return
    await msg.delete()
    await callback.message.answer(text=texts['timeout_error'], reply_markup=await InlineKeyboard.list_wallets())


async def disconnect_wallet(callback: CallbackQuery):
    connector = await get_connector(callback.message.chat.id)
    await connector.restore_connection()
    await connector.disconnect()
    await Database.update_wallet(callback.message.chat.id, None, 0)
    user = await Database.get_user(callback.message.chat.id)
    await callback.message.edit_text(text=texts['wallet_disconnected'])
    await callback.message.answer(text=texts['menu_description'].format(wallet=user[5]),
                                  reply_markup=await InlineKeyboard.start_kb(user[5] is not None),
                                  disable_web_page_preview=True)
