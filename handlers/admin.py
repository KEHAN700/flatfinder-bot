"""Админка: /admin, /add_listing, /leads, /stats. Доступ только для ADMIN_IDS."""
from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.filters import BaseFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import settings
from keyboards.inline import add_listing_deal_kb, admin_menu_kb
from services import leads
from services.listings import add_listing, get_stats
from services.notifications import run_notifications
from states.fsm import AddListingSG
from utils.formatting import deal_type_label

router = Router(name="admin")

SKIP_TOKENS = {"-", "нет", "пропустить", "skip"}


class IsAdmin(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user = event.from_user
        return user is not None and settings.is_admin(user.id)


router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


def _is_skip(text: str | None) -> bool:
    return (text or "").strip().lower() in SKIP_TOKENS


@router.message(Command("admin"))
async def admin_menu(message: Message) -> None:
    await message.answer("🛠 <b>Админ-меню</b>", reply_markup=admin_menu_kb())


@router.message(Command("stats"))
@router.callback_query(F.data == "admin:stats")
async def show_stats(event: Message | CallbackQuery) -> None:
    stats = await get_stats()
    text = (
        "📊 <b>Статистика</b>\n"
        f"🏠 Объектов: {stats['listings']}\n"
        f"👥 Пользователей: {stats['users']}\n"
        f"🔔 Подписок: {stats['searches']}\n"
        f"📩 Заявок: {stats['leads']}"
    )
    message = event.message if isinstance(event, CallbackQuery) else event
    await message.answer(text)
    if isinstance(event, CallbackQuery):
        await event.answer()


@router.message(Command("leads"))
@router.callback_query(F.data == "admin:leads")
async def show_leads(event: Message | CallbackQuery) -> None:
    items = await leads.recent_leads(limit=10)
    message = event.message if isinstance(event, CallbackQuery) else event

    if not items:
        await message.answer("Заявок пока нет.")
    else:
        lines = ["📋 <b>Последние заявки</b>\n"]
        for lead in items:
            obj = f" · объект #{lead.listing_id}" if lead.listing_id else ""
            lines.append(
                f"#{lead.id} [{lead.status}] {lead.name} — "
                f"{lead.phone or '—'}{obj}"
            )
        await message.answer("\n".join(lines))

    if isinstance(event, CallbackQuery):
        await event.answer()


@router.message(Command("add_listing"))
@router.callback_query(F.data == "admin:add")
async def add_start(event: Message | CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(AddListingSG.deal_type)
    message = event.message if isinstance(event, CallbackQuery) else event
    await message.answer("➕ Тип сделки нового объекта:", reply_markup=add_listing_deal_kb())
    if isinstance(event, CallbackQuery):
        await event.answer()


@router.callback_query(AddListingSG.deal_type, F.data.startswith("add:deal:"))
async def add_deal(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(deal_type=callback.data.split(":")[2])
    await state.set_state(AddListingSG.city)
    await callback.message.edit_text("Город:")
    await callback.answer()


@router.message(AddListingSG.city)
async def add_city(message: Message, state: FSMContext) -> None:
    await state.update_data(city=(message.text or "").strip())
    await state.set_state(AddListingSG.district)
    await message.answer("Район:")


@router.message(AddListingSG.district)
async def add_district(message: Message, state: FSMContext) -> None:
    await state.update_data(district=(message.text or "").strip())
    await state.set_state(AddListingSG.price)
    await message.answer("Цена (число, USD):")


@router.message(AddListingSG.price)
async def add_price(message: Message, state: FSMContext) -> None:
    try:
        price = int((message.text or "").strip())
    except ValueError:
        await message.answer("Введите цену числом, например <code>750</code>:")
        return
    await state.update_data(price=price)
    await state.set_state(AddListingSG.rooms)
    await message.answer("Количество комнат (число):")


@router.message(AddListingSG.rooms)
async def add_rooms(message: Message, state: FSMContext) -> None:
    try:
        rooms = int((message.text or "").strip())
    except ValueError:
        await message.answer("Введите число комнат, например <code>2</code>:")
        return
    await state.update_data(rooms=rooms)
    await state.set_state(AddListingSG.area)
    await message.answer("Площадь, м² (число):")


@router.message(AddListingSG.area)
async def add_area(message: Message, state: FSMContext) -> None:
    try:
        area = float((message.text or "").strip().replace(",", "."))
    except ValueError:
        await message.answer("Введите площадь числом, например <code>54.5</code>:")
        return
    await state.update_data(area=area)
    await state.set_state(AddListingSG.floor)
    await message.answer(
        "Этаж в формате <code>этаж/всего</code> (например <code>5/9</code>) "
        "или просто <code>5</code>. Отправьте «-», чтобы пропустить."
    )


@router.message(AddListingSG.floor)
async def add_floor(message: Message, state: FSMContext) -> None:
    floor: int | None = None
    total_floors: int | None = None
    if not _is_skip(message.text):
        raw = (message.text or "").strip()
        try:
            if "/" in raw:
                floor_s, total_s = raw.split("/", 1)
                floor = int(floor_s)
                total_floors = int(total_s)
            else:
                floor = int(raw)
        except ValueError:
            await message.answer("Не понял этаж. Пример: <code>5/9</code> или <code>5</code>:")
            return

    await state.update_data(floor=floor, total_floors=total_floors)
    await state.set_state(AddListingSG.title)
    await message.answer("Заголовок объявления:")


@router.message(AddListingSG.title)
async def add_title(message: Message, state: FSMContext) -> None:
    await state.update_data(title=(message.text or "").strip())
    await state.set_state(AddListingSG.description)
    await message.answer("Описание (или «-», чтобы пропустить):")


@router.message(AddListingSG.description)
async def add_description(message: Message, state: FSMContext) -> None:
    description = "" if _is_skip(message.text) else (message.text or "").strip()
    await state.update_data(description=description)
    await state.set_state(AddListingSG.photo_url)
    await message.answer("Ссылка на фото (URL картинки):")


@router.message(AddListingSG.photo_url)
async def add_photo(message: Message, state: FSMContext, bot: Bot) -> None:
    await state.update_data(photo_url=(message.text or "").strip())
    data = await state.get_data()
    await state.clear()

    listing = await add_listing(data)
    await message.answer(
        f"✅ Объект #{listing.id} добавлен: <b>{listing.title}</b> "
        f"({deal_type_label(listing.deal_type)}, {listing.city}).\n"
        "Проверяю подписки и рассылаю уведомления…"
    )
    await run_notifications(bot)
