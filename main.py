import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import sqlite3
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, \
    ChatMemberStatus
from aiogram.dispatcher.filters import Text
import logging
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import aiosqlite
import random
import openpyxl
from openpyxl import Workbook
import os
import random
from aiogram import types
import datetime
import json
from config import INITIAL_REFERRAL_TOKENS, SECOND_LEVEL_REFERRAL_TOKENS, BOT_API_TOKEN, \
    WALLET_PAY, LINK_BOT, DATABASE_NAME, COMAND_STATISTINK

logging.basicConfig(level=logging.DEBUG)

bot = Bot(token=BOT_API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class Form(StatesGroup):
    wallet = State()


def load_texts(language):
    with open('texts.json', 'r', encoding='utf-8') as f:
        texts = json.load(f)
    return texts.get(language, texts['en'])


db = None



async def register_user(user_id, referral_id):
    async with db.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,)) as cursor:
        data = await cursor.fetchone()
        if data is None:
            query = 'INSERT INTO users (user_id, referral_id) VALUES (?, ?)' if referral_id else 'INSERT INTO users (user_id) VALUES (?)'
            params = (user_id, referral_id) if referral_id else (user_id,)
            await db.execute(query, params)
            await db.commit()
            if referral_id:
                await update_referrals(referral_id, 1, INITIAL_REFERRAL_TOKENS)


async def update_referrals(user_id, level, tokens):
    await db.execute(f'UPDATE users SET level_{level} = level_{level} + 1, tokens = tokens + ? WHERE user_id = ?',
                     (tokens, user_id))
    await db.commit()
    referral_id = await db.execute('SELECT referral_id FROM users WHERE user_id = ?', (user_id,))
    referral_id = await referral_id.fetchone()
    if referral_id and referral_id[0] and level == 1:
        await update_referrals(referral_id[0], 2, SECOND_LEVEL_REFERRAL_TOKENS)


@dp.message_handler(commands=[COMAND_STATISTINK])
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    wb = Workbook()
    ws = wb.active
    ws.title = "User Statistics"
    columns = ["User ID", "Tokens", "Level 1 Referrals", "Level 2 Referrals", "Wallet"]
    ws.append(columns)
    async with db.execute('SELECT user_id, tokens, level_1, level_2, wallet FROM users') as cursor:
        async for row in cursor:
            ws.append(row)
    filename = f"user_statistics_{random.randint(1000, 9999)}.xlsx"
    wb.save(filename)
    with open(filename, 'rb') as file:
        await bot.send_document(user_id, document=file)
    os.remove(filename)


async def send_welcome(message: types.Message):
    user_language = message.from_user.language_code[:2]
    texts = load_texts(user_language)
    sticker_id = 'CAACAgIAAxkBAAEFFu1mMPGGfu97QqFKl-OtSOvgQ1xcUgACNgEAAtumCQwwUFM3OxQEiDQE'
    await bot.send_sticker(chat_id=message.chat.id, sticker=sticker_id)
    user_id = message.from_user.id
    referral_id = message.get_args()
    await register_user(user_id, referral_id)
    main_channel_status = await bot.get_chat_member(chat_id=MAIN_CHANNEL_ID, user_id=user_id)
    if main_channel_status.status != 'left':
        second_channel_status = await bot.get_chat_member(chat_id=SECOND_CHANNEL_ID, user_id=user_id)
        if second_channel_status.status != 'left':
            await send_menu(message.chat.id, user_id, user_language)
        else:
            await prompt_for_channel_subscription(message.chat.id, user_language)
    else:
        await prompt_for_channel_subscription(message.chat.id, user_language)


async def prompt_for_channel_subscription(chat_id, user_language):
    texts = load_texts(user_language)
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text=texts['subscribe_channel_1'], url=texts['subscribe_channel_1_url']))
    keyboard.add(types.InlineKeyboardButton(text=texts['subscribe_channel_2'], url=texts['subscribe_channel_2_url']))
    keyboard.add(types.InlineKeyboardButton(text=texts['subscribed_button'], callback_data='check_subscription'))
    msd_text = texts['prompt_channel_subscription']
    await bot.send_message(chat_id, msd_text, reply_markup=keyboard, parse_mode='HTML')


async def send_menu(chat_id, user_id, user_language, message_id=None):
    texts = load_texts(user_language)
    async with db.execute('SELECT tokens, level_1, level_2, wallet FROM users WHERE user_id = ?', (user_id,)) as cursor:
        result = await cursor.fetchone()
    if result:
        tokens, level_1, level_2, wallet = result
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text=texts['invite_friends'],
                                                url=f'https://t.me/share/url?url=https://t.me/{LINK_BOT}?start={chat_id}'))
        keyboard.add(types.InlineKeyboardButton(text=texts['bind_wallet'], callback_data='wallets'),
                     types.InlineKeyboardButton(text=texts['withdraw_funds'], callback_data='Wiward'))
        keyboard.add(types.InlineKeyboardButton(text=texts['refresh'], callback_data='Menu'))
        msd_text = texts['menu_description'].format(link=f'https://t.me/{LINK_BOT}?start={chat_id}', wallet=wallet,
                                                    tokens=tokens, level_1=level_1, level_2=level_2)
        if message_id:
            await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=msd_text, reply_markup=keyboard,
                                        parse_mode='HTML', disable_web_page_preview=True)
        else:
            await bot.send_message(chat_id, msd_text, reply_markup=keyboard, parse_mode='HTML')


async def process_wallet(message: types.Message, state: FSMContext):
    wallet = message.text
    user_id = message.from_user.id
    user_language = message.from_user.language_code[:2]
    texts = load_texts(user_language)
    async with db.execute('UPDATE users SET wallet = ?, wallet_verif = 0 WHERE user_id = ?', (wallet, user_id)):
        await db.commit()
    await state.finish()
    keyboard = types.InlineKeyboardMarkup()
    ink_pay = f'ton://transfer/{WALLET_PAY}?amount=9000000&text={message.chat.id}'
    keyboard.add(types.InlineKeyboardButton(text=texts['open_wallet'], url=f'{ink_pay}'))
    keyboard.add(types.InlineKeyboardButton(text=texts['back'], callback_data='Menu'))
    msd_text = texts['payment_instruction'].format(WALLET_PAY=WALLET_PAY, comment=message.chat.id)
    await bot.send_message(user_id, msd_text, reply_markup=keyboard, parse_mode='HTML')


async def handle_callback_query(call: types.CallbackQuery):
    await bot.answer_callback_query(call.id)
    command = call.data
    user_language = call.from_user.language_code[:2]
    if command == 'Menu':
        await send_menu(call.message.chat.id, call.from_user.id, user_language, call.message.message_id)
    elif command == 'check_subscription':
        main_status = await bot.get_chat_member(chat_id=MAIN_CHANNEL_ID, user_id=call.from_user.id)
        second_status = await bot.get_chat_member(chat_id=SECOND_CHANNEL_ID, user_id=call.from_user.id)
        '''if main_status.status != 'left' and second_status.status != 'left':
            await send_menu(call.message.chat.id, call.from_user.id, user_language, call.message.message_id)
        else:
            await prompt_for_channel_subscription(call.message.chat.id, user_language)'''
        await send_menu(call.message.chat.id, call.from_user.id, user_language, call.message.message_id)

    elif command == 'wallets':
        async with db.execute('SELECT wallet, wallet_verif FROM users WHERE user_id = ?',
                              (call.from_user.id,)) as cursor:
            result = await cursor.fetchone()
        if result:
            wallet, wallet_verif = result
            texts = load_texts(user_language)
            if wallet_verif == 0:
                await bot.send_message(call.message.chat.id, texts['enter_wallet_address'])
                await Form.wallet.set()
            else:
                keyboard = types.InlineKeyboardMarkup()
                keyboard.add(types.InlineKeyboardButton(text=texts['change_wallet'], callback_data='wallets_edit'))
                keyboard.add(types.InlineKeyboardButton(text=texts['back_button'], callback_data='Menu'))
                await bot.send_message(call.message.chat.id, texts['current_wallet'].format(wallet=wallet),
                                       reply_markup=keyboard, parse_mode='HTML')

    elif command == 'wallets_edit':
        texts = load_texts(user_language)
        await bot.send_message(call.message.chat.id, texts['enter_wallet_address'])
        await Form.wallet.set()

    elif command == 'Wiward':
        async with db.execute('SELECT tokens, wallet_verif FROM users WHERE user_id = ?',
                              (call.from_user.id,)) as cursor:
            result = await cursor.fetchone()
        texts = load_texts(user_language)
        keyboard = types.InlineKeyboardMarkup()
        ink_pay = f'ton://transfer/{WALLET_PAY}?amount=100000000&text={call.message.chat.id}'
        if result:
            tokens, wallet_verif = result
            if wallet_verif != 0:
                today = datetime.date.today()
                restriction_end_date = datetime.date(2024, 7, 17)

                if today > restriction_end_date:
                    keyboard.add(types.InlineKeyboardButton(text=texts['open_wallet'], url=f'{ink_pay}'))
                    keyboard.add(types.InlineKeyboardButton(text=texts['back'], callback_data='Menu'))
                    await call.message.answer(texts['dev_message'], reply_markup=keyboard, parse_mode='HTML')
                else:
                    keyboard.add(types.InlineKeyboardButton(text=texts['back'], callback_data='Menu'))
                    await bot.send_message(call.message.chat.id, texts['access_date_announcement'], parse_mode='HTML',
                                           reply_markup=keyboard)
            else:
                keyboard.add(types.InlineKeyboardButton(text=texts['back'], callback_data='Menu'))
                await bot.send_message(call.message.chat.id, texts['wallet_not_verified'], parse_mode='HTML',
                                       reply_markup=keyboard)
