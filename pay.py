import aiohttp
import logging
from datetime import datetime
import asyncio
import aiosqlite
from config import DATABASE_NAME, AUTHORIZATION_TOKEN, TON_API_URL, BOT_API_TOKEN

logging.basicConfig(level=logging.DEBUG)


async def from_nano(value):
    return round(int(value) / 10 ** 9, 9)


async def to_nano(value):
    return int(float(value) * (10 ** 9))


def get_data():
    return datetime.now().strftime("%H:%M:%S")


async def send_message(user_id, text):
    url = f"https://api.telegram.org/bot{BOT_API_TOKEN}/sendMessage"
    keyboard = {"inline_keyboard": [[{"text": "🔙 Back", "callback_data": "Menu"}]]}
    data = {
        "chat_id": user_id,
        "text": text,
        "reply_markup": keyboard,
        "parse_mode": "HTML"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data) as response:
            await response.text()


async def check_hash(transaction_hash):
    async with aiosqlite.connect(DATABASE_NAME) as connection:
        async with connection.cursor() as cursor:
            await cursor.execute("SELECT * FROM transactions_list WHERE transaction_hash = ?", (transaction_hash,))
            row = await cursor.fetchone()
            if row is None:
                await cursor.execute("INSERT INTO transactions_list (transaction_hash) VALUES (?)", (transaction_hash,))
                await connection.commit()
                return True
            return False


# async def insert_transaction(transaction):
#     query = """
#     INSERT OR REPLACE INTO transactions (hash, logical_time, account_address, account_name, is_scam, is_wallet, transaction_success, unix_time, incoming_message_value, source_address, source_is_scam, source_is_wallet)
#     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#     """
#     params = (
#         transaction.get('hash', ''),
#         transaction.get('lt', 0),
#         transaction['account'].get('address', ''),
#         transaction['account'].get('name', ''),
#         int(transaction['account'].get('is_scam', False)),
#         int(transaction['account'].get('is_wallet', False)),
#         int(transaction.get('success', False)),
#         transaction.get('utime', 0),
#         transaction.get('in_msg', {}).get('value', 0),
#         transaction.get('in_msg', {}).get('source', {}).get('address', ''),
#         int(transaction.get('in_msg', {}).get('source', {}).get('is_scam', False)),
#         int(transaction.get('in_msg', {}).get('source', {}).get('is_wallet', False))
#     )
#     async with aiosqlite.connect(DATABASE_NAME) as db:
#         await db.execute(query, params)
#         await db.commit()

async def check_ton_pay():
    headers = {'Authorization': AUTHORIZATION_TOKEN}
    async with aiohttp.ClientSession() as session:
        async with session.get(TON_API_URL, headers=headers) as response:
            response_json = await response.json()
            if 'error' not in response_json:
                for x in response_json.get('transactions', []):
                    await process_transaction(x)
                    # await print_info_transaction_info(x)
                    # await insert_transaction(x)  # Добавляем запись в базу данных


# async def print_info_transaction_info(transaction):
#     # Базовая информация о транзакции
#     logging.info(f"Hash: {transaction.get('hash', 'N/A')}")
#     logging.info(f"Logical Time (lt): {transaction.get('lt', 'N/A')}")
#     logging.info(f"Account Address: {transaction['account'].get('address', 'N/A')}")
#     logging.info(f"Account Name: {transaction['account'].get('name', 'N/A')}")
#     logging.info(f"Is Scam: {transaction['account'].get('is_scam', 'N/A')}")
#     logging.info(f"Is Wallet: {transaction['account'].get('is_wallet', 'N/A')}")
#     logging.info(f"Transaction Success: {transaction.get('success', 'N/A')}")
#     logging.info(f"Unix Time: {transaction.get('utime', 'N/A')}")
#     in_msg = transaction.get('in_msg', {})
#     logging.info(f"Incoming Message Value: {in_msg.get('value', 'N/A')}")
#     source = in_msg.get('source', {})
#     logging.info(f"Source Address: {source.get('address', 'N/A')}")
#     logging.info(f"Source Is Scam: {source.get('is_scam', 'N/A')}")
#     logging.info(f"Source Is Wallet: {source.get('is_wallet', 'N/A')}")

async def process_transaction(transaction):
    # Обработка транзакции для обновления базы данных или отправки сообщений
    in_msg = transaction.get('in_msg', {})
    decoded_body = in_msg.get('decoded_body')
    if decoded_body and 'text' in decoded_body:
        text_com = decoded_body['text']
        value = int(in_msg.get('value', 0))
        transaction_hash = transaction.get('hash')
        if transaction_hash and await check_hash(transaction_hash) and value == 9000000:
            await send_message(text_com, "Wallet verified")


async def main():
    while True:
        logging.info(f"[{get_data()}] Запрашиваем новые транзакции")
        await check_ton_pay()
        await asyncio.sleep(2)
