"""CRUD подписок (saved_searches)."""
from __future__ import annotations

from sqlalchemy import select

from database.engine import session_factory
from database.models import SavedSearch
from services.listings import SearchFilters


async def create_subscription(user_id: int, filters: SearchFilters) -> SavedSearch:
    """Сохраняет текущие фильтры поиска как подписку."""
    async with session_factory() as session:
        search = SavedSearch(
            user_id=user_id,
            deal_type=filters.deal_type,
            city=filters.city,
            district=filters.district,
            price_min=filters.price_min,
            price_max=filters.price_max,
            rooms_min=filters.rooms_min,
            rooms_max=filters.rooms_max,
            is_active=True,
        )
        session.add(search)
        await session.commit()
        await session.refresh(search)
        return search


async def list_subscriptions(user_id: int) -> list[SavedSearch]:
    """Активные подписки пользователя."""
    async with session_factory() as session:
        stmt = (
            select(SavedSearch)
            .where(
                SavedSearch.user_id == user_id,
                SavedSearch.is_active.is_(True),
            )
            .order_by(SavedSearch.created_at.desc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())


async def delete_subscription(user_id: int, search_id: int) -> bool:
    """Деактивирует подписку, если она принадлежит пользователю."""
    async with session_factory() as session:
        search = await session.get(SavedSearch, search_id)
        if search is None or search.user_id != user_id or not search.is_active:
            return False
        search.is_active = False
        await session.commit()
        return True
