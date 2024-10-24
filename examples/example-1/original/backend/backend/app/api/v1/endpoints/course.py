from fastapi import APIRouter, status
from fastapi.encoders import jsonable_encoder
from pydantic import PositiveInt

from app.api.deps import DBDep
from app.crud import courses, enrollments, users
from app.models import Course, User
from app.schemas.course_enrollment_schema import EnrollmentCreate, EnrollmentType
from app.schemas.course_schema import CourseCreate, CourseResponse, CourseUpdate
from app.utils.exceptions.common_exceptions import (
    ExistingObjectFoundException,
    KeyNotFoundException,
)

router = APIRouter()


@router.get("/{id}", response_model=CourseResponse, status_code=status.HTTP_200_OK)
async def get_course_by_id(id: PositiveInt, db: DBDep):
    """Get course by ID."""
    db_course = await courses.get(db, key=id)
    if not db_course:
        raise KeyNotFoundException(Course, id)

    return db_course


@router.post("/", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(db: DBDep, data: CourseCreate):
    """Create a course.

    The course creator will be enrolled in the course with the `owner` `EnrollmentType`.
    """
    creator_exists = await users.get(db, data.creator_id)
    if not creator_exists:
        raise KeyNotFoundException(User, data.creator_id)

    existing_course = await courses.get_by_name(db, data.name)
    if existing_course:
        raise ExistingObjectFoundException(Course, "name", data.name)

    db_course = await courses.create(db, obj_in=data)
    db_course = CourseResponse(**jsonable_encoder(db_course))

    enroll_create = EnrollmentCreate(
        course_id=db_course.id, user_id=data.creator_id, role=EnrollmentType.owner
    )
    await enrollments.create(db, obj_in=enroll_create)

    return db_course


@router.delete(
    "/{id}", response_model=CourseResponse, status_code=status.HTTP_202_ACCEPTED
)
async def delete_course(db: DBDep, id: PositiveInt):
    """Delete a course with the given ID."""
    db_course = await courses.get(db, key=id)
    if not db_course:
        raise KeyNotFoundException(Course, id)

    deleted_course = await courses.delete(db, key=id)

    return deleted_course


@router.put("/{id}", response_model=CourseResponse, status_code=status.HTTP_200_OK)
async def update_course(db: DBDep, id: PositiveInt, data: CourseUpdate):
    """Complete or partial update of course."""
    db_course = await courses.get(db, key=id)
    if not db_course:
        raise KeyNotFoundException(Course, id)

    updated_course = await courses.update(db, key=id, obj_in=data)

    return updated_course
