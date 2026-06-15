"""Идемпотентный засев примеров объектов недвижимости.

Запуск: python -m database.seed
"""
from __future__ import annotations

import asyncio
import logging

from sqlalchemy import func, select

from database.engine import init_db, session_factory
from database.models import Listing

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def _photo(seed: str) -> str:
    """Стабильная демо-картинка по seed (доступна Telegram по URL)."""
    return f"https://picsum.photos/seed/{seed}/900/600"


SEED_LISTINGS: list[dict] = [
    dict(deal_type="rent", city="Минск", district="Центр", price=600, rooms=1, area=42.0,
         floor=5, total_floors=9, title="Уютная студия у Немиги",
         description="Светлая квартира с новым ремонтом, рядом метро Немига, вся техника.",
         photo_url=_photo("minsk1")),
    dict(deal_type="rent", city="Минск", district="Центр", price=950, rooms=2, area=60.0,
         floor=7, total_floors=12, title="2-комнатная с видом на проспект",
         description="Просторная квартира, панорамные окна, паркинг, консьерж.",
         photo_url=_photo("minsk2")),
    dict(deal_type="rent", city="Минск", district="Уручье", price=450, rooms=1, area=38.0,
         floor=3, total_floors=16, title="Бюджетная однушка в Уручье",
         description="Тихий зелёный район, рядом метро и парк, для долгосрочной аренды.",
         photo_url=_photo("minsk3")),
    dict(deal_type="rent", city="Минск", district="Малиновка", price=1200, rooms=3, area=85.0,
         floor=10, total_floors=19, title="Семейная 3-комнатная в Малиновке",
         description="Новый дом, два санузла, гардеробная, кухня-гостиная.",
         photo_url=_photo("minsk4")),
    dict(deal_type="sale", city="Минск", district="Центр", price=145000, rooms=2, area=58.0,
         floor=4, total_floors=9, title="Продажа 2-комнатной в центре",
         description="Сталинка после капремонта, высокие потолки, развитая инфраструктура.",
         photo_url=_photo("minsk5")),
    dict(deal_type="sale", city="Минск", district="Уручье", price=98000, rooms=1, area=44.0,
         floor=8, total_floors=16, title="Однокомнатная в новостройке",
         description="Сдан дом, чистовая отделка, кладовая, закрытый двор.",
         photo_url=_photo("minsk6")),
    dict(deal_type="sale", city="Минск", district="Малиновка", price=210000, rooms=3, area=92.0,
         floor=12, total_floors=19, title="Просторная 3-комнатная",
         description="Панорамные окна, два балкона, подземный паркинг в подарок.",
         photo_url=_photo("minsk7")),
    dict(deal_type="rent", city="Москва", district="Хамовники", price=1800, rooms=2, area=70.0,
         floor=6, total_floors=14, title="Аренда 2-комнатной в Хамовниках",
         description="Премиум-класс, дизайнерский ремонт, рядом Москва-река и парки.",
         photo_url=_photo("msk1")),
    dict(deal_type="rent", city="Москва", district="Хамовники", price=2500, rooms=3, area=110.0,
         floor=9, total_floors=17, title="Видовая 3-комнатная",
         description="Панорама на центр, два санузла, охраняемая территория, паркинг.",
         photo_url=_photo("msk2")),
    dict(deal_type="rent", city="Москва", district="Митино", price=900, rooms=1, area=40.0,
         floor=11, total_floors=22, title="Однушка у метро Митино",
         description="Свежий ремонт, вся бытовая техника, 5 минут до метро.",
         photo_url=_photo("msk3")),
    dict(deal_type="rent", city="Москва", district="Митино", price=1300, rooms=2, area=64.0,
         floor=4, total_floors=17, title="2-комнатная для семьи",
         description="Тихий двор, школа и садик рядом, развитая инфраструктура.",
         photo_url=_photo("msk4")),
    dict(deal_type="sale", city="Москва", district="Хамовники", price=420000, rooms=2, area=68.0,
         floor=7, total_floors=14, title="Продажа квартиры в Хамовниках",
         description="Элитный дом, консьерж, паркинг, готова к проживанию.",
         photo_url=_photo("msk5")),
    dict(deal_type="sale", city="Москва", district="Митино", price=185000, rooms=1, area=42.0,
         floor=15, total_floors=22, title="Однокомнатная в Митино",
         description="Новостройка, чистовая отделка, хорошая транспортная доступность.",
         photo_url=_photo("msk6")),
    dict(deal_type="rent", city="Тбилиси", district="Ваке", price=700, rooms=2, area=65.0,
         floor=5, total_floors=8, title="Квартира в престижном Ваке",
         description="Рядом парк Ваке, кафе и рестораны, мебель и техника включены.",
         photo_url=_photo("tbs1")),
    dict(deal_type="rent", city="Тбилиси", district="Сабуртало", price=500, rooms=1, area=45.0,
         floor=3, total_floors=10, title="Светлая однушка в Сабуртало",
         description="Новый ремонт, балкон с видом на горы, рядом метро.",
         photo_url=_photo("tbs2")),
    dict(deal_type="rent", city="Тбилиси", district="Старый город", price=850, rooms=2, area=58.0,
         floor=2, total_floors=4, title="Аутентичная квартира в Старом городе",
         description="Историческое здание, балкон, в шаге от главных достопримечательностей.",
         photo_url=_photo("tbs3")),
    dict(deal_type="sale", city="Тбилиси", district="Ваке", price=125000, rooms=3, area=95.0,
         floor=6, total_floors=12, title="Продажа 3-комнатной в Ваке",
         description="Новостройка бизнес-класса, панорамные окна, паркинг.",
         photo_url=_photo("tbs4")),
    dict(deal_type="sale", city="Тбилиси", district="Сабуртало", price=72000, rooms=1, area=48.0,
         floor=9, total_floors=14, title="Инвестиционная однушка",
         description="Сдан дом, белый каркас, высокий потенциал для аренды.",
         photo_url=_photo("tbs5")),
    dict(deal_type="sale", city="Тбилиси", district="Старый город", price=98000, rooms=2, area=62.0,
         floor=3, total_floors=5, title="Квартира с историей",
         description="Отреставрированное здание, аутентичные детали, центр города.",
         photo_url=_photo("tbs6")),
]


async def seed() -> None:
    await init_db()
    async with session_factory() as session:
        count = await session.scalar(select(func.count()).select_from(Listing))
        if count and count > 0:
            logger.info("В БД уже %s объектов — засев пропущен (идемпотентно).", count)
            return

        session.add_all([Listing(**data) for data in SEED_LISTINGS])
        await session.commit()
        logger.info("Засеяно объектов: %s", len(SEED_LISTINGS))


if __name__ == "__main__":
    asyncio.run(seed())
