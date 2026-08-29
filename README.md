# Система контроля заданий на выпуск продукции

Учебный backend-проект на Python и FastAPI — управление сменными заданиями на
производстве, с асинхронной обработкой задач через Celery, файловым хранилищем
(MinIO) и внешними интеграциями (webhooks).

## Стек

- API: FastAPI, SQLAlchemy 2.0 (async), Pydantic v2
- БД: PostgreSQL 16, миграции — Alembic
- Асинхронные задачи: Celery + RabbitMQ (брокер) + Redis (result backend)
- Файловое хранилище: MinIO (S3-совместимое)
- Мониторинг задач: Flower

## Первый запуск

### 1. Инфраструктура (Docker)

```powershell
docker compose up -d
```

Поднимает Postgres, Redis, RabbitMQ, MinIO и Flower. Проверить, что всё
поднялось и здорово:

```powershell
docker compose ps
```

### 2. Виртуальное окружение и зависимости

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Скопируйте `.env.example` в `.env` и при необходимости поправьте значения под
свою машину (например, порты, если они у вас заняты — см. `docker-compose.yml`).

### 3. Миграции

```powershell
alembic upgrade head
```

### 4. Бакеты MinIO (один раз)

```powershell
python -m scripts.init_minio
```

### 5. Запуск API

```powershell
uvicorn src.main:app --reload
```

**Важно для Windows**: флаг `--reload` тут не просто для удобства — без него
`psycopg` в асинхронном режиме падает на Windows из-за несовместимости с
`ProactorEventLoop`, которую по умолчанию использует `uvicorn` вне
`--reload`/`--workers` режима.

### 6. Запуск Celery worker (в отдельном терминале)

```powershell
celery -A src.celery_app worker --loglevel=info --pool=solo
```

`--pool=solo` обязателен на Windows — дефолтный prefork-пул использует
`os.fork`, которого на Windows нет.

### 7. Запуск Celery Beat — планировщик (в отдельном терминале, опционально)

```powershell
celery -A src.celery_app beat --loglevel=info
```

Beat сам ничего не выполняет — он по расписанию (см. `celery_app.py`,
`beat_schedule`) кладёт задачи в очередь, а выполняет их обычный worker
(шаг 6), так что worker должен быть запущен тоже.

### Альтернатива шагам 5-7: всё в Docker

Вместо локального venv можно поднять api/worker/beat тоже контейнерами —
они не запускаются по умолчанию (`docker compose up -d` их не трогает,
только инфраструктуру), чтобы не конфликтовать по порту 8000 с локальным
`uvicorn`. Явно:

```powershell
docker compose --profile full up -d --build
```

Тогда шаги 5-7 (и активация venv) не нужны вообще — просто заходишь на
<http://127.0.0.1:8000>. Учти: presigned URL на файлы (отчёты/экспорт),
сгенерированные из контейнеров, будут указывать на `http://minio:9000/...`
— это имя резолвится только внутри docker-сети, с хоста по умолчанию не
откроется (для этого нужно прописать `minio` в hosts-файл на 127.0.0.1).

## Тесты

Тесты используют отдельную базу `production_control_test` в том же
Postgres-контейнере (создать один раз):

```powershell
docker exec production_control_db psql -U postgres -c "CREATE DATABASE production_control_test;"
```

Дальше просто:

```powershell
pytest
```

Не нужен ни запущенный `uvicorn`, ни Celery worker — тесты стучатся в
FastAPI-приложение напрямую, в памяти (`httpx.ASGITransport`). Но Postgres,
Redis и RabbitMQ должны быть подняты (`docker compose up -d`) — код
реально ходит в базу, кэш и очередь, просто в тестовую БД, а не в рабочую.

## Доступные адреса

- Проверка приложения: <http://127.0.0.1:8000/health>
- Swagger-документация: <http://127.0.0.1:8000/docs>
- RabbitMQ Management UI: <http://127.0.0.1:15672> (admin/admin)
- Flower (мониторинг Celery-задач): <http://127.0.0.1:5555>
- MinIO Console: <http://127.0.0.1:9001> (minioadmin/minioadmin)
