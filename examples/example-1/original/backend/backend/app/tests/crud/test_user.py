import pytest
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import users
from app.models import User
from app.schemas.user_schema import UserUpdate
from app.tests.utils.models import random_user_info
from app.tests.utils.utils import check_updated_fields, num_rows_in_tbl


@pytest.mark.anyio
async def test_create_user(db: AsyncSession):
    """Test create user."""
    user_data = random_user_info()

    rows = await num_rows_in_tbl(db, User)

    db_user = await users.create(db, obj_in=user_data)

    assert db_user.email == user_data.email
    assert db_user.name == user_data.name

    assert await num_rows_in_tbl(db, User) == 1 + rows


@pytest.mark.anyio
async def test_read_user(db: AsyncSession):
    """Test read user."""
    user_data = random_user_info()

    db_user = await users.create(db, obj_in=user_data)

    db_read = await users.get(db, db_user.id)

    assert db_user == db_read


@pytest.mark.anyio
async def test_update_user(db: AsyncSession):
    """Test update user."""
    user_data = random_user_info()

    db_created = await users.create(db, obj_in=user_data)
    json_created = jsonable_encoder(db_created)

    update_data = UserUpdate(email="bob@mail.com")

    db_read = await users.update(db, key=db_created.id, obj_in=update_data)
    json_read = jsonable_encoder(db_read)

    check_updated_fields(User, json_created, json_read, update_data)


@pytest.mark.anyio
async def test_delete_user(db: AsyncSession):
    """Test delete user."""
    user_data = random_user_info()

    rows = await num_rows_in_tbl(db, User)

    db_user = await users.create(db, obj_in=user_data)

    assert await num_rows_in_tbl(db, User) == 1 + rows

    await users.delete(db, key=db_user.id)

    assert await num_rows_in_tbl(db, User) == rows


@pytest.mark.anyio
async def test_get_user_by_email(db: AsyncSession):
    """Test get user by email."""
    user_data = random_user_info()

    db_user = await users.create(db, obj_in=user_data)

    db_user_2 = await users.get_by_email(db, user_data.email)

    assert db_user == db_user_2


@pytest.mark.anyio
async def test_get_user_by_email_none(db: AsyncSession):
    """Test get user by email when no user exists with that email."""
    user_data = random_user_info()

    db_user = await users.get_by_email(db, user_data.email)

    assert db_user is None
