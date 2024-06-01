from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from database import Database
from utils import load_texts
from keyboards import InlineKeyboard

from config import bot, SECOND_CHANNEL_ID, MAIN_CHANNEL_ID, LINK


async def start(message: Message, state: FSMContext):
    texts = await load_texts()
    sticker_id = 'CAACAgIAAxkBAAEFFu1mMPGGfu97QqFKl-OtSOvgQ1xcUgACNgEAAtumCQwwUFM3OxQEiDQE'
    await message.answer_sticker(sticker=sticker_id)

    user_id = message.chat.id
    referral_id = message.text.split(' ')
    if len(referral_id) == 2:
        if int(referral_id[1]) != message.chat.id:
            referral_id = int(referral_id[1])
        else:
            referral_id = None
    else:
        referral_id = None

    # Проверка подписки
    main_channel_status = await bot.get_chat_member(chat_id=MAIN_CHANNEL_ID, user_id=message.chat.id)
    second_channel_status = await bot.get_chat_member(chat_id=SECOND_CHANNEL_ID, user_id=message.chat.id)
    if main_channel_status.status == 'left' or second_channel_status.status == 'left':
        await message.answer(text=texts['not_subscribed'],
                             reply_markup=await InlineKeyboard.subscribe_kb())
        await state.update_data(referral_id=referral_id)
        return

    await Database.insert_user(user_id, referral_id)

    user = await Database.get_user(message.chat.id)

    await message.answer(
        text=texts['menu_description'].format(link=LINK.format(message.chat.id), wallet=user.wallet,
                                              tokens=user.balance, level_1=user.level_1, level_2=user.level_2),
        reply_markup=await InlineKeyboard.start_kb(user.wallet is not None, LINK.format(message.chat.id)),
        disable_web_page_preview=True)


async def start_callback(callback: CallbackQuery, state: FSMContext):
    texts = await load_texts()
    data = await state.get_data()

    main_channel_status = await bot.get_chat_member(chat_id=MAIN_CHANNEL_ID, user_id=callback.message.chat.id)
    second_channel_status = await bot.get_chat_member(chat_id=SECOND_CHANNEL_ID, user_id=callback.message.chat.id)
    if main_channel_status.status == 'left' or second_channel_status.status == 'left':
        await callback.answer(text=texts['not_subscribed'], show_alert=True)
        return
    if 'referral_id' in data:
        await Database.insert_user(callback.message.chat.id, data['referral_id'])

    user = await Database.get_user(callback.message.chat.id)

    try:
        await callback.message.edit_text(
            text=texts['menu_description'].format(link=LINK.format(callback.message.chat.id),
                                                  wallet=user.wallet, tokens=user.balance, level_1=user.level_1,
                                                  level_2=user.level_2),
            reply_markup=await InlineKeyboard.start_kb(user.wallet is not None, LINK.format(callback.message.chat.id)),
            disable_web_page_preview=True)
    except:
        pass
