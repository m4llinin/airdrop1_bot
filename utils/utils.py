import asyncio
import json

from pytonlib import TonlibClient
from tonsdk.utils import to_nano

from config import ton_config, keystore_dir, wallet
from database.schemas.user import User


async def load_texts(language: str = 'ru'):
    with open('texts.json', 'r', encoding='utf-8') as f:
        texts = json.load(f)
    return texts.get(language, texts['en'])


async def transaction(user: User, amount: float):
    client = TonlibClient(ls_index=0, config=ton_config, keystore=keystore_dir)
    await client.init()

    # init_query = wallet.create_init_external_message()
    # await client.raw_send_message(init_query['message'].to_boc(False))

    seqno = int((await client.raw_run_method(method='seqno', stack_data=[],
                                             address=wallet.address.to_string(True, True, True)))['stack'][0][1], 16)

    transfer = wallet.create_transfer_message(to_addr=user.wallet, amount=to_nano(amount, 'ton'),
                                              seqno=seqno, payload="Airdrop bot")
    await client.raw_send_message(transfer['message'].to_boc(False))
    await client.close()
