"""
Общие фикстуры для всех тестов. pytest подхватывает этот файл автоматически
по имени "conftest.py" — импортировать его руками в тестах не нужно.
"""

import asyncio
import sys

if sys.platform == "win32":
    # Та же самая история, что и в main.py/celery_app.py — без этого
    # psycopg в асинхронном режиме падает на Windows.
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.core.database import Base, get_db
from src.core.config import settings
from src.main import app

# Та же база, что в .env, но с другим именем — физически отдельная БД
# внутри того же Postgres-контейнера. Реальный код (src/...) её никогда
# не увидит — только тесты.
TEST_DATABASE_URL = settings.database_url.rsplit("/", 1)[0] + "/production_control_test"

test_engine = create_async_engine(TEST_DATABASE_URL)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    """
    scope="session" — эта фикстура выполняется ОДИН РАЗ на весь прогон
    тестов (а не перед каждым тестом отдельно). autouse=True — значит её
    не нужно явно запрашивать в тестах, pytest применит её сама.

    Base.metadata.create_all — создаёт все таблицы из наших моделей
    (Batch, Product, WorkCenter...) в тестовой базе, "с нуля", один раз
    перед первым тестом. drop_all после yield — сносит их после того,
    как ВСЕ тесты закончились (уборка на выход).
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(autouse=True)
async def clean_tables():
    """
    Эта — без scope, значит по умолчанию запускается ПЕРЕД КАЖДЫМ тестом
    (и её "уборка" после yield — ПОСЛЕ каждого теста).

    Почему нельзя просто открыть транзакцию и откатить её после теста
    (казалось бы, проще)? Потому что наш прикладной код сам вызывает
    session.commit() почти в каждом репозитории/роутере — и это уже
    реально фиксирует данные в базе, откат внешней транзакции их не
    сотрёт. Поэтому проще и честнее: после каждого теста явно очищаем
    все таблицы (delete), чтобы следующий тест начинал с пустой базы.
    """
    yield

    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest_asyncio.fixture
async def client():
    """
    HTTP-клиент, который стучится не в реальный запущенный uvicorn (это
    было бы медленно и требовало бы отдельного процесса), а НАПРЯМУЮ в
    объект FastAPI-приложения через ASGITransport — тот же код, что
    обрабатывает настоящие HTTP-запросы, просто без сети между нами и им.

    app.dependency_overrides — механизм FastAPI: "везде, где роутер
    просит зависимость get_db (нашу боевую сессию к реальной БД),
    подставь вместо неё вот эту функцию" — которая отдаёт сессию к
    тестовой базе. Без этого тесты били бы по твоей рабочей базе.
    """
    async def override_get_db():
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    # Rate limiting (slowapi) в тестах не нужен и только мешал бы —
    # при большом числе тестов подряд легко упереться в лимит "100/minute"
    # и получить 429 там, где тест ждёт 200/201.
    app.state.limiter.enabled = False

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    app.state.limiter.enabled = True
