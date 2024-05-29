import js2py

from aiogram.types import CallbackQuery
from database import Database
from datetime import datetime
from config import TIMEZONE
from utils import load_texts


async def airdrop_handler(callback: CallbackQuery):
    texts = await load_texts()

    user = await Database.get_user(callback.message.chat.id)
    if not user.wallet:
        await callback.answer(text=texts['no_wallet'], show_alert=True)
        return

    airdrops = await Database.get_airdrops()
    now = datetime.now(tz=TIMEZONE).strftime("%H:%M %d.%m.%Y")
    for airdrop in airdrops:
        if airdrop.end_date:
            if airdrop.start_date <= now <= airdrop.end_date:
                pass
                return
        elif airdrop.start_date == now:
            pass
            return
    await callback.answer(text=texts['no_airdrop'], show_alert=True)

