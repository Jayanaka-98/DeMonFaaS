import pytest
from fastapi.encoders import jsonable_encoder
from httpx import AsyncClient, Request

from app.crud import users
from app.models import User
from app.schemas.user_schema import UserCreateSuper, UserResponse, UserUpdate
from app.tests.utils.models import random_user_info
from app.tests.utils.utils import check_updated_fields, num_rows_in_tbl
from app.utils.exceptions.common_exceptions import (
    ExistingObjectFoundException,
    KeyNotFoundException,
)

base_url = "/api_v1/user"


@pytest.mark.anyio
async def test_get_user_with_invalid_id(client: AsyncClient, db):
    """Test getting a user with an ID not present in the table."""
    non_user_id = 1000000
    response: Request = await client.get(f"{base_url}/{non_user_id}")

    msg = KeyNotFoundException.key_present_msg.format(
        table_name=User.__tablename__, key=non_user_id
    )

    assert response.status_code == 404
    assert response.json() == {"detail": msg}


@pytest.mark.anyio
async def test_get_created_user(client: AsyncClient, db):
    """Test getting a user that exists in the table."""
    rows_before = await num_rows_in_tbl(db, User)

    user_data = random_user_info()
    db_user = await users.create(db, obj_in=user_data)
    db_user_data = UserResponse(**jsonable_encoder(db_user))

    response: Request = await client.get(f"{base_url}/{db_user.id}")
    resp_data = UserResponse(**response.json())

    assert response.status_code == 200
    assert await num_rows_in_tbl(db, User) == 1 + rows_before
    assert db_user_data.model_dump() == resp_data.model_dump()


@pytest.mark.anyio
async def test_create_user(client: AsyncClient, db):
    """Test creating a user."""
    rows_before = await num_rows_in_tbl(db, User)

    user_data = random_user_info()
    response = await client.post(f"{base_url}/", json=user_data.model_dump())
    resp_data = UserResponse(**response.json())

    db_user = await users.get(db, resp_data.id)
    db_user_data = UserResponse(**jsonable_encoder(db_user))

    assert await num_rows_in_tbl(db, User) == 1 + rows_before
    assert response.status_code == 201
    assert resp_data.model_dump() == db_user_data.model_dump()


@pytest.mark.anyio
async def test_create_user_that_already_exists(client: AsyncClient, db):
    """Test creating a user with an email currently used by another user."""
    user_data = random_user_info()

    await users.create(db, obj_in=user_data)
    rows_before = await num_rows_in_tbl(db, User)

    msg = ExistingObjectFoundException.error_msg.format(
        table_name=User.__tablename__, field="email", value=user_data.email
    )

    response = await client.post(f"{base_url}/", json=user_data.model_dump())

    assert await num_rows_in_tbl(db, User) == rows_before
    assert response.status_code == 409
    assert response.json() == {"detail": msg}


@pytest.mark.anyio
async def test_delete_user_that_exists(client: AsyncClient, db):
    """Test deleting a user that exists."""
    user_data = random_user_info()

    created_db_user = await users.create(db, obj_in=user_data)
    c_user_data = UserResponse(**jsonable_encoder(created_db_user))
    rows_before = await num_rows_in_tbl(db, User)

    response = await client.delete(f"{base_url}/{created_db_user.id}")
    d_user_data = UserResponse(**response.json())

    assert await num_rows_in_tbl(db, User) == rows_before - 1
    assert response.status_code == 202
    assert c_user_data.model_dump() == d_user_data.model_dump()


@pytest.mark.anyio
async def test_delete_user_not_exists(client: AsyncClient, db):
    """Test deleting a user that doesn't exist."""
    id = 1000000
    rows_before = await num_rows_in_tbl(db, User)

    msg = KeyNotFoundException.key_present_msg.format(
        table_name=User.__tablename__, key=id
    )

    response = await client.delete(f"{base_url}/{id}")
    resp_data = response.json()

    assert await num_rows_in_tbl(db, User) == rows_before
    assert response.status_code == 404
    assert resp_data == {"detail": msg}


@pytest.mark.anyio
async def test_update_user(client: AsyncClient, db):
    """Test update user."""
    user_data = random_user_info()

    db_created = await users.create(db, obj_in=user_data)
    json_created = UserResponse(**jsonable_encoder(db_created)).model_dump()

    update_data = UserUpdate(email="bob@mail.com")

    response = await client.put(
        f"{base_url}/{db_created.id}", json=update_data.model_dump(exclude_unset=True)
    )

    json_updated = UserResponse(**response.json()).model_dump()

    assert response.status_code == 200

    check_updated_fields(UserResponse, json_created, json_updated, update_data)


@pytest.mark.anyio
async def test_update_user_via_dict(client: AsyncClient, db):
    """Test update user directly using a dict."""
    user_data = random_user_info()

    db_created = await users.create(db, obj_in=user_data)
    json_created = UserResponse(**jsonable_encoder(db_created)).model_dump()

    update_data = {"email": "bob@mail.com"}

    response = await client.put(f"{base_url}/{db_created.id}", json=update_data)

    json_updated = UserResponse(**response.json()).model_dump()

    assert response.status_code == 200

    check_updated_fields(UserResponse, json_created, json_updated, update_data)


@pytest.mark.anyio
async def test_update_non_user(client: AsyncClient, db):
    """Test update user that doesn't exist."""
    non_user_id = 10000
    response: Request = await client.put(
        f"{base_url}/{non_user_id}", json={"email": "bob@mail.com"}
    )

    msg = KeyNotFoundException.key_present_msg.format(
        table_name=User.__tablename__, key=non_user_id
    )

    assert response.status_code == 404
    assert response.json() == {"detail": msg}


@pytest.mark.anyio
async def test_update_invalid_field(client: AsyncClient, db):
    """Test update user with invalid field."""
    user_data = random_user_info()

    db_created = await users.create(db, obj_in=user_data)

    update_data = {"fake_field": "bob@mail.com"}
    response: Request = await client.put(
        f"{base_url}/{db_created.id}", json=update_data
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_update_forbidden_field(client: AsyncClient, db):
    """Test update user with a field forbidden from being updated."""
    user_data = random_user_info()

    db_created = await users.create(db, obj_in=user_data)

    update_data = {"id": 4000}
    response: Request = await client.put(
        f"{base_url}/{db_created.id}", json=update_data
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_update_bad_fields_with_good_fields(client: AsyncClient, db):
    """Test update user with both good and bad fields."""
    user_data = random_user_info()

    db_created = await users.create(db, obj_in=user_data)

    update_data = {"id": 4000, "fake_field": "bad_value", "email": "new@mail.com"}
    response: Request = await client.put(
        f"{base_url}/{db_created.id}", json=update_data
    )

    assert response.status_code == 422
    assert (await users.get(db, db_created.id)).email == user_data.email


@pytest.mark.anyio
async def test_cant_delete_superuser(client: AsyncClient, db):
    """Test that app throws error when trying to delete the superuser."""
    supa_user = UserCreateSuper(
        email="super@email.com", name="the super", is_superuser=True
    )
    db_super_user: User = await users.create_superuser(db, obj_in=supa_user)

    response = await client.delete(f"{base_url}/{db_super_user.id}")

    assert response.status_code == 403
