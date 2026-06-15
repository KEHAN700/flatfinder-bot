"""Форматирование текстов: карточка объекта, описание подписки."""
from __future__ import annotations

from html import escape

from database.models import Listing, SavedSearch

DEAL_TYPE_LABELS = {"rent": "Аренда", "sale": "Покупка"}


def deal_type_label(deal_type: str) -> str:
    return DEAL_TYPE_LABELS.get(deal_type, deal_type)


def _floor_text(listing: Listing) -> str:
    if listing.floor is None:
        return ""
    if listing.total_floors:
        return f"\n🏢 Этаж: {listing.floor}/{listing.total_floors}"
    return f"\n🏢 Этаж: {listing.floor}"


def listing_caption(listing: Listing, *, full: bool = False) -> str:
    """Caption карточки объекта. full=True добавляет полное описание."""
    title = escape(listing.title)
    district = escape(listing.district)
    city = escape(listing.city)
    deal = deal_type_label(listing.deal_type)

    text = (
        f"<b>{title}</b>\n"
        f"💰 {listing.price:,} {escape(listing.currency)}".replace(",", " ")
        + f" · {deal}\n"
        f"🛏 Комнат: {listing.rooms}\n"
        f"📐 Площадь: {listing.area:g} м²\n"
        f"📍 {city}, {district}"
        f"{_floor_text(listing)}"
    )

    if full and listing.description:
        text += f"\n\n{escape(listing.description)}"
    return text


def saved_search_text(search: SavedSearch) -> str:
    """Текстовое описание подписки для списка «Мои подписки»."""
    deal = deal_type_label(search.deal_type)
    parts = [f"<b>{deal}</b> · {escape(search.city)}"]

    if search.district:
        parts.append(f"район: {escape(search.district)}")
    else:
        parts.append("район: любой")

    if search.price_min is not None or search.price_max is not None:
        lo = search.price_min if search.price_min is not None else "—"
        hi = search.price_max if search.price_max is not None else "∞"
        parts.append(f"цена: {lo}–{hi}")

    if search.rooms_min is not None or search.rooms_max is not None:
        if search.rooms_min == search.rooms_max and search.rooms_min is not None:
            parts.append(f"комнат: {search.rooms_min}")
        else:
            lo = search.rooms_min if search.rooms_min is not None else "1"
            hi = search.rooms_max if search.rooms_max is not None else "∞"
            parts.append(f"комнат: {lo}+")

    return "\n".join(["🔔 " + parts[0]] + [f"   {p}" for p in parts[1:]])
