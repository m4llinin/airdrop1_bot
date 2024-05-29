from aiogram.types import CallbackQuery
from tonsdk.utils import to_nano

from database import Database
from datetime import datetime
from config import TIMEZONE, ton_config, keystore_dir, wallet, logger
from database.schemas.airdrop import Airdrop
from database.schemas.user import User
from utils import load_texts

from pytonlib import TonlibClient


async def transaction(user: User, airdrop: Airdrop):
    client = TonlibClient(ls_index=0, config=ton_config, keystore=keystore_dir)
    await client.init()

    # init_query = wallet.create_init_external_message()
    # await client.raw_send_message(init_query['message'].to_boc(False))

    seqno = int((await client.raw_run_method(method='seqno', stack_data=[],
                                             address=wallet.address.to_string(True, True, True)))['stack'][0][1], 16)

    transfer = wallet.create_transfer_message(to_addr=user.wallet, amount=to_nano(airdrop.amount, 'ton'),
                                              seqno=seqno, payload="Airdrop bot")
    await client.raw_send_message(transfer['message'].to_boc(False))
    await client.close()


async def check_participation(callback: CallbackQuery, user: User, airdrop: Airdrop, texts: dict):
    claimed_users = airdrop.users_got
    if claimed_users is None:
        claimed_users = []

    if not (user.user_id in claimed_users) and len(claimed_users) < airdrop.max_count_users:
        await transaction(user, airdrop)
        claimed_users.append(user.user_id)
        await Database.update_users_airdrop(airdrop.id, claimed_users)
        await callback.answer(text=texts["successful_airdrop"].format(amount=airdrop.amount), show_alert=True)
        return
    elif user.user_id in claimed_users:
        await callback.answer(text=texts["completed_airdrop"], show_alert=True)
    elif len(claimed_users) >= airdrop.max_count_users:
        await callback.answer(text=texts["failed_airdrop"], show_alert=True)
    else:
        await callback.answer(text=texts["no_server"], show_alert=True)


async def claim_airdrop(callback: CallbackQuery):
    texts = await load_texts()

    user = await Database.get_user(callback.message.chat.id)
    if not user.wallet:
        await callback.answer(text=texts['no_wallet'], show_alert=True)
        return

    airdrops = await Database.get_airdrops()
    now = datetime.now(tz=TIMEZONE).strftime("%H:%M %d.%m.%Y")
    for airdrop in airdrops:
        try:
            if airdrop.end_date:
                if airdrop.start_date <= now <= airdrop.end_date:
                    await check_participation(callback, user, airdrop, texts)
                    return
            elif airdrop.start_date == now:
                await check_participation(callback, user, airdrop, texts)
                return
        except Exception as e:
            logger.error(e)
            await callback.answer(text=texts["no_server"], show_alert=True)
    await callback.answer(text=texts['no_airdrop'], show_alert=True)
