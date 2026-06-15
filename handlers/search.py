"""FSM поиска + выдача карточек + пагинация."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InputMediaPhoto, Message

from keyboards.inline import (
    ANY,
    PRICE_PRESETS,
    cities_kb,
    deal_type_kb,
    districts_kb,
    listing_card_kb,
    price_kb,
    rooms_kb,
)
from keyboards.reply import BTN_SEARCH, main_menu
from services import subscriptions
from services.listings import (
    SearchFilters,
    get_cities,
    get_districts,
    get_listing,
    search as search_listings,
)
from states.fsm import SearchSG
from utils.formatting import listing_caption

router = Router(name="search")

ROOMS_MAP: dict[str, tuple[int | None, int | None]] = {
    "1": (1, 1),
    "2": (2, 2),
    "3": (3, 3),
    "4+": (4, None),
    ANY: (None, None),
}

NO_RESULTS_TEXT = (
    "😔 По таким фильтрам объектов не нашлось.\n"
    "Попробуйте изменить параметры — нажмите «🔍 Найти жильё» ещё раз."
)


@router.message(F.text == BTN_SEARCH)
async def start_search(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(SearchSG.deal_type)
    await message.answer("Что ищем? Выберите тип сделки:", reply_markup=deal_type_kb())


@router.callback_query(SearchSG.deal_type, F.data.startswith("srch:deal:"))
async def pick_deal_type(callback: CallbackQuery, state: FSMContext) -> None:
    deal_type = callback.data.split(":")[2]
    await state.update_data(deal_type=deal_type)

    cities = await get_cities(deal_type)
    if not cities:
        await state.clear()
        await callback.message.edit_text(NO_RESULTS_TEXT)
        await callback.answer()
        return

    await state.set_state(SearchSG.city)
    await callback.message.edit_text("Выберите город:", reply_markup=cities_kb(cities))
    await callback.answer()


@router.callback_query(SearchSG.city, F.data.startswith("srch:city:"))
async def pick_city(callback: CallbackQuery, state: FSMContext) -> None:
    city = callback.data.split(":", 2)[2]
    await state.update_data(city=city)

    data = await state.get_data()
    districts = await get_districts(data["deal_type"], city)

    await state.set_state(SearchSG.district)
    await callback.message.edit_text(
        f"Город: <b>{city}</b>\nВыберите район:",
        reply_markup=districts_kb(districts),
    )
    await callback.answer()


@router.callback_query(SearchSG.district, F.data.startswith("srch:district:"))
async def pick_district(callback: CallbackQuery, state: FSMContext) -> None:
    district = callback.data.split(":", 2)[2]
    await state.update_data(district=None if district == ANY else district)

    await state.set_state(SearchSG.price)
    await callback.message.edit_text("Выберите диапазон цены:", reply_markup=price_kb())
    await callback.answer()


@router.callback_query(SearchSG.price, F.data == "srch:price:manual")
async def price_manual_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SearchSG.price_input)
    await callback.message.edit_text(
        "Введите диапазон цены в формате <code>min-max</code> "
        "(например, <code>500-1500</code>):"
    )
    await callback.answer()


@router.callback_query(SearchSG.price, F.data.startswith("srch:price:"))
async def pick_price(callback: CallbackQuery, state: FSMContext) -> None:
    value = callback.data.split(":", 2)[2]
    if value == ANY:
        price_min, price_max = None, None
    else:
        lo_s, hi_s = value.split("-")
        price_min = int(lo_s) if lo_s else None
        price_max = int(hi_s) if hi_s else None

    await state.update_data(price_min=price_min, price_max=price_max)
    await _ask_rooms(callback.message, state, edit=True)
    await callback.answer()


@router.message(SearchSG.price_input)
async def price_manual_input(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").replace(" ", "")
    parts = raw.replace("—", "-").split("-")
    try:
        price_min = int(parts[0]) if parts[0] else None
        price_max = int(parts[1]) if len(parts) > 1 and parts[1] else None
    except (ValueError, IndexError):
        await message.answer(
            "Не понял диапазон. Введите в формате <code>min-max</code>, "
            "например <code>500-1500</code>:"
        )
        return

    await state.update_data(price_min=price_min, price_max=price_max)
    await _ask_rooms(message, state, edit=False)


async def _ask_rooms(message: Message, state: FSMContext, *, edit: bool) -> None:
    await state.set_state(SearchSG.rooms)
    text = "Сколько комнат?"
    if edit:
        await message.edit_text(text, reply_markup=rooms_kb())
    else:
        await message.answer(text, reply_markup=rooms_kb())


@router.callback_query(SearchSG.rooms, F.data.startswith("srch:rooms:"))
async def pick_rooms(callback: CallbackQuery, state: FSMContext) -> None:
    rooms_key = callback.data.split(":", 2)[2]
    rooms_min, rooms_max = ROOMS_MAP.get(rooms_key, (None, None))
    await state.update_data(rooms_min=rooms_min, rooms_max=rooms_max)

    data = await state.get_data()
    filters = SearchFilters.from_dict(data)
    results = await search_listings(filters)

    if not results:
        await callback.message.edit_text(NO_RESULTS_TEXT)
        await callback.answer()
        await callback.message.answer("Главное меню:", reply_markup=main_menu())
        return

    ids = [listing.id for listing in results]
    await state.update_data(results=ids, offset=0)
    await state.set_state(state=None)

    await callback.message.delete()
    await _send_first_card(callback.message, results[0], total=len(ids))
    await callback.answer(f"Найдено объектов: {len(ids)}")


async def _send_first_card(message: Message, listing, *, total: int) -> None:
    await message.answer_photo(
        photo=listing.photo_url,
        caption=listing_caption(listing),
        reply_markup=listing_card_kb(
            listing_id=listing.id, offset=0, total=total, full=False
        ),
    )


async def _current_listing(state: FSMContext, offset: int):
    data = await state.get_data()
    ids: list[int] = data.get("results", [])
    if not ids:
        return None, 0, data
    offset %= len(ids)
    listing = await get_listing(ids[offset])
    return listing, offset, data


@router.callback_query(F.data == "card:noop")
async def card_noop(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(F.data.startswith("card:nav:"))
async def card_navigate(callback: CallbackQuery, state: FSMContext) -> None:
    offset = int(callback.data.split(":")[2])
    listing, offset, data = await _current_listing(state, offset)
    if listing is None:
        await callback.answer("Результаты устарели, начните поиск заново.", show_alert=True)
        return

    await state.update_data(offset=offset)
    total = len(data["results"])
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=listing.photo_url, caption=listing_caption(listing)
        ),
        reply_markup=listing_card_kb(
            listing_id=listing.id, offset=offset, total=total, full=False
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("card:more:"))
async def card_more(callback: CallbackQuery, state: FSMContext) -> None:
    await _toggle_full(callback, state, full=True)


@router.callback_query(F.data.startswith("card:less:"))
async def card_less(callback: CallbackQuery, state: FSMContext) -> None:
    await _toggle_full(callback, state, full=False)


async def _toggle_full(callback: CallbackQuery, state: FSMContext, *, full: bool) -> None:
    offset = int(callback.data.split(":")[2])
    listing, offset, data = await _current_listing(state, offset)
    if listing is None:
        await callback.answer("Результаты устарели, начните поиск заново.", show_alert=True)
        return

    total = len(data["results"])
    await callback.message.edit_caption(
        caption=listing_caption(listing, full=full),
        reply_markup=listing_card_kb(
            listing_id=listing.id, offset=offset, total=total, full=full
        ),
    )
    await callback.answer()


@router.callback_query(F.data == "card:sub")
async def card_subscribe(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    if "deal_type" not in data or "city" not in data:
        await callback.answer("Фильтры не найдены, начните поиск заново.", show_alert=True)
        return

    filters = SearchFilters.from_dict(data)
    await subscriptions.create_subscription(callback.from_user.id, filters)
    await callback.answer("🔔 Подписка создана! Сообщу о новых объектах.", show_alert=True)
