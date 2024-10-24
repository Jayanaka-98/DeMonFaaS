import pytest
from httpx import AsyncClient, Response


@pytest.mark.anyio
async def test_app_root(client: AsyncClient):
    """Test app root."""
    response: Response = await client.get("/")

    assert {"message": "Root of API"} == response.json()
