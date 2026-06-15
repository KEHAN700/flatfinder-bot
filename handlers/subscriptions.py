"""Подписки на поиск: список и удаление."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from keyboards.inline import subscription_delete_kb
from keyboards.reply import BTN_SUBSCRIPTIONS
from services import subscriptions
from utils.formatting import saved_search_text

router = Router(name="subscriptions")

EMPTY_TEXT = (
    "У вас пока нет подписок.\n"
    "Найдите жильё и нажмите «🔔 Подписаться» под карточкой, "
    "чтобы получать новые подходящие объекты."
)


@router.message(F.text == BTN_SUBSCRIPTIONS)
async def my_subscriptions(message: Message) -> None:
    searches = await subscriptions.list_subscriptions(message.from_user.id)
    if not searches:
        await message.answer(EMPTY_TEXT)
        return

    await message.answer(f"🔔 <b>Ваши подписки</b> ({len(searches)}):")
    for search in searches:
        await message.answer(
            saved_search_text(search),
            reply_markup=subscription_delete_kb(search.id),
        )


@router.callback_query(F.data.startswith("sub:del:"))
async def delete_subscription(callback: CallbackQuery) -> None:
    search_id = int(callback.data.split(":")[2])
    deleted = await subscriptions.delete_subscription(callback.from_user.id, search_id)
    if deleted:
        await callback.message.edit_text("🗑 Подписка удалена.")
        await callback.answer("Удалено")
    else:
        await callback.answer("Подписка не найдена.", show_alert=True)
