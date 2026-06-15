"""FSM State-группы для поиска, заявки и добавления объекта."""
from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class SearchSG(StatesGroup):
    """Пошаговый поиск жилья."""

    deal_type = State()
    city = State()
    district = State()
    price = State()
    price_input = State()
    rooms = State()


class LeadSG(StatesGroup):
    """Оставить заявку риелтору."""

    name = State()
    phone = State()
    message = State()


class AddListingSG(StatesGroup):
    """Админ: пошаговое добавление объекта."""

    deal_type = State()
    city = State()
    district = State()
    price = State()
    rooms = State()
    area = State()
    floor = State()
    title = State()
    description = State()
    photo_url = State()
