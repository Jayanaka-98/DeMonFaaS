import pytest
from fastapi.encoders import jsonable_encoder
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import enrollments
from app.models import CourseEnrollment
from app.models.course_enrollment_model import EnrollmentType
from app.schemas.course_enrollment_schema import (
    EnrollmentCreate,
    EnrollmentPrimaryKey,
    EnrollmentResponse,
    EnrollmentUpdate,
)
from app.tests.utils.models import (
    create_random_course,
    create_random_enrollment,
    create_random_user,
)
from app.tests.utils.utils import check_updated_fields, num_rows_in_tbl


@pytest.mark.anyio
async def test_enroll_user_in_course(db: AsyncSession):
    """Test enrolling users in an existing course."""
    # using table.<attr> actually calls another query,
    # so I was getting random errors without this, unless
    # the data being asked for with .<attr> was from the last
    # used query. Below is an example of this behavior.
    existing_course_id = (await create_random_course(db)).id
    user_to_add_id = await create_random_user(db)

    enroll_create = EnrollmentCreate(
        course_id=existing_course_id, user_id=user_to_add_id.id
    )

    enroll_key = EnrollmentPrimaryKey(
        course_id=existing_course_id, user_id=user_to_add_id.id
    )

    enrollment = await enrollments.create(db, obj_in=enroll_create)

    assert enrollment is not None
    assert await enrollments.get(db, enroll_key) == enrollment


@pytest.mark.anyio
async def test_enroll_user_in_nonexistent_course(db: AsyncSession):
    """Test enrolling users in a non-existent course."""
    user_to_add = await create_random_user(db)

    enroll_create = EnrollmentCreate(course_id=1000000, user_id=user_to_add.id)

    with pytest.raises(IntegrityError):
        await enrollments.create(db, obj_in=enroll_create)


@pytest.mark.anyio
async def test_enroll_nonexistent_user_in_course(db: AsyncSession):
    """Test enrolling users in a non-existent course."""
    db_course = await create_random_course(db)

    enroll_create = EnrollmentCreate(course_id=db_course.id, user_id=10000000)

    with pytest.raises(IntegrityError):
        await enrollments.create(db, obj_in=enroll_create)


@pytest.mark.anyio
async def test_delete_enrollment(db: AsyncSession):
    """Test deleting an enrollment when providing class and user id."""
    enroll = await create_random_enrollment(db)
    pk = EnrollmentPrimaryKey(course_id=enroll.course_id, user_id=enroll.user_id)

    rows = await num_rows_in_tbl(db, CourseEnrollment)

    del_enroll = await enrollments.delete(db, key=pk)

    assert await num_rows_in_tbl(db, CourseEnrollment) == rows - 1
    assert await enrollments.get(db, pk) is None
    assert del_enroll == enroll


@pytest.mark.anyio
async def test_update_enrollment(db: AsyncSession):
    """Test updating the role of a user."""
    enroll = await create_random_enrollment(db)
    old_data = jsonable_encoder(enroll)
    pk = EnrollmentPrimaryKey(course_id=enroll.course_id, user_id=enroll.user_id)
    update_data = EnrollmentUpdate(role=EnrollmentType.admin)

    update_enroll = await enrollments.update(db, key=pk, obj_in=update_data)

    check_updated_fields(
        EnrollmentResponse, old_data, jsonable_encoder(update_enroll), update_data
    )
