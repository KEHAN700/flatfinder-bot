"""Бизнес-логика по объектам и пользователям: выборка, фильтрация, добавление."""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.engine import session_factory
from database.models import Lead, Listing, SavedSearch, User


@dataclass
class SearchFilters:
    """Набор фильтров поиска. None означает «любой» для соответствующего поля."""

    deal_type: str
    city: str
    district: str | None = None
    price_min: int | None = None
    price_max: int | None = None
    rooms_min: int | None = None
    rooms_max: int | None = None

    def to_dict(self) -> dict:
        return {
            "deal_type": self.deal_type,
            "city": self.city,
            "district": self.district,
            "price_min": self.price_min,
            "price_max": self.price_max,
            "rooms_min": self.rooms_min,
            "rooms_max": self.rooms_max,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SearchFilters":
        return cls(
            deal_type=data["deal_type"],
            city=data["city"],
            district=data.get("district"),
            price_min=data.get("price_min"),
            price_max=data.get("price_max"),
            rooms_min=data.get("rooms_min"),
            rooms_max=data.get("rooms_max"),
        )


async def upsert_user(user_id: int, username: str | None, first_name: str) -> None:
    """Создаёт пользователя или обновляет его имя/username при /start."""
    async with session_factory() as session:
        user = await session.get(User, user_id)
        if user is None:
            session.add(
                User(id=user_id, username=username, first_name=first_name or "")
            )
        else:
            user.username = username
            user.first_name = first_name or user.first_name
        await session.commit()


async def get_cities(deal_type: str) -> list[str]:
    """Города, в которых реально есть активные объекты данного типа сделки."""
    async with session_factory() as session:
        stmt = (
            select(Listing.city)
            .where(Listing.deal_type == deal_type, Listing.is_active.is_(True))
            .distinct()
            .order_by(Listing.city)
        )
        result = await session.execute(stmt)
        return [row[0] for row in result.all()]


async def get_districts(deal_type: str, city: str) -> list[str]:
    """Районы города с активными объектами данного типа сделки."""
    async with session_factory() as session:
        stmt = (
            select(Listing.district)
            .where(
                Listing.deal_type == deal_type,
                Listing.city == city,
                Listing.is_active.is_(True),
            )
            .distinct()
            .order_by(Listing.district)
        )
        result = await session.execute(stmt)
        return [row[0] for row in result.all()]


def matching_query(
    *,
    deal_type: str,
    city: str,
    district: str | None,
    price_min: int | None,
    price_max: int | None,
    rooms_min: int | None,
    rooms_max: int | None,
) -> Select:
    """Базовый SELECT по активным объектам, подходящим под фильтры.

    Используется и поиском, и джобой уведомлений — единый источник истины.
    """
    stmt = select(Listing).where(
        Listing.is_active.is_(True),
        Listing.deal_type == deal_type,
        Listing.city == city,
    )
    if district:
        stmt = stmt.where(Listing.district == district)
    if price_min is not None:
        stmt = stmt.where(Listing.price >= price_min)
    if price_max is not None:
        stmt = stmt.where(Listing.price <= price_max)
    if rooms_min is not None:
        stmt = stmt.where(Listing.rooms >= rooms_min)
    if rooms_max is not None:
        stmt = stmt.where(Listing.rooms <= rooms_max)
    return stmt


async def search(filters: SearchFilters) -> list[Listing]:
    """Возвращает подходящие объекты, свежие — первыми."""
    async with session_factory() as session:
        stmt = matching_query(**filters.to_dict()).order_by(Listing.created_at.desc())
        result = await session.execute(stmt)
        return list(result.scalars().all())


async def matching_for_search(
    session: AsyncSession, saved_search: SavedSearch
) -> list[Listing]:
    """Объекты, подходящие под сохранённую подписку (в рамках переданной сессии)."""
    stmt = matching_query(
        deal_type=saved_search.deal_type,
        city=saved_search.city,
        district=saved_search.district,
        price_min=saved_search.price_min,
        price_max=saved_search.price_max,
        rooms_min=saved_search.rooms_min,
        rooms_max=saved_search.rooms_max,
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_listing(listing_id: int) -> Listing | None:
    async with session_factory() as session:
        return await session.get(Listing, listing_id)


async def add_listing(data: dict) -> Listing:
    """Создаёт объект из словаря FSM добавления и возвращает его."""
    async with session_factory() as session:
        listing = Listing(
            deal_type=data["deal_type"],
            city=data["city"],
            district=data["district"],
            price=data["price"],
            currency=data.get("currency", "USD"),
            rooms=data["rooms"],
            area=data["area"],
            floor=data.get("floor"),
            total_floors=data.get("total_floors"),
            title=data["title"],
            description=data.get("description", ""),
            photo_url=data["photo_url"],
            is_active=True,
        )
        session.add(listing)
        await session.commit()
        await session.refresh(listing)
        return listing


async def get_stats() -> dict[str, int]:
    async with session_factory() as session:
        async def _count(model) -> int:
            result = await session.execute(select(func.count()).select_from(model))
            return int(result.scalar_one())

        return {
            "listings": await _count(Listing),
            "users": await _count(User),
            "searches": await _count(SavedSearch),
            "leads": await _count(Lead),
        }
