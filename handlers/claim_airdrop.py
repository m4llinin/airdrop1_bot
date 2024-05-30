from aiogram.types import CallbackQuery

from database import Database
from datetime import datetime
from config import TIMEZONE, logger, wallet
from database.schemas.airdrop import Airdrop
from database.schemas.user import User
from keyboards import InlineKeyboard
from utils import load_texts


async def check_participation(callback: CallbackQuery, user: User, airdrop: Airdrop, texts: dict):
    claimed_users = airdrop.users_got
    if claimed_users is None:
        claimed_users = []

    if not (user.user_id in claimed_users) and len(claimed_users) < airdrop.max_count_users:
        await Database.update_balance(user.user_id, user.balance + airdrop.amount)
        claimed_users.append(user.user_id)
        await Database.update_users_airdrop(airdrop.id, claimed_users)

        new_user = await Database.get_user(user.user_id)
        await callback.message.edit_text(text=texts['menu_description'].format(wallet=new_user.wallet,
                                                                               owner_wallet=wallet.address.to_string(
                                                                                   True, True,
                                                                                   True),
                                                                               balance=new_user.balance),
                                         reply_markup=await InlineKeyboard.start_kb(new_user.wallet is not None),
                                         disable_web_page_preview=True)

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
