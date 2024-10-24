from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from meilisearch_python_sdk import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import sessionmanager


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session."""
    async with sessionmanager.session() as session:
        yield session


DBDep = Annotated[AsyncSession, Depends(get_db_session)]


async def get_search_client() -> AsyncGenerator[AsyncClient, None]:
    """Get instance of async MEilisearch client."""
    async with AsyncClient(
        url=settings.MEILISEARCH_URL, api_key=settings.MEILISEARCH_API_KEY
    ) as client:
        yield client


SearchDep = Annotated[AsyncClient, Depends(get_search_client)]
