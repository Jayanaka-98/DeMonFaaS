import pytest
from fastapi.encoders import jsonable_encoder
from httpx import AsyncClient

from app.crud import questions
from app.models import CourseEnrollment, Question
from app.schemas.course_enrollment_schema import EnrollmentPrimaryKey
from app.schemas.question_schema import QuestionResponse, QuestionUpdate
from app.tests.utils.models import (
    create_random_course,
    create_random_enrollment,
    create_random_nested_responses,
    create_random_question,
    create_random_user,
    random_question_info,
)
from app.tests.utils.utils import check_updated_fields, num_rows_in_tbl
from app.utils.exceptions.common_exceptions import (
    KeyNotFoundException,
)

base_url = "/api_v1/question"


@pytest.mark.anyio
async def test_get_question_with_invalid_id(client: AsyncClient, db):
    """Test getting a non-existent question."""
    response = await client.get(f"{base_url}/{10000000}")
    resp_data = response.json()
    msg = KeyNotFoundException(Question, key=10000000)

    assert response.status_code == 404
    assert msg.detail == resp_data["detail"]


@pytest.mark.anyio
async def test_get_question(client: AsyncClient, db):
    """Test getting an existing question."""
    db_q = await create_random_question(db)
    q_data = QuestionResponse(**jsonable_encoder(db_q))

    response = await client.get(f"{base_url}/{db_q.id}")
    resp_data = QuestionResponse(**response.json())

    assert response.status_code == 200
    assert q_data.model_dump() == resp_data.model_dump()


@pytest.mark.anyio
async def test_create_question(client: AsyncClient, db):
    """Test creating a question."""
    db_e = await create_random_enrollment(db)
    q_info = random_question_info(db_e.course_id, db_e.user_id)
    rows = await num_rows_in_tbl(db, Question)
    response = await client.post(f"{base_url}/", json=q_info.model_dump())
    resp_data = QuestionResponse(**response.json())

    db_q = await questions.get(db, resp_data.id)
    db_data = QuestionResponse(**jsonable_encoder(db_q))

    assert await num_rows_in_tbl(db, Question) == rows + 1
    assert resp_data.model_dump() == db_data.model_dump()


@pytest.mark.anyio
async def test_fail_create_question_no_enroll(client: AsyncClient, db):
    """Test failing to create a question because user not enrolled in the course."""
    db_c = (await create_random_course(db)).id
    db_u = (await create_random_user(db)).id
    q_info = random_question_info(db_c, db_u)
    enroll_pk = EnrollmentPrimaryKey(course_id=db_c, user_id=db_u)

    rows = await num_rows_in_tbl(db, Question)
    response = await client.post(f"{base_url}/", json=q_info.model_dump())
    resp_data = response.json()

    msg = KeyNotFoundException(CourseEnrollment, enroll_pk)

    assert await num_rows_in_tbl(db, Question) == rows
    assert response.status_code == 404
    assert msg.detail == resp_data["detail"]


@pytest.mark.anyio
async def test_fail_create_question_no_user(client: AsyncClient, db):
    """Test failing because user doesn't exist."""
    db_c = (await create_random_course(db)).id
    db_u = 10000000
    q_info = random_question_info(db_c, db_u)
    enroll_pk = EnrollmentPrimaryKey(course_id=db_c, user_id=db_u)

    rows = await num_rows_in_tbl(db, Question)
    response = await client.post(f"{base_url}/", json=q_info.model_dump())
    resp_data = response.json()

    msg = KeyNotFoundException(CourseEnrollment, enroll_pk)

    assert await num_rows_in_tbl(db, Question) == rows
    assert response.status_code == 404
    assert msg.detail == resp_data["detail"]


@pytest.mark.anyio
async def test_fail_create_question_no_course(client: AsyncClient, db):
    """Test failing because course doesn't exist."""
    db_c = 10000000
    db_u = (await create_random_user(db)).id
    q_info = random_question_info(db_c, db_u)
    enroll_pk = EnrollmentPrimaryKey(course_id=db_c, user_id=db_u)

    rows = await num_rows_in_tbl(db, Question)
    response = await client.post(f"{base_url}/", json=q_info.model_dump())
    resp_data = response.json()

    msg = KeyNotFoundException(CourseEnrollment, enroll_pk)

    assert await num_rows_in_tbl(db, Question) == rows
    assert response.status_code == 404
    assert msg.detail == resp_data["detail"]


@pytest.mark.anyio
async def test_delete_question(client: AsyncClient, db):
    """Test deleting a question."""
    db_q = await create_random_question(db)
    db_data = QuestionResponse(**jsonable_encoder(db_q))

    rows = await num_rows_in_tbl(db, Question)

    response = await client.delete(f"{base_url}/{db_q.id}")
    resp_data = QuestionResponse(**response.json())

    assert response.status_code == 202
    assert await num_rows_in_tbl(db, Question) == rows - 1
    assert db_data.model_dump() == resp_data.model_dump()


@pytest.mark.anyio
async def test_fail_delete_no_question(client: AsyncClient, db):
    """Test failing to delete a nonexistent question."""
    rows = await num_rows_in_tbl(db, Question)

    response = await client.delete(f"{base_url}/{10000000}")
    resp_data = response.json()

    msg = KeyNotFoundException(Question, key=10000000)

    assert response.status_code == 404
    assert await num_rows_in_tbl(db, Question) == rows
    assert msg.detail == resp_data["detail"]


@pytest.mark.anyio
async def test_update_question(client: AsyncClient, db):
    """Test updating a question."""
    db_q = await create_random_question(db)
    old_data = QuestionResponse(**jsonable_encoder(db_q)).model_dump()
    q_info = QuestionUpdate(
        is_private=True,
        is_anonymous=True,
        title="new title.",
        body="new body.",
        is_starred_for_course=True,
    )

    response = await client.put(
        f"{base_url}/{db_q.id}", json=q_info.model_dump(exclude_unset=True)
    )
    resp_data = QuestionResponse(**response.json()).model_dump()

    assert response.status_code == 200
    check_updated_fields(QuestionResponse, old_data, resp_data, q_info)


@pytest.mark.anyio
async def test_getting_responses_to_question(client: AsyncClient, db):
    """Test getting nested json responses to question."""
    depth = 3
    root_resp = await create_random_nested_responses(db, depth=depth)
    q_id = root_resp.question_id

    response = await client.get(f"{base_url}/{q_id}/responses")

    resp_data = response.json()[0]

    assert response.status_code == 200
    for d in range(depth):
        if d != depth - 1:
            assert resp_data.get("children") != []
            resp_data = resp_data.get("children")[0]
        else:
            assert resp_data.get("children") == []
