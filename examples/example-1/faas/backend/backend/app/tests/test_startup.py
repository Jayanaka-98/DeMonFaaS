import pytest
from meilisearch_python_sdk import AsyncClient as SearchAsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.user_crud import users


@pytest.mark.anyio
async def test_superuser_exists(db: AsyncSession):
    """Test that the superuser exists."""
    sup_user = await users.get_by_email(db, settings.FIRST_SUPERUSER_EMAIL)

    assert sup_user is not None


@pytest.mark.anyio
async def test_search_connection_alive(search_client: SearchAsyncClient):
    """Test that the search index is properly connected to."""
    assert (await search_client.health()).status == "available"
