# Архитектура проекта

Шпаргалка "какой файл за что отвечает" — чтобы не держать всё в голове.
Не документация ради галочки, а рабочий справочник для себя.

## Слои (как запрос проходит через код)

```
HTTP-запрос
    ↓
api/v1/routers/*.py     — принимает HTTP, вызывает сервис, превращает
                           доменные исключения в HTTP-коды (404/409/...)
    ↓
domain/services/*.py    — бизнес-правила (например: "если is_closed
                           стало true → проставить closed_at",
                           "нельзя аггрегировать дважды")
    ↓
data/repositories/*.py  — ЕДИНСТВЕННОЕ место, где пишутся запросы
                           к базе через SQLAlchemy (select/insert/update)
    ↓
data/models/*.py        — описание таблиц: какие колонки, связи,
                           индексы, ограничения
```

Роутер не знает про SQL. Репозиторий не знает про бизнес-правила.
Сервис не пишет запросы сам, а просит репозиторий.

## `src/api/v1/` — HTTP-слой

- `routers/batches.py` — CRUD партий + аггрегация + запуск фоновых задач
  (`aggregate-async`, `reports`)
- `routers/products.py` — создание продукции
- `routers/webhooks.py` — CRUD подписок на вебхуки + история доставок
- `routers/tasks.py` — универсальный `GET /tasks/{id}`: статус/результат
  любой Celery-задачи (аггрегация, отчёты — все ходят через одну ручку)
- `schemas/*.py` — Pydantic-модели запросов/ответов. `batch.py` — с
  алиасами на кириллицу (`НомерПартии` и т.п.), т.к. этого требует ТЗ

## `src/domain/` — бизнес-логика

- `services/batch_service.py` — создание/обновление/список партий,
  проверка дубликатов, правило `is_closed → closed_at`, кэширование,
  рассылка событий (`batch_created`, `batch_closed`)
- `services/product_service.py` — добавление продукции, аггрегация,
  событие `product_aggregated`
- `services/webhook_service.py` — CRUD подписок + `dispatch_event(...)`:
  находит подходящие подписки и ставит для каждой задачу отправки
- `exceptions/__init__.py` — доменные исключения (`BatchNotFoundError`,
  `ProductAlreadyAggregatedError` и т.п.) — их ловят роутеры и
  превращают в HTTP-коды

## `src/data/` — доступ к БД

- `models/` — `WorkCenter`, `Batch`, `Product`, `WebhookSubscription`,
  `WebhookDelivery` (SQLAlchemy 2.0, `Mapped[...]`)
- `repositories/batch_repository.py` — `create`, `update`, `get_by_id`,
  `list_batches` (фильтры+пагинация), `list_expired_open_batches`
  (для Celery Beat)
- `repositories/product_repository.py` — `create`, `get_by_unique_code`,
  `update`
- `repositories/webhook_repository.py` — CRUD подписок, `create_delivery`,
  `get_delivery_by_id`, `list_active_by_event` (фильтр по PostgreSQL
  ARRAY через `any_()`), `list_failed_deliveries`
- `repositories/work_center_repository.py` — `get_by_identifier`, `create`

## `src/core/` — инфраструктура, общая для всего проекта

- `config.py` — настройки из `.env` (`Settings`, pydantic-settings)
- `database.py` — async engine, `AsyncSessionLocal`, `get_db()` (DI для
  роутеров), `Base` (родитель всех моделей)
- `cache.py` — Redis-клиент, декоратор `@cached(ttl, key_prefix)` и
  `invalidate(*prefixes)` — используется в `batch_service`/`product_service`
- `exceptions.py` — глобальный перехватчик необработанных исключений
  (клиенту — чистый 500, в лог — полный traceback)
- `rate_limit.py` — `slowapi`, лимит запросов по IP

## `src/tasks/` — Celery-задачи (фоновая обработка)

- `aggregation.py` — `aggregate_products_batch` — массовая аггрегация
  по списку кодов
- `webhooks.py` — `send_webhook_delivery` — реальная отправка одного
  вебхука (HMAC-подпись, retry с exponential backoff через `autoretry_for`)
- `reports.py` — `generate_batch_report` — Excel-отчёт по партии
  (3 листа), заливка в MinIO
- `scheduled.py` — задачи для Celery Beat: `auto_close_expired_batches`
  (каждый день в 01:00), `retry_failed_webhooks` (каждые 15 минут)

`src/celery_app.py` — сам объект `Celery` (broker/backend) +
`beat_schedule` (расписание для Beat).

## Прочее

- `src/storage/minio_service.py` — обёртка над MinIO (upload/download/
  list/delete, presigned URLs)
- `src/utils/hmac_utils.py` — подпись/проверка HMAC-SHA256 (используется
  при отправке вебхуков)
- `src/main.py` — сборка FastAPI-приложения: подключение роутеров,
  rate limiting, глобальный обработчик ошибок. Тонкий, без бизнес-логики.

## Инфраструктура (не Python-код)

- `docker-compose.yml` — Postgres, Redis, RabbitMQ, MinIO, Flower
- `alembic/` — миграции БД
- `Dockerfile` — образ самого API (пока не используется в docker-compose,
  api и worker запускаются локально через venv)

## Известные ограничения (осознанные, не баги)

- `WebhookService.dispatch_event` кладёт задачу в очередь до того, как
  внешний `session.commit()` в роутере реально завершится — в теории
  worker может попытаться прочитать ещё не закоммиченную запись
  (транзакционная гонка). На практике пока не проявлялось.
- `@cached` строит ключ кэша из `args[1:]` (пропускает `self`) + все
  `kwargs` — работает верно только если вызывать закэшированные методы
  именованными аргументами, не позиционными.
