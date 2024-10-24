import pytest
from fastapi.encoders import jsonable_encoder
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import responses
from app.models import Response
from app.schemas.response_schema import ResponseUpdate
from app.tests.utils.models import (
    create_random_nested_responses,
    create_random_question,
    create_random_response,
    create_random_user,
    random_response_info,
)
from app.tests.utils.utils import check_updated_fields, num_rows_in_tbl


@pytest.mark.anyio
async def test_create_response(db: AsyncSession):
    """Test creating a response."""
    db_q = await create_random_question(db)
    q_id = db_q.id
    creator_id = db_q.creator_id
    resp = random_response_info(q_id, creator_id)
    rows = await num_rows_in_tbl(db, Response)
    db_resp = await responses.create(db, obj_in=resp)

    assert await db_resp.awaitable_attrs.children == []
    assert db_resp.creator_id == resp.creator_id
    assert db_resp.question_id == resp.question_id
    assert db_resp.body == resp.body
    assert await num_rows_in_tbl(db, Response) == rows + 1


@pytest.mark.anyio
async def test_catching_bad_creates(db: AsyncSession):
    """Test behavior when a response shouldn't be created."""
    rows = await num_rows_in_tbl(db, Response)
    # Invalid user ID
    db_q = await create_random_question(db)
    resp = random_response_info(db_q.id, 10000000)
    with pytest.raises(IntegrityError):
        await responses.create(db, obj_in=resp)
    await db.rollback()

    # Invalid question ID
    db_u = await create_random_user(db)
    resp = random_response_info(10000000, db_u.id)
    with pytest.raises(IntegrityError):
        await responses.create(db, obj_in=resp)
    await db.rollback()

    assert await num_rows_in_tbl(db, Response) == rows


@pytest.mark.anyio
async def test_get_response(db: AsyncSession):
    """Test retrieving a response."""
    db_r = await create_random_response(db)

    db_resp = await responses.get(db, key=db_r.id)

    assert db_r == db_resp


@pytest.mark.anyio
async def test_catching_bad_gets(db: AsyncSession):
    """Test behavior when a response can't be retrieved."""
    db_resp = await responses.get(db, key=10000000)

    assert db_resp is None


@pytest.mark.anyio
async def test_delete_response(db: AsyncSession):
    """Test deleting a response."""
    db_r = await create_random_response(db)
    r_id = db_r.id

    rows = await num_rows_in_tbl(db, Response)
    del_resp = await responses.delete(db, key=r_id)

    assert await num_rows_in_tbl(db, Response) == rows - 1
    assert db_r == del_resp
    assert (await responses.get(db, key=r_id)) is None


@pytest.mark.anyio
async def test_catching_bad_deletes(db: AsyncSession):
    """Test behavior when a response can't be deleted."""
    del_resp = await responses.delete(db, key=10000000)

    assert del_resp is None


@pytest.mark.anyio
async def test_update_response(db: AsyncSession):
    """Test updating a response."""
    db_resp = await create_random_response(db)
    old_data = jsonable_encoder(db_resp)

    update_data = ResponseUpdate(
        is_anonymous=True, is_private=True, is_resolved=True, body="poo"
    )

    db_updated = await responses.update(db, key=db_resp.id, obj_in=update_data)
    new_data = jsonable_encoder(db_updated)

    check_updated_fields(Response, old_data, new_data, update_data)


@pytest.mark.anyio
async def test_catching_bad_updates(db: AsyncSession):
    """Test behavior when a response can't be updated."""
    update_data = ResponseUpdate(
        is_anonymous=True, is_private=True, is_resolved=True, body="poo"
    )

    db_updated = await responses.update(db, key=10000000, obj_in=update_data)
    assert db_updated is None


@pytest.mark.anyio
async def test_create_nested_response(db: AsyncSession):
    """Test creating nested responses."""
    db_resp = await create_random_response(db)
    db_resp_id = db_resp.id

    nest_resp = random_response_info(
        db_resp.question_id, db_resp.creator_id, parent_id=db_resp_id
    )

    db_nested = await responses.create(db, obj_in=nest_resp)
    nest_creator_id = db_nested.creator_id
    nest_q_id = db_nested.question_id
    nested_id = db_nested.id

    assert await db_resp.awaitable_attrs.children == [db_nested]
    assert db_nested.parent_id == db_resp_id

    nest_resp_2 = random_response_info(nest_q_id, nest_creator_id, parent_id=nested_id)

    db_nested_2 = await responses.create(db, obj_in=nest_resp_2)

    assert await db_nested.awaitable_attrs.children == [db_nested_2]
    assert db_nested_2.parent_id == nested_id
    assert len(jsonable_encoder(db_nested).get("children")) == 1


@pytest.mark.anyio
async def test_accessing_children_in_nested(db: AsyncSession):
    """Test getting all children in nested structure from nested responses."""
    db_q = await create_random_question(db)
    root_id = db_q.id
    user_id = db_q.creator_id

    resp_1_0_info = random_response_info(root_id, user_id)
    resp_1_0 = await responses.create(db, obj_in=resp_1_0_info)
    resp_1_0_id = resp_1_0.id
    resp_2_0_info = random_response_info(root_id, user_id)
    await responses.create(db, obj_in=resp_2_0_info)
    resp_1_1_info = random_response_info(root_id, user_id, parent_id=resp_1_0_id)
    await responses.create(db, obj_in=resp_1_1_info)
    resp_1_2_info = random_response_info(root_id, user_id, parent_id=resp_1_0_id)
    await responses.create(db, obj_in=resp_1_2_info)
    children = await responses.all_responses_to_question(db, question_id=root_id)

    assert len(children) == 2
    assert len(children[0].children) == 2
    assert len(children[1].children) == 0

    nested_responses = jsonable_encoder(children[0])
    assert nested_responses.get("body") == resp_1_0_info.body
    assert nested_responses.get("children")[0].get("body") == resp_1_1_info.body
    assert nested_responses.get("children")[1].get("body") == resp_1_2_info.body


@pytest.mark.anyio
async def test_deleting_parent_response(db: AsyncSession):
    """Test cascading delete of deleting parent response."""
    depth = 4
    db_root = await create_random_nested_responses(db, depth)
    rows = await num_rows_in_tbl(db, Response)

    db_del = await responses.delete(db, key=db_root.id)

    assert await num_rows_in_tbl(db, Response) == rows - depth
    assert db_del == db_root


@pytest.mark.anyio
async def test_get_nested_response(db: AsyncSession):
    """Test getting a nested response."""
    depth = 4
    db_root = await create_random_nested_responses(db, depth)

    db_nest = await responses.get(db, key=db_root.id)

    assert db_root == db_nest


@pytest.mark.anyio
async def test_parent_alive_after_child_delete(db: AsyncSession):
    """Test that the parent remains after the child response is deleted."""
    depth = 4
    db_root = await create_random_nested_responses(db, depth)
    root_id = db_root.id
    rows = await num_rows_in_tbl(db, Response)

    bob = (
        await (await responses.get(db, key=root_id))
        .children[0]
        .awaitable_attrs.children
    )[0].id
    await responses.delete(db, key=bob)

    assert await num_rows_in_tbl(db, Response) == rows - 2
    assert (
        await (await responses.get(db, key=root_id))
        .children[0]
        .awaitable_attrs.children
    ) == []
