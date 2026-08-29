import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.core.cache import invalidate
from src.core.config import settings
from src.core.database import Base, get_db
from src.main import app

TEST_DATABASE_URL = settings.database_url.rsplit("/", 1)[0] + "/production_control_test"

test_engine = create_async_engine(TEST_DATABASE_URL)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def _reset_state():
    # Транзакция-с-откатом тут не подходит: прикладной код сам вызывает
    # session.commit() (репозитории/роутеры), так что откат снаружи ничего
    # не отменит без SAVEPOINT-обвязки. Проще чистить таблицы явно.
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())

    # @cached кладёт данные в Redis отдельно от SQL и не знает о тестовой
    # БД — не сбросишь, будешь читать чужой кэш (в том числе от ручных
    # прогонов на рабочей базе, а не только от прошлых тестов).
    await invalidate("dashboard_stats", "batches_list", "batch_detail")


@pytest_asyncio.fixture(autouse=True)
async def clean_tables():
    # До теста — на случай если что-то осталось от ручных прогонов приложения
    # или от теста, упавшего до своей же уборки. После — чтобы не оставлять
    # мусор следующему тесту.
    await _reset_state()
    yield
    await _reset_state()


@pytest_asyncio.fixture
async def client():
    async def override_get_db():
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    app.state.limiter.enabled = False  # иначе прогон тестов может словить 429

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    app.state.limiter.enabled = True
