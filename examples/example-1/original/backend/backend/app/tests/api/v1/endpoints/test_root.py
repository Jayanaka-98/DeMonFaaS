import pytest
from httpx import AsyncClient, Response

base_url = "/api_v1/"


@pytest.mark.anyio
async def test_v1_root(client: AsyncClient):
    """Test v1 root."""
    response: Response = await client.get(base_url)

    assert response.json() == {"message": "Root of API Version 1."}
