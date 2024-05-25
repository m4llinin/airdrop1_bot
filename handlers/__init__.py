__all__ = ['register_handlers']

from aiogram import F, Router
from aiogram.filters import Command

from .start import start, start_callback
from .wallet import connect_wallet, connected_wallet, disconnect_wallet


def register_handlers(router: Router):
    router.message.register(start, Command('start'))
    router.callback_query.register(start_callback, F.data == "menu")
    router.message.register(start, Command('menu'))
    router.callback_query.register(connect_wallet, F.data == 'wallets')
    router.callback_query.register(connected_wallet, lambda query: query.data.startswith('connect:'))
    router.callback_query.register(disconnect_wallet, F.data == 'disconnect')