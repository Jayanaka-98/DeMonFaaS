from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from meilisearch_python_sdk import AsyncClient as SearchAsyncClient
from sqlalchemy import event
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, SessionTransaction

from app.api.deps import get_db_session
from app.core.config import settings
from app.main import app


@pytest.fixture
def anyio_backend() -> str:
    """Clarify asyncio as backend for all pytest.mark.anyio decorators."""
    return "asyncio"


@pytest.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Return an AsyncClient of the application."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="https://test/"
    ) as c:
        yield c


# Provide Async Database connection
# This fixture is NEEDED for ALL API tests which tested routes rely on a database connection
# because it overrides the normal get_db dependency
# copied from: https://github.com/rhoboro/async-fastapi-sqlalchemy/blob/main/app/tests/conftest.py
@pytest.fixture
async def db() -> AsyncGenerator:
    """Generate async database session."""
    # https://github.com/sqlalchemy/sqlalchemy/issues/5811#issuecomment-756269881
    async_engine = create_async_engine(settings.get_db_uri_string())
    async with async_engine.connect() as conn:
        await conn.begin()
        await conn.begin_nested()
        AsyncSessionLocal = async_sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=conn,
            future=True,
        )

        async_session = AsyncSessionLocal()

        @event.listens_for(async_session.sync_session, "after_transaction_end")
        def end_savepoint(session: Session, transaction: SessionTransaction) -> None:
            """Perform clean up after a transaction ends."""
            if conn.closed:
                return
            if not conn.in_nested_transaction():
                if conn.sync_connection:
                    conn.sync_connection.begin_nested()

        async def test_get_session() -> AsyncGenerator:
            try:
                yield AsyncSessionLocal()
            except SQLAlchemyError:
                pass

        app.dependency_overrides[get_db_session] = test_get_session

        yield async_session
        await async_session.close()
        await conn.rollback()

    await async_engine.dispose()


@pytest.fixture(scope="function")
async def search_client() -> AsyncGenerator[SearchAsyncClient, None]:
    """Return an async client to interact with the search indexes."""
    async with SearchAsyncClient(
        url=settings.MEILISEARCH_URL, api_key=settings.MEILISEARCH_API_KEY
    ) as search_client:
        yield search_client
