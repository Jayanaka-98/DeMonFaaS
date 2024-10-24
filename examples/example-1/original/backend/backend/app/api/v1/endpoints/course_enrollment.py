from fastapi import APIRouter, status
from pydantic import PositiveInt

from app.api.deps import DBDep
from app.crud import courses, enrollments, users
from app.models import Course, CourseEnrollment, User
from app.schemas.course_enrollment_schema import (
    EnrollmentCreate,
    EnrollmentPrimaryKey,
    EnrollmentResponse,
    EnrollmentUpdate,
)
from app.utils.exceptions.common_exceptions import (
    ExistingObjectFoundException,
    KeyNotFoundException,
)

router = APIRouter()


@router.get(
    "/{course_id}/{user_id}",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_200_OK,
)
async def get_enrollment_by_key(
    db: DBDep, course_id: PositiveInt, user_id: PositiveInt
):
    """Get enrollment by course and user."""
    key = EnrollmentPrimaryKey(course_id=course_id, user_id=user_id)
    db_enrollment = await enrollments.get(db, key=key)
    if not db_enrollment:
        raise KeyNotFoundException(Course, key)

    return db_enrollment


@router.post(
    "/", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED
)
async def create_enrollment(db: DBDep, data: EnrollmentCreate):
    """Enroll a user in a course."""
    user_exists = await users.get(db, data.user_id)
    if not user_exists:
        raise KeyNotFoundException(User, data.user_id)

    course_exists = await courses.get(db, data.course_id)
    if not course_exists:
        raise KeyNotFoundException(Course, data.course_id)

    already_enrolled = await enrollments.get(
        db, EnrollmentPrimaryKey(**data.model_dump())
    )
    if already_enrolled:
        raise ExistingObjectFoundException(
            CourseEnrollment, "(course, user)", (data.course_id, data.user_id)
        )

    db_enrollment = await enrollments.create(db, obj_in=data)
    return db_enrollment


@router.delete(
    "/{course_id}/{user_id}",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def delete_enrollment(db: DBDep, course_id: PositiveInt, user_id: PositiveInt):
    """Delete an enrollment with the given key."""
    key = EnrollmentPrimaryKey(course_id=course_id, user_id=user_id)
    db_enroll = await enrollments.get(db, key=key)
    if not db_enroll:
        raise KeyNotFoundException(CourseEnrollment, key)

    deleted_enrollments = await enrollments.delete(db, key=key)

    return deleted_enrollments


@router.put(
    "/{course_id}/{user_id}",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_200_OK,
)
async def update_course(
    db: DBDep, course_id: PositiveInt, user_id: PositiveInt, data: EnrollmentUpdate
):
    """Complete or partial update of course."""
    key = EnrollmentPrimaryKey(course_id=course_id, user_id=user_id)
    db_course = await enrollments.get(db, key=key)
    if not db_course:
        raise KeyNotFoundException(CourseEnrollment, key)

    updated_course = await enrollments.update(db, key=key, obj_in=data)

    return updated_course
