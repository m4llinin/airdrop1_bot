from aiogram.types import Message, CallbackQuery

from database import Database
from utils import load_texts
from keyboards import InlineKeyboard


async def start(message: Message):
    texts = load_texts()
    sticker_id = 'CAACAgIAAxkBAAEFFu1mMPGGfu97QqFKl-OtSOvgQ1xcUgACNgEAAtumCQwwUFM3OxQEiDQE'

    user_id = message.chat.id
    referral_id = message.text.split(' ')
    if len(referral_id) == 2:
        if int(referral_id[1]) != message.chat.id:
            referral_id = int(referral_id[1])
        else:
            referral_id = None
    else:
        referral_id = None

    await Database.insert_user(user_id, referral_id)

    user = await Database.get_user(message.chat.id)

    await message.answer_sticker(sticker=sticker_id)
    await message.answer(text=texts['menu_description'].format(wallet=user[5]),
                         reply_markup=await InlineKeyboard.start_kb(user[5] is not None),
                         disable_web_page_preview=True)


async def start_callback(callback: CallbackQuery):
    texts = load_texts()
    user = await Database.get_user(callback.message.chat.id)
    await callback.message.edit_text(text=texts['menu_description'].format(wallet=user[5]),
                                     reply_markup=await InlineKeyboard.start_kb(user[5] is not None),
                                     disable_web_page_preview=True)
