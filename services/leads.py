"""CRUD заявок риелтору (leads)."""
from __future__ import annotations

from sqlalchemy import select

from database.engine import session_factory
from database.models import Lead


async def create_lead(
    *,
    user_id: int,
    listing_id: int | None,
    name: str,
    phone: str | None,
    message: str | None,
) -> Lead:
    async with session_factory() as session:
        lead = Lead(
            user_id=user_id,
            listing_id=listing_id,
            name=name,
            phone=phone,
            message=message,
            status="new",
        )
        session.add(lead)
        await session.commit()
        await session.refresh(lead)
        return lead


async def recent_leads(limit: int = 10) -> list[Lead]:
    async with session_factory() as session:
        stmt = select(Lead).order_by(Lead.created_at.desc()).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())
