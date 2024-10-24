import pytest
from fastapi.encoders import jsonable_encoder
from httpx import AsyncClient, Request

from app.crud import courses
from app.models import Course
from app.schemas.course_schema import CourseCreate, CourseResponse, CourseUpdate
from app.tests.utils.models import (
    create_random_course,
    create_random_user,
    random_course_info,
)
from app.tests.utils.utils import check_updated_fields, num_rows_in_tbl
from app.utils.exceptions.common_exceptions import (
    ExistingObjectFoundException,
    KeyNotFoundException,
)

base_url = "/api_v1/course"


@pytest.mark.anyio
async def test_get_course_with_invalid_id(client: AsyncClient, db):
    """Test getting a course with an ID not present in the table."""
    non_course_id = 1000000
    response: Request = await client.get(f"{base_url}/{non_course_id}")

    msg = KeyNotFoundException.key_present_msg.format(
        table_name=Course.__tablename__, key=non_course_id
    )

    assert response.status_code == 404
    assert response.json() == {"detail": msg}


@pytest.mark.anyio
async def test_get_created_course(client: AsyncClient, db):
    """Test getting a course that exists in the table."""
    rows_before = await num_rows_in_tbl(db, Course)

    rdm_user = await create_random_user(db)
    course_data = random_course_info(rdm_user.id)

    db_course = await courses.create(db, obj_in=course_data)
    db_course_data = CourseResponse(**jsonable_encoder(db_course))

    response: Request = await client.get(f"{base_url}/{db_course.id}")
    resp_data = CourseResponse(**response.json())

    assert response.status_code == 200
    assert await num_rows_in_tbl(db, Course) == 1 + rows_before
    assert db_course_data.model_dump() == resp_data.model_dump()


@pytest.mark.anyio
async def test_create_course(client: AsyncClient, db):
    """Test creating a course."""
    rows_before = await num_rows_in_tbl(db, Course)

    user_data = await create_random_user(db)
    course_data = random_course_info(user_data.id)

    response = await client.post(f"{base_url}/", json=course_data.model_dump())
    resp_data = CourseResponse(**response.json())

    db_course = await courses.get(db, resp_data.id)
    db_course_data = CourseResponse(**jsonable_encoder(db_course))

    assert await num_rows_in_tbl(db, Course) == 1 + rows_before
    assert response.status_code == 201
    assert resp_data.model_dump() == db_course_data.model_dump()


@pytest.mark.anyio
async def test_create_course_that_already_exists(client: AsyncClient, db):
    """Test creating a course with a name currently used by another course."""
    first_course = await create_random_course(db)
    course_data = CourseCreate(**jsonable_encoder(first_course))
    rows_before = await num_rows_in_tbl(db, Course)

    msg = ExistingObjectFoundException.error_msg.format(
        table_name=Course.__tablename__, field="name", value=course_data.name
    )

    response = await client.post(f"{base_url}/", json=course_data.model_dump())

    assert await num_rows_in_tbl(db, Course) == rows_before
    assert response.status_code == 409
    assert response.json() == {"detail": msg}


@pytest.mark.anyio
async def test_delete_course_that_exists(client: AsyncClient, db):
    """Test deleting a course that exists."""
    created_db_course: Course = await create_random_course(db)
    c_course_data = CourseResponse(**jsonable_encoder(created_db_course))
    rows_before = await num_rows_in_tbl(db, Course)

    response = await client.delete(f"{base_url}/{created_db_course.id}")
    d_course_data = CourseResponse(**response.json())

    assert await num_rows_in_tbl(db, Course) == rows_before - 1
    assert response.status_code == 202
    assert c_course_data.model_dump() == d_course_data.model_dump()


@pytest.mark.anyio
async def test_delete_course_not_exists(client: AsyncClient, db):
    """Test deleting a course that doesn't exist."""
    id = 1000000
    rows_before = await num_rows_in_tbl(db, Course)

    msg = KeyNotFoundException.key_present_msg.format(
        table_name=Course.__tablename__, key=id
    )

    response = await client.delete(f"{base_url}/{id}")
    resp_data = response.json()

    assert await num_rows_in_tbl(db, Course) == rows_before
    assert response.status_code == 404
    assert resp_data == {"detail": msg}


@pytest.mark.anyio
async def test_update_course(client: AsyncClient, db):
    """Test update course."""
    course_data: Course = await create_random_course(db)
    json_created = CourseResponse(**jsonable_encoder(course_data)).model_dump()

    update_data = CourseUpdate(name="fake name")

    response = await client.put(
        f"{base_url}/{course_data.id}", json=update_data.model_dump()
    )

    json_updated = CourseResponse(**response.json()).model_dump()

    assert response.status_code == 200

    check_updated_fields(CourseResponse, json_created, json_updated, update_data)


@pytest.mark.anyio
async def test_update_course_via_dict(client: AsyncClient, db):
    """Test update course using a dictionary directly."""
    course_data: Course = await create_random_course(db)
    json_created = CourseResponse(**jsonable_encoder(course_data)).model_dump()

    update_data = {"name": "fake name"}

    response = await client.put(f"{base_url}/{course_data.id}", json=update_data)

    json_updated = CourseResponse(**response.json()).model_dump()

    assert response.status_code == 200

    check_updated_fields(CourseResponse, json_created, json_updated, update_data)


@pytest.mark.anyio
async def test_update_non_course(client: AsyncClient, db):
    """Test update course that doesn't exist."""
    non_course_id = 10000
    response: Request = await client.put(
        f"{base_url}/{non_course_id}", json={"name": " random name"}
    )

    msg = KeyNotFoundException.key_present_msg.format(
        table_name=Course.__tablename__, key=non_course_id
    )

    assert response.status_code == 404
    assert response.json() == {"detail": msg}


@pytest.mark.anyio
async def test_update_invalid_field(client: AsyncClient, db):
    """Test update user with invalid field."""
    db_created = await create_random_course(db)

    update_data = {"fake_field": "bob kjkj mco"}
    response: Request = await client.put(
        f"{base_url}/{db_created.id}", json=update_data
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_update_forbidden_field(client: AsyncClient, db):
    """Test update course with a field forbidden from being updated."""
    db_created = await create_random_course(db)

    update_data = {"id": 4000}
    response: Request = await client.put(
        f"{base_url}/{db_created.id}", json=update_data
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_update_bad_fields_with_good_fields(client: AsyncClient, db):
    """Test update user with both good and bad fields."""
    db_created = await create_random_course(db)

    update_data = {
        "id": 4000,
        "fake_field": "bad_value",
        "name": "new name",
        "creator_id": 55342,
    }
    response: Request = await client.put(
        f"{base_url}/{db_created.id}", json=update_data
    )

    assert response.status_code == 422
    assert (await courses.get(db, db_created.id)).name == db_created.name
