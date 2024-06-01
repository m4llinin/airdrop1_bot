import asyncio
import json
from base64 import urlsafe_b64encode

from pytoniq_core import begin_cell
from pytonlib import TonlibClient
from tonsdk.contract.token.ft import JettonWallet
from tonsdk.utils import to_nano, Address

from config import ton_config, keystore_dir, wallet
from database.schemas.user import User


async def load_texts(language: str = 'ru'):
    with open('texts.json', 'r', encoding='utf-8') as f:
        texts = json.load(f)
    return texts.get(language, texts['en'])


async def transaction(user: User, amount: float, jetton_address: str = None):
    client = TonlibClient(ls_index=0, config=ton_config, keystore=keystore_dir)
    await client.init()

    body = f"From airdrop bot, your id: {user.user_id}"
    if jetton_address:
        body = JettonWallet().create_transfer_body(
            to_address=Address(user.wallet),
            jetton_amount=to_nano(amount, 'ton')
        )

    # init_query = wallet.create_init_external_message()
    # await client.raw_send_message(init_query['message'].to_boc(False))

    seqno = int((await client.raw_run_method(method='seqno', stack_data=[],
                                             address=wallet.address.to_string()))['stack'][0][1], 16)

    transfer = wallet.create_transfer_message(to_addr=jetton_address if jetton_address else wallet.address.to_string(),
                                              amount=to_nano(0.05 if jetton_address else amount, 'ton'),
                                              seqno=seqno, payload=body)
    await client.raw_send_message(transfer['message'].to_boc(False))
    await client.close()



async def get_comment_message(destination_address: str, amount: int, comment: str) -> dict:
    data = {
        'address': destination_address,
        'amount': str(amount),
        'payload': urlsafe_b64encode(
            begin_cell()
            .store_uint(0, 32)  # op code for comment message
            .store_string(comment)  # store comment
            .end_cell()  # end cell
            .to_boc()  # convert it to boc
        )
        .decode()  # encode it to urlsafe base64
    }

    return data
