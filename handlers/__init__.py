"""Регистрация всех роутеров в одном месте."""
from __future__ import annotations

from aiogram import Dispatcher

from handlers import admin, leads, search, start, subscriptions


def register_handlers(dp: Dispatcher) -> None:
    dp.include_router(start.router)
    dp.include_router(search.router)
    dp.include_router(subscriptions.router)
    dp.include_router(leads.router)
    dp.include_router(admin.router)
