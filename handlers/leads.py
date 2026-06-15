"""FSM «Оставить заявку» риелтору + уведомление админов."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import settings
from keyboards.reply import BTN_LEAD, main_menu, share_contact
from services import leads
from services.listings import get_listing
from states.fsm import LeadSG

router = Router(name="leads")

SKIP_TOKENS = {"-", "нет", "пропустить", "skip"}


def _is_skip(text: str | None) -> bool:
    return (text or "").strip().lower() in SKIP_TOKENS


async def _start_lead(message: Message, state: FSMContext, listing_id: int | None) -> None:
    await state.clear()
    await state.update_data(listing_id=listing_id)
    await state.set_state(LeadSG.name)
    prefix = "📩 Заявка по выбранному объекту.\n\n" if listing_id else "📩 Новая заявка.\n\n"
    await message.answer(prefix + "Как вас зовут?")


@router.message(F.text == BTN_LEAD)
async def lead_from_menu(message: Message, state: FSMContext) -> None:
    await _start_lead(message, state, listing_id=None)


@router.callback_query(F.data.startswith("card:lead:"))
async def lead_from_card(callback: CallbackQuery, state: FSMContext) -> None:
    listing_id = int(callback.data.split(":")[2])
    await _start_lead(callback.message, state, listing_id=listing_id)
    await callback.answer()


@router.message(LeadSG.name)
async def lead_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer("Пожалуйста, введите имя текстом:")
        return
    await state.update_data(name=name)
    await state.set_state(LeadSG.phone)
    await message.answer(
        "Оставьте телефон — нажмите кнопку ниже или введите вручную.\n"
        "Можно пропустить, отправив «-».",
        reply_markup=share_contact(),
    )


@router.message(LeadSG.phone)
async def lead_phone(message: Message, state: FSMContext) -> None:
    if message.contact is not None:
        phone = message.contact.phone_number
    elif _is_skip(message.text):
        phone = None
    else:
        phone = (message.text or "").strip() or None

    await state.update_data(phone=phone)
    await state.set_state(LeadSG.message)
    await message.answer(
        "Добавьте комментарий к заявке или отправьте «-», чтобы пропустить.",
        reply_markup=main_menu(),
    )


@router.message(LeadSG.message)
async def lead_message(message: Message, state: FSMContext) -> None:
    comment = None if _is_skip(message.text) else (message.text or "").strip() or None
    data = await state.get_data()
    await state.clear()

    lead = await leads.create_lead(
        user_id=message.from_user.id,
        listing_id=data.get("listing_id"),
        name=data.get("name", ""),
        phone=data.get("phone"),
        message=comment,
    )

    await message.answer(
        "✅ Заявка отправлена! Риелтор свяжется с вами в ближайшее время.",
        reply_markup=main_menu(),
    )
    await _notify_admins(message, lead, comment)


async def _notify_admins(message: Message, lead, comment: str | None) -> None:
    if not settings.admin_ids:
        return

    listing_line = ""
    if lead.listing_id:
        listing = await get_listing(lead.listing_id)
        if listing:
            listing_line = f"\n🏠 Объект #{listing.id}: {listing.title}"

    user = message.from_user
    username = f" (@{user.username})" if user and user.username else ""
    text = (
        f"📩 <b>Новая заявка #{lead.id}</b>\n"
        f"👤 {lead.name}{username}\n"
        f"📞 {lead.phone or '—'}"
        f"{listing_line}\n"
        f"💬 {comment or '—'}\n"
        f"🆔 user_id: <code>{lead.user_id}</code>"
    )
    for admin_id in settings.admin_ids:
        try:
            await message.bot.send_message(admin_id, text)
        except Exception:
            pass
