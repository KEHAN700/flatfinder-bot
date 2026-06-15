"""/start, главное меню, «О боте»."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from keyboards.reply import BTN_ABOUT, main_menu
from services.listings import upsert_user

router = Router(name="start")

WELCOME_TEXT = (
    "👋 <b>Привет! Это бот по поиску недвижимости.</b>\n\n"
    "Помогу подобрать жильё в аренду или на покупку, подписаться на новые "
    "подходящие объекты и оставить заявку риелтору.\n\n"
    "Выберите действие в меню ниже 👇"
)

ABOUT_TEXT = (
    "ℹ️ <b>О боте</b>\n\n"
    "Я подбираю объекты недвижимости по вашим фильтрам: тип сделки, город, "
    "район, цена и комнаты. Можно листать карточки с фото, подписаться на поиск "
    "и получать уведомления о новых объектах, а также оставить заявку риелтору.\n\n"
    "🧪 Это рабочий демо-прототип на собственной базе примеров. В боевой версии "
    "источником данных служит фид агентства или CRM."
)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    user = message.from_user
    if user is not None:
        await upsert_user(user.id, user.username, user.first_name)
    await message.answer(WELCOME_TEXT, reply_markup=main_menu())


@router.message(F.text == BTN_ABOUT)
async def show_about(message: Message) -> None:
    await message.answer(ABOUT_TEXT, reply_markup=main_menu())
