"""Фоновая джоба рассылки новых подходящих объектов подписчикам."""
from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from sqlalchemy import select

from database.engine import session_factory
from database.models import NotificationSent, SavedSearch
from keyboards.inline import notification_card_kb
from services.listings import matching_for_search
from utils.formatting import listing_caption

logger = logging.getLogger(__name__)


async def run_notifications(bot: Bot) -> None:
    """Для каждой активной подписки шлёт подходящие, ещё не отправленные объекты."""
    async with session_factory() as session:
        searches_result = await session.execute(
            select(SavedSearch).where(SavedSearch.is_active.is_(True))
        )
        searches = list(searches_result.scalars().all())

        for search in searches:
            listings = await matching_for_search(session, search)
            if not listings:
                continue

            sent_result = await session.execute(
                select(NotificationSent.listing_id).where(
                    NotificationSent.saved_search_id == search.id
                )
            )
            already_sent = {row[0] for row in sent_result.all()}

            for listing in listings:
                if listing.id in already_sent:
                    continue
                try:
                    await bot.send_photo(
                        chat_id=search.user_id,
                        photo=listing.photo_url,
                        caption=(
                            "🆕 <b>Новый объект по вашей подписке</b>\n\n"
                            + listing_caption(listing)
                        ),
                        reply_markup=notification_card_kb(listing.id),
                    )
                except TelegramAPIError as exc:
                    logger.warning(
                        "Не удалось отправить уведомление user=%s listing=%s: %s",
                        search.user_id,
                        listing.id,
                        exc,
                    )

                session.add(
                    NotificationSent(
                        saved_search_id=search.id,
                        listing_id=listing.id,
                    )
                )
                await session.commit()
