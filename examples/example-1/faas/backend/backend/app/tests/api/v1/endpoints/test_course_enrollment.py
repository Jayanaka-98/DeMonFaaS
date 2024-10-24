import pytest
from fastapi.encoders import jsonable_encoder
from httpx import AsyncClient

from app.crud import enrollments
from app.models import Course, CourseEnrollment, User
from app.schemas.course_enrollment_schema import (
    EnrollmentCreate,
    EnrollmentPrimaryKey,
    EnrollmentResponse,
    EnrollmentType,
    EnrollmentUpdate,
)
from app.schemas.course_schema import CourseCreate
from app.tests.utils.models import (
    create_random_course,
    create_random_enrollment,
    create_random_user,
)
from app.tests.utils.utils import check_updated_fields, num_rows_in_tbl
from app.utils.exceptions.common_exceptions import (
    ExistingObjectFoundException,
    KeyNotFoundException,
)

base_url = "/api_v1/enrollment"


@pytest.mark.anyio
async def test_course_creator_auto_enrolled_as_owner(client: AsyncClient, db):
    """Test that a course creator is automatically enrolled as the course owner."""
    user_id = (await create_random_user(db)).id

    course_data = CourseCreate(name="a course.", creator_id=user_id)

    response = await client.post("/api_v1/course/", json=course_data.model_dump())
    resp_data = response.json()

    enroll_pk = EnrollmentPrimaryKey(course_id=resp_data.get("id"), user_id=user_id)

    db_enroll = await enrollments.get(db, enroll_pk)

    assert db_enroll.role == EnrollmentType.owner


@pytest.mark.anyio
async def test_create_enrollment(client: AsyncClient, db):
    """Test enrolling a user in a course."""
    rows_before = await num_rows_in_tbl(db, CourseEnrollment)

    db_course_id = (await create_random_course(db)).id
    db_user_id = (await create_random_user(db)).id
    create = EnrollmentCreate(course_id=db_course_id, user_id=db_user_id)

    response = await client.post(f"{base_url}/", json=create.model_dump())
    enroll_data = EnrollmentResponse(**response.json())

    db_enroll = await enrollments.get(db, EnrollmentPrimaryKey(**create.model_dump()))
    get_data = EnrollmentResponse(**jsonable_encoder(db_enroll))

    assert rows_before + 1 == await num_rows_in_tbl(db, CourseEnrollment)
    assert response.status_code == 201
    assert enroll_data.model_dump() == get_data.model_dump()


@pytest.mark.anyio
async def test_create_invalid_user_or_course(client: AsyncClient, db):
    """Test creating enrollments when either user or course don't exist."""
    db_course_id = (await create_random_course(db)).id
    db_user_id = (await create_random_user(db)).id
    bad_user = EnrollmentCreate(course_id=db_course_id, user_id=10000000)
    bad_course = EnrollmentCreate(course_id=10000000, user_id=db_user_id)

    response = await client.post(f"{base_url}/", json=bad_user.model_dump())
    resp = KeyNotFoundException(User, key=10000000)

    assert resp.detail == response.json()["detail"]
    assert response.status_code == 404

    response = await client.post(f"{base_url}/", json=bad_course.model_dump())
    resp = KeyNotFoundException(Course, key=10000000)

    assert resp.detail == response.json()["detail"]
    assert response.status_code == 404


@pytest.mark.anyio
async def test_create_enrollment_that_already_exists(client: AsyncClient, db):
    """Test enrolling a user in a course they are already enrolled in."""
    enroll = await create_random_enrollment(db)
    data = EnrollmentCreate(course_id=enroll.course_id, user_id=enroll.user_id)

    response = await client.post(f"{base_url}/", json=data.model_dump())

    resp = ExistingObjectFoundException(
        CourseEnrollment, "(course, user)", (data.course_id, data.user_id)
    )

    assert response.status_code == 409
    assert resp.detail == response.json()["detail"]


@pytest.mark.anyio
async def test_get_enrollment_info(client: AsyncClient, db):
    """Test getting enrollment information."""
    enroll = await create_random_enrollment(db)
    enroll_data = EnrollmentResponse(**jsonable_encoder(enroll))

    response = await client.get(f"{base_url}/{enroll.course_id}/{enroll.user_id}")

    assert response.status_code == 200
    assert enroll_data == EnrollmentResponse(**response.json())


@pytest.mark.anyio
async def test_get_enrollment_bad_info(client: AsyncClient, db):
    """Test failing to get enrollment because of bad data."""
    response = await client.get(f"{base_url}/{10000000}/{10000000}")

    assert response.status_code == 404


@pytest.mark.anyio
async def test_delete_enrollment(client: AsyncClient, db):
    """Test deleting an enrollment."""
    enroll = await create_random_enrollment(db)
    enroll_data = EnrollmentResponse(**jsonable_encoder(enroll))

    rows = await num_rows_in_tbl(db, CourseEnrollment)
    response = await client.delete(f"{base_url}/{enroll.course_id}/{enroll.user_id}")
    resp_data = EnrollmentResponse(**response.json())

    assert rows - 1 == await num_rows_in_tbl(db, CourseEnrollment)
    assert response.status_code == 202
    assert resp_data.model_dump() == enroll_data.model_dump()


@pytest.mark.anyio
async def test_fail_delete_nonexistent_enrollment(client: AsyncClient, db):
    """Test failing to delete a nonexistent enrollment."""
    bad_pk = EnrollmentPrimaryKey(course_id=10000000, user_id=10000000)
    response = await client.delete(f"{base_url}/{bad_pk.course_id}/{bad_pk.user_id}")

    resp = KeyNotFoundException(CourseEnrollment, bad_pk)

    assert response.status_code == 404
    assert resp.detail == response.json()["detail"]


@pytest.mark.anyio
async def test_update_role(client: AsyncClient, db):
    """Test updating a users role."""
    enroll = await create_random_enrollment(db)
    old_data = EnrollmentResponse(**jsonable_encoder(enroll)).model_dump()

    update_data = EnrollmentUpdate(role=EnrollmentType.admin).model_dump()

    response = await client.put(
        f"{base_url}/{enroll.course_id}/{enroll.user_id}", json=update_data
    )
    resp_data = EnrollmentResponse(**response.json()).model_dump()

    assert response.status_code == 200
    check_updated_fields(CourseEnrollment, old_data, resp_data, update_data)


@pytest.mark.anyio
async def test_fail_update_nonexistent_enrollment(client: AsyncClient, db):
    """Test failing to update a nonexistent enrollment."""
    bad_pk = EnrollmentPrimaryKey(course_id=10000000, user_id=10000000)
    update_data = EnrollmentUpdate(role=EnrollmentType.admin).model_dump()
    response = await client.put(
        f"{base_url}/{bad_pk.course_id}/{bad_pk.user_id}", json=update_data
    )

    resp = KeyNotFoundException(CourseEnrollment, bad_pk)

    assert response.status_code == 404
    assert resp.detail == response.json()["detail"]
