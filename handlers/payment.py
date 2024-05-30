from aiogram.types import CallbackQuery
from pytonlib import TonlibClient

from config import ton_config, keystore_dir, wallet
from database import Database
from utils import load_texts, transaction
from keyboards import InlineKeyboard

from tonsdk.utils import from_nano


async def payment(callback: CallbackQuery):
    texts = await load_texts()
    user = await Database.get_user(callback.message.chat.id)
    transfer_fee = user.balance * 0.005
    await callback.message.edit_text(text=texts['wait_payment'].format(fee=transfer_fee,
                                                                       owner_wallet=wallet.address.to_string(True, True,
                                                                                                             True)),
                                     reply_markup=await InlineKeyboard.check_payment())


async def check_payment(callback: CallbackQuery):
    texts = await load_texts()
    user = await Database.get_user(callback.message.chat.id)

    client = TonlibClient(ls_index=0, config=ton_config, keystore=keystore_dir)
    await client.init()

    last_transaction = await client.get_transactions(account=user.wallet, limit=1)
    await client.close()

    if last_transaction:
        last_transaction = last_transaction[0]['in_msg']
        if last_transaction['source'] == user.wallet and \
                last_transaction['destination'] == wallet.address.to_string(True, True, True) and \
                from_nano(int(last_transaction['value']), 'ton') == user.balance * 0.005:
            await transaction(user, user.balance)
            await Database.update_balance(user.user_id, 0)
            await callback.message.edit_text(text=texts['menu_description'].format(wallet=user.wallet,
                                                                                   owner_wallet=wallet.address.to_string(
                                                                                       True, True, True),
                                                                                   balance=user.balance),
                                             reply_markup=await InlineKeyboard.start_kb(user.wallet is not None),
                                             disable_web_page_preview=True)
            await callback.answer(text=texts['successful_payment'], show_alert=True)
        else:
            await callback.answer(text=texts['bad_payment'], show_alert=True)
    else:
        await callback.answer(text=texts['bad_payment'], show_alert=True)
