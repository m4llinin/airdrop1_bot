import asyncio
import time

from aiogram.fsm.context import FSMContext
from pytonconnect.exceptions import UserRejectsError
from aiogram.types import CallbackQuery, Message
from tonsdk.utils import to_nano

from aiogram.exceptions import TelegramBadRequest
from database import Database
from datetime import datetime
from config import TIMEZONE, logger, wallet, bot, MAIN_CHANNEL_ID, SECOND_CHANNEL_ID
from database.schemas.airdrop import Airdrop
from database.schemas.user import User
from handlers.wallet import get_connector
from keyboards import InlineKeyboard
from utils import load_texts, transaction, get_comment_message


async def payment(callback: CallbackQuery, texts: dict, user: User, airdrop: Airdrop, state: FSMContext):
    connector = await get_connector(callback.message.chat.id)
    connected = await connector.restore_connection()
    if not connected:
        raise ImportWarning

    transfer_fee = 0.05 if airdrop.jetton_wallet else airdrop.amount * 0.05
    cur_transaction = {
        'valid_until': int(time.time() + 15 * 60),
        'messages': [await get_comment_message(destination_address=wallet.address.to_string(),
                                               amount=to_nano(transfer_fee, 'ton'),
                                               comment='Airdrop bot')]
    }

    name = airdrop.jetton_name if airdrop.jetton_name else "TON"
    call = await callback.message.edit_text(text=texts['wait_payment'].format(fee=transfer_fee,
                                                                              amount=airdrop.amount,
                                                                              name=name),
                                            reply_markup=await InlineKeyboard.payment(user.wallet_provider))
    await state.update_data(cl=call)

    await asyncio.wait_for(connector.send_transaction(transaction=cur_transaction), 15 * 60)


async def check_participation(message: Message, user: User, airdrop: Airdrop, texts: dict):
    claimed_users = airdrop.users_got
    if claimed_users is None:
        claimed_users = []

    if not (user.user_id in claimed_users) and len(claimed_users) < airdrop.max_count_users:
        await transaction(user, airdrop.amount, airdrop.jetton_wallet)
        claimed_users.append(user.user_id)
        await Database.update_users_airdrop(airdrop.id, claimed_users)

        name = airdrop.jetton_name if airdrop.jetton_name else "TON"
        await message.edit_text(text=texts["successful_airdrop"].format(amount=airdrop.amount, name=name))
    elif user.user_id in claimed_users:
        await message.edit_text(text=texts["completed_airdrop"])
    elif len(claimed_users) >= airdrop.max_count_users:
        await message.edit_text(text=texts["failed_airdrop"])
    else:
        await message.edit_text(text=texts["no_server"])

    await message.answer(text=texts['menu_description'].format(wallet=user.wallet,
                                                               owner_wallet=wallet.address.to_string(
                                                                   True, True, True)),
                         reply_markup=await InlineKeyboard.start_kb(user.wallet is not None),
                         disable_web_page_preview=True)


async def claim_airdrop(callback: CallbackQuery, state: FSMContext):
    texts = await load_texts()

    # Проверка подписки
    try:
        main_channel_status = await bot.get_chat_member(chat_id=MAIN_CHANNEL_ID, user_id=callback.message.chat.id)
        second_channel_status = await bot.get_chat_member(chat_id=SECOND_CHANNEL_ID, user_id=callback.message.chat.id)
        if main_channel_status.status == 'left' or second_channel_status.status == 'left':
            try:
                await callback.message.edit_text(text=texts['not_subscribed'],
                                                 reply_markup=await InlineKeyboard.subscribe_kb())
            except:
                pass
            return
    except TelegramBadRequest:
        await callback.message.edit_text(text=texts['not_subscribed'],
                                         reply_markup=await InlineKeyboard.subscribe_kb())
        return

    # Проверка, чтобы был привязан кошелек
    user = await Database.get_user(callback.message.chat.id)
    airdrops = await Database.get_airdrops()
    now = datetime.now(tz=TIMEZONE).timestamp()
    for airdrop in airdrops:
        try:
            if airdrop.end_date:
                if datetime.strptime(airdrop.start_date, "%H:%M %d.%m.%Y").timestamp() <= now <= datetime.strptime(
                        airdrop.end_date, "%H:%M %d.%m.%Y").timestamp():
                    # Оплата комиссии
                    try:
                        await payment(callback=callback, texts=texts, user=user, airdrop=airdrop, state=state)
                    except asyncio.TimeoutError:
                        data = await state.get_data()
                        await data["cl"].edit_text(text=texts['timeout_airdrop'])
                        await data["cl"].answer(text=texts['menu_description'].format(wallet=user.wallet,
                                                                                      owner_wallet=wallet.address.to_string(
                                                                                          True, True,
                                                                                          True)),
                                                reply_markup=await InlineKeyboard.start_kb(
                                                    user.wallet is not None),
                                                disable_web_page_preview=True)
                        return
                    except UserRejectsError:
                        data = await state.get_data()
                        await data["cl"].edit_text(text=texts['user_rejects'])
                        await data["cl"].answer(text=texts['menu_description'].format(wallet=user.wallet,
                                                                                      owner_wallet=wallet.address.to_string(
                                                                                          True, True,
                                                                                          True)),
                                                reply_markup=await InlineKeyboard.start_kb(
                                                    user.wallet is not None),
                                                disable_web_page_preview=True)
                        return
                    except ImportWarning:
                        data = await state.get_data()
                        await data["cl"].edit_text(text=texts['wallet_not_verified'], show_alert=True)
                        await data["cl"].answer(text=texts['menu_description'].format(wallet=user.wallet,
                                                                                      owner_wallet=wallet.address.to_string(
                                                                                          True, True,
                                                                                          True)),
                                                reply_markup=await InlineKeyboard.start_kb(
                                                    user.wallet is not None),
                                                disable_web_page_preview=True)
                        return

                    data = await state.get_data()
                    # claim airdrop
                    await check_participation(data['cl'], user, airdrop, texts)
                    return
            elif datetime.strptime(airdrop.start_date, "%H:%M %d.%m.%Y").timestamp() == now:
                # Оплата комиссии
                try:
                    await payment(callback=callback, texts=texts, user=user, airdrop=airdrop, state=state)
                except asyncio.TimeoutError:
                    data = await state.get_data()
                    await data["cl"].edit_text(text=texts['timeout_airdrop'])
                    await data["cl"].answer(text=texts['menu_description'].format(wallet=user.wallet,
                                                                                  owner_wallet=wallet.address.to_string(
                                                                                      True, True,
                                                                                      True)),
                                            reply_markup=await InlineKeyboard.start_kb(
                                                user.wallet is not None),
                                            disable_web_page_preview=True)
                    return
                except UserRejectsError:
                    data = await state.get_data()
                    await data["cl"].edit_text(text=texts['user_rejects'])
                    await data["cl"].answer(text=texts['menu_description'].format(wallet=user.wallet,
                                                                                  owner_wallet=wallet.address.to_string(
                                                                                      True, True,
                                                                                      True)),
                                            reply_markup=await InlineKeyboard.start_kb(
                                                user.wallet is not None),
                                            disable_web_page_preview=True)
                    return
                except ImportWarning:
                    data = await state.get_data()
                    await data["cl"].edit_text(text=texts['wallet_not_verified'], show_alert=True)
                    await data["cl"].answer(text=texts['menu_description'].format(wallet=user.wallet,
                                                                                  owner_wallet=wallet.address.to_string(
                                                                                      True, True,
                                                                                      True)),
                                            reply_markup=await InlineKeyboard.start_kb(
                                                user.wallet is not None),
                                            disable_web_page_preview=True)
                    return

                data = await state.get_data()
                # claim airdrop
                await check_participation(data['cl'], user, airdrop, texts)
                return
        except Exception as e:
            logger.error(e)
            await callback.answer(text=texts["no_server"], show_alert=True)

    try:
        await callback.message.edit_text(text=texts['menu_description'].format(wallet=user.wallet,
                                                                               owner_wallet=wallet.address.to_string(
                                                                                   True, True,
                                                                                   True)),
                                         reply_markup=await InlineKeyboard.start_kb(user.wallet is not None),
                                         disable_web_page_preview=True)
    except:
        pass

    await callback.answer(text=texts['no_airdrop'], show_alert=True)
