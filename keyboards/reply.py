"""Reply-клавиатуры (главное меню, шаринг контакта)."""
from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

BTN_SEARCH = "🔍 Найти жильё"
BTN_SUBSCRIPTIONS = "🔔 Мои подписки"
BTN_LEAD = "📩 Оставить заявку"
BTN_ABOUT = "ℹ️ О боте"


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_SEARCH), KeyboardButton(text=BTN_SUBSCRIPTIONS)],
            [KeyboardButton(text=BTN_LEAD), KeyboardButton(text=BTN_ABOUT)],
        ],
        resize_keyboard=True,
    )


def share_contact() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Поделиться контактом", request_contact=True)],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
