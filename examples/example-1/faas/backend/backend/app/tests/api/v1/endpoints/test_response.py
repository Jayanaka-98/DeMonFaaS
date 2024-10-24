import pytest
from fastapi.encoders import jsonable_encoder
from httpx import AsyncClient

from app.models import CourseEnrollment, Question, Response
from app.schemas.course_enrollment_schema import EnrollmentPrimaryKey
from app.schemas.response_schema import ResponseCreate, ResponseResponse, ResponseUpdate
from app.tests.utils.models import (
    create_random_enrollment,
    create_random_question,
    create_random_response,
    create_random_user,
)
from app.tests.utils.utils import check_updated_fields, num_rows_in_tbl
from app.utils.exceptions.common_exceptions import (
    KeyNotFoundException,
)

base_url = "/api_v1/response"


@pytest.mark.anyio
async def test_create_response(client: AsyncClient, db):
    """Test creating a valid response."""
    db_q = await create_random_question(db)
    create = ResponseCreate(
        creator_id=db_q.creator_id, question_id=db_q.id, body="HEllo."
    )

    rows = await num_rows_in_tbl(db, Response)

    response = await client.post(f"{base_url}/", json=create.model_dump())

    assert await num_rows_in_tbl(db, Response) == rows + 1
    assert response.status_code == 201


@pytest.mark.anyio
async def test_no_question_create_response(client: AsyncClient, db):
    """Test failing to create a response to a nonexistent question."""
    db_enroll = await create_random_enrollment(db)
    bad_create = ResponseCreate(
        creator_id=db_enroll.user_id, question_id=10000000, body="HEllo."
    )

    rows = await num_rows_in_tbl(db, Response)
    response = await client.post(f"{base_url}/", json=bad_create.model_dump())
    assert await num_rows_in_tbl(db, Response) == rows

    msg = KeyNotFoundException(Question, key=10000000)

    assert response.status_code == 404
    assert response.json()["detail"] == msg.detail


@pytest.mark.anyio
async def test_no_enrolled_user_create_response(client: AsyncClient, db):
    """Test failing to create a response when user isn't enrolled."""
    db_q = await create_random_question(db)
    db_q_id = db_q.id
    db_c_id = db_q.course_id
    db_user_not = await create_random_user(db)
    db_u_id = db_user_not.id

    bad_create = ResponseCreate(creator_id=db_u_id, question_id=db_q_id, body="HEllo.")

    rows = await num_rows_in_tbl(db, Response)
    response = await client.post(f"{base_url}/", json=bad_create.model_dump())
    assert await num_rows_in_tbl(db, Response) == rows

    enroll_pk = EnrollmentPrimaryKey(course_id=db_c_id, user_id=db_u_id)
    msg = KeyNotFoundException(CourseEnrollment, enroll_pk)

    assert response.status_code == 404
    assert response.json()["detail"] == msg.detail


@pytest.mark.anyio
async def test_delete_response(client: AsyncClient, db):
    """Test deleting an existing response."""
    db_resp_id = (await create_random_response(db)).id

    rows = await num_rows_in_tbl(db, Response)
    response = await client.delete(f"{base_url}/{db_resp_id}")
    assert await num_rows_in_tbl(db, Response) == rows - 1

    response.status_code == 202


@pytest.mark.anyio
async def test_invalid_delete_response(client: AsyncClient, db):
    """Test failing to delete a nonexistent response."""
    rows = await num_rows_in_tbl(db, Response)
    response = await client.delete(f"{base_url}/{10000000}")
    assert await num_rows_in_tbl(db, Response) == rows

    msg = KeyNotFoundException(Response, key=10000000)

    assert response.status_code == 404
    assert response.json()["detail"] == msg.detail


@pytest.mark.anyio
async def test_update_response(client: AsyncClient, db):
    """Test updating a response."""
    db_resp = await create_random_response(db)
    old_data = ResponseResponse(**jsonable_encoder(db_resp)).model_dump()
    update_data = ResponseUpdate(is_anonymous=True, body="i am anonymous.")
    response = await client.put(
        f"{base_url}/{db_resp.id}", json=update_data.model_dump(exclude_unset=True)
    )

    new_data = ResponseResponse(**response.json()).model_dump()

    assert response.status_code == 200
    check_updated_fields(ResponseResponse, old_data, new_data, update_data)


@pytest.mark.anyio
async def test_invalid_update_response(client: AsyncClient, db):
    """Test not updating a valid response."""
    update_data = ResponseUpdate(is_anonymous=True, body="i am anonymous.")
    response = await client.put(f"{base_url}/{10000000}", json=update_data.model_dump())

    msg = KeyNotFoundException(Response, key=10000000)

    assert response.status_code == 404
    assert response.json()["detail"] == msg.detail


@pytest.mark.anyio
async def test_invalid_get_response(client: AsyncClient, db):
    """Testing failing to get a nonexistent response."""
    response = await client.get(f"{base_url}/{10000000}")

    msg = KeyNotFoundException(Response, key=10000000)

    assert response.status_code == 404
    assert response.json()["detail"] == msg.detail
