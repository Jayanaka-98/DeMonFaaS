from fastapi import APIRouter, status
from fastapi.encoders import jsonable_encoder
from pydantic import PositiveInt

from app.api.deps import DBDep
from app.crud import enrollments, questions, responses
from app.models import CourseEnrollment, Question, Response
from app.schemas.course_enrollment_schema import EnrollmentPrimaryKey
from app.schemas.response_schema import ResponseCreate, ResponseResponse, ResponseUpdate
from app.utils.exceptions.common_exceptions import (
    KeyNotFoundException,
)

router = APIRouter()


@router.get("/{id}", response_model=ResponseResponse, status_code=status.HTTP_200_OK)
async def get_response_by_id(id: PositiveInt, db: DBDep):
    """Get response by ID."""
    db_response = await responses.get(db, key=id)
    if not db_response:
        raise KeyNotFoundException(Response, id)

    return db_response


@router.post("/", response_model=ResponseResponse, status_code=status.HTTP_201_CREATED)
async def create_response(db: DBDep, data: ResponseCreate):
    """Create a response.

    The question being responded to must exist
    The user creating the response must be enrolled in the course.
    """
    parent_q = await questions.get(db, key=data.question_id)
    if not parent_q:
        raise KeyNotFoundException(Question, data.question_id)
    q_course_id = parent_q.course_id

    enroll_pk = EnrollmentPrimaryKey(course_id=q_course_id, user_id=data.creator_id)
    existing_enrollment = await enrollments.get(db, enroll_pk)
    if not existing_enrollment:
        raise KeyNotFoundException(CourseEnrollment, enroll_pk)

    db_response = await responses.create(db, obj_in=data)
    db_response = ResponseResponse(**jsonable_encoder(db_response))

    return db_response


@router.delete(
    "/{id}", response_model=ResponseResponse, status_code=status.HTTP_202_ACCEPTED
)
async def delete_response(db: DBDep, id: PositiveInt):
    """Delete a response with the given ID."""
    db_response = await responses.get(db, key=id)
    if not db_response:
        raise KeyNotFoundException(Response, id)

    deleted_response = await responses.delete(db, key=id)

    return deleted_response


@router.put("/{id}", response_model=ResponseResponse, status_code=status.HTTP_200_OK)
async def update_response(db: DBDep, id: PositiveInt, data: ResponseUpdate):
    """Complete or partial update of response."""
    db_response = await responses.get(db, key=id)
    if not db_response:
        raise KeyNotFoundException(Response, id)

    updated_response = await responses.update(db, key=id, obj_in=data)

    return updated_response
