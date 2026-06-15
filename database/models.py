"""SQLAlchemy 2.0 модели данных бота."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String, nullable=True)
    first_name: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    saved_searches: Mapped[list["SavedSearch"]] = relationship(back_populates="user")
    leads: Mapped[list["Lead"]] = relationship(back_populates="user")


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    deal_type: Mapped[str] = mapped_column(String)
    city: Mapped[str] = mapped_column(String)
    district: Mapped[str] = mapped_column(String)
    price: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String, default="USD")
    rooms: Mapped[int] = mapped_column(Integer)
    area: Mapped[float] = mapped_column(Float)
    floor: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_floors: Mapped[int | None] = mapped_column(Integer, nullable=True)
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String, default="")
    photo_url: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class SavedSearch(Base):
    __tablename__ = "saved_searches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    deal_type: Mapped[str] = mapped_column(String)
    city: Mapped[str] = mapped_column(String)
    district: Mapped[str | None] = mapped_column(String, nullable=True)
    price_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    price_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rooms_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rooms_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="saved_searches")


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    listing_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("listings.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    message: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="new")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="leads")


class NotificationSent(Base):
    __tablename__ = "notifications_sent"
    __table_args__ = (
        UniqueConstraint("saved_search_id", "listing_id", name="uq_search_listing"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    saved_search_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("saved_searches.id")
    )
    listing_id: Mapped[int] = mapped_column(Integer, ForeignKey("listings.id"))
    sent_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
