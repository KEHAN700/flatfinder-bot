# FlatFinder Bot

Telegram-бот для поиска недвижимости. Пользователь задаёт параметры поиска
(тип сделки, город, район, цена, количество комнат), получает подборку объектов
карточками с фотографиями и листанием, подписывается на поиск с уведомлениями о
новых подходящих объектах и оставляет заявку риелтору. Для администратора —
добавление объектов и просмотр заявок.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![aiogram](https://img.shields.io/badge/aiogram-3.x-2CA5E0?logo=telegram&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0%20async-D71F00)
![License](https://img.shields.io/badge/license-MIT-green)

> Демонстрационный проект на собственной засеянной базе примеров. Архитектура
> рассчитана на подключение реального источника данных (фид агентства или CRM)
> сменой слоя `services/` без переписывания хендлеров.

## Возможности

- **Поиск** пошаговым диалогом (FSM): тип сделки → город → район → цена → комнаты.
  Списки городов и районов формируются из реально доступных в базе объектов.
- **Выдача** карточками с фото и подписью, навигация листанием, раскрытие полного
  описания.
- **Подписки**: сохранение текущих фильтров, список активных подписок, удаление.
- **Уведомления**: фоновая задача (APScheduler) рассылает новые подходящие объекты
  без повторов (таблица `notifications_sent`).
- **Заявки** риелтору с автоматическим уведомлением администраторов.
- **Администрирование** (`/admin`, `/add_listing`, `/leads`, `/stats`) с доступом
  только для заданных `ADMIN_IDS`.

## Технологии

| Слой            | Решение                                  |
|-----------------|------------------------------------------|
| Язык            | Python 3.11+                             |
| Telegram        | aiogram 3.x (Router-based, FSM)          |
| База данных     | SQLAlchemy 2.0 (async) + aiosqlite       |
| Планировщик     | APScheduler                              |
| Конфигурация    | pydantic-settings + python-dotenv        |

## Архитектура

```
bot.py            Точка входа: Bot, Dispatcher, роутеры, планировщик, polling
config.py         Настройки из окружения (pydantic-settings)
database/         Async engine, модели, инициализация, идемпотентный seed
handlers/         Хендлеры: только разбор апдейтов и вызовы services
keyboards/        Reply- и inline-клавиатуры
states/           FSM State-группы
services/         Вся работа с данными: listings, subscriptions, leads, notifications
utils/            Форматирование карточек и подписок
```

Хендлеры не содержат запросов к базе данных — вся логика работы с данными
изолирована в слое `services/`.

## Запуск

```bash
git clone https://github.com/KEHAN700/flatfinder-bot.git
cd flatfinder-bot

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env        # заполнить BOT_TOKEN и ADMIN_IDS

python -m database.seed     # засеять примеры объектов (идемпотентно)
python bot.py               # запуск (long polling)
```

## Конфигурация

| Переменная            | Назначение                              | Пример                          |
|-----------------------|------------------------------------------|---------------------------------|
| `BOT_TOKEN`           | Токен бота от @BotFather                 | `123456:ABC-DEF...`             |
| `ADMIN_IDS`           | ID администраторов через запятую         | `111111111,222222222`           |
| `NOTIFY_INTERVAL_MIN` | Период задачи уведомлений, минуты        | `5`                             |
| `DB_URL`              | Async-строка подключения к базе          | `sqlite+aiosqlite:///estate.db` |

## Деплой

Репозиторий содержит [`render.yaml`](render.yaml) и [`Dockerfile`](Dockerfile).

**Render (Blueprint):** New → Blueprint → выбрать репозиторий → задать секреты
`BOT_TOKEN` и `ADMIN_IDS` → Deploy. Бот поднимает health-эндпоинт на `/health`,
что позволяет хостить его как Web Service.

**Docker:**

```bash
docker build -t flatfinder-bot .
docker run --env-file .env flatfinder-bot
```

## Модель данных

`users`, `listings`, `saved_searches`, `leads`, `notifications_sent`
(ограничение уникальности `saved_search_id + listing_id` исключает повторную
отправку одного объекта по одной подписке).

## Лицензия

MIT.
