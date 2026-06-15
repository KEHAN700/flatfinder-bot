"""Inline-клавиатуры: фильтры поиска, навигация по карточкам, действия, админка.

Конвенция callback_data: "<scope>:<action>:<arg>...".
"""
from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

ANY = "any"

PRICE_PRESETS: list[tuple[str, int | None, int | None]] = [
    ("до 500", None, 500),
    ("500–1000", 500, 1000),
    ("1000–2000", 1000, 2000),
    ("2000+", 2000, None),
]


def deal_type_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🏠 Аренда", callback_data="srch:deal:rent")
    kb.button(text="🔑 Покупка", callback_data="srch:deal:sale")
    kb.adjust(2)
    return kb.as_markup()


def cities_kb(cities: list[str]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for city in cities:
        kb.button(text=city, callback_data=f"srch:city:{city}")
    kb.adjust(2)
    return kb.as_markup()


def districts_kb(districts: list[str]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for district in districts:
        kb.button(text=district, callback_data=f"srch:district:{district}")
    kb.button(text="Любой", callback_data=f"srch:district:{ANY}")
    kb.adjust(2)
    return kb.as_markup()


def price_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for label, lo, hi in PRICE_PRESETS:
        lo_s = "" if lo is None else str(lo)
        hi_s = "" if hi is None else str(hi)
        kb.button(text=label, callback_data=f"srch:price:{lo_s}-{hi_s}")
    kb.button(text="Любая", callback_data=f"srch:price:{ANY}")
    kb.button(text="✏️ Ввести вручную", callback_data="srch:price:manual")
    kb.adjust(2, 2, 1, 1)
    return kb.as_markup()


def rooms_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for label in ("1", "2", "3", "4+"):
        kb.button(text=label, callback_data=f"srch:rooms:{label}")
    kb.button(text="Любое", callback_data=f"srch:rooms:{ANY}")
    kb.adjust(4, 1)
    return kb.as_markup()


def listing_card_kb(
    *,
    listing_id: int,
    offset: int,
    total: int,
    full: bool,
) -> InlineKeyboardMarkup:
    """Кнопки под карточкой: навигация + действия."""
    kb = InlineKeyboardBuilder()

    prev_off = (offset - 1) % total
    next_off = (offset + 1) % total
    kb.button(text="◀️", callback_data=f"card:nav:{prev_off}")
    kb.button(text=f"{offset + 1} / {total}", callback_data="card:noop")
    kb.button(text="▶️", callback_data=f"card:nav:{next_off}")

    if full:
        kb.button(text="🔼 Свернуть", callback_data=f"card:less:{offset}")
    else:
        kb.button(text="📄 Подробнее", callback_data=f"card:more:{offset}")

    kb.button(text="🔔 Подписаться", callback_data="card:sub")
    kb.button(text="📩 Оставить заявку", callback_data=f"card:lead:{listing_id}")

    kb.adjust(3, 1, 1, 1)
    return kb.as_markup()


def subscription_delete_kb(search_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🗑 Удалить", callback_data=f"sub:del:{search_id}")
    return kb.as_markup()


def notification_card_kb(listing_id: int) -> InlineKeyboardMarkup:
    """Кнопки под карточкой в уведомлении (без навигации)."""
    kb = InlineKeyboardBuilder()
    kb.button(text="📩 Оставить заявку", callback_data=f"card:lead:{listing_id}")
    return kb.as_markup()


def admin_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Добавить объект", callback_data="admin:add")
    kb.button(text="📋 Заявки", callback_data="admin:leads")
    kb.button(text="📊 Статистика", callback_data="admin:stats")
    kb.adjust(1)
    return kb.as_markup()


def add_listing_deal_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🏠 Аренда", callback_data="add:deal:rent")
    kb.button(text="🔑 Покупка", callback_data="add:deal:sale")
    kb.adjust(2)
    return kb.as_markup()


def skip_kb(callback_data: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="⏭ Пропустить", callback_data=callback_data)
    return kb.as_markup()
