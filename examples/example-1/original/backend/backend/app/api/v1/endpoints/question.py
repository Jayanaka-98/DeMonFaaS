from fastapi import APIRouter, status
from fastapi.encoders import jsonable_encoder
from pydantic import PositiveInt

from app.api.deps import DBDep
from app.crud import enrollments, questions, responses
from app.models import CourseEnrollment, Question
from app.schemas.course_enrollment_schema import EnrollmentPrimaryKey
from app.schemas.question_schema import QuestionCreate, QuestionResponse, QuestionUpdate
from app.schemas.response_schema import ResponseResponse
from app.utils.exceptions.common_exceptions import (
    KeyNotFoundException,
)

router = APIRouter()


@router.get("/{id}", response_model=QuestionResponse, status_code=status.HTTP_200_OK)
async def get_question_by_id(id: PositiveInt, db: DBDep):
    """Get question by ID."""
    db_question = await questions.get(db, key=id)
    if not db_question:
        raise KeyNotFoundException(Question, id)

    return db_question


@router.post("/", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
async def create_question(db: DBDep, data: QuestionCreate):
    """Create a question.

    The user creating the question must be enrolled in the course.
    """
    enroll_pk = EnrollmentPrimaryKey(course_id=data.course_id, user_id=data.creator_id)
    existing_enrollment = await enrollments.get(db, enroll_pk)
    if not existing_enrollment:
        raise KeyNotFoundException(CourseEnrollment, enroll_pk)

    db_question = await questions.create(db, obj_in=data)
    db_question = QuestionResponse(**jsonable_encoder(db_question))

    return db_question


@router.delete(
    "/{id}", response_model=QuestionResponse, status_code=status.HTTP_202_ACCEPTED
)
async def delete_question(db: DBDep, id: PositiveInt):
    """Delete a question with the given ID."""
    db_question = await questions.get(db, key=id)
    if not db_question:
        raise KeyNotFoundException(Question, id)

    deleted_question = await questions.delete(db, key=id)

    return deleted_question


@router.put("/{id}", response_model=QuestionResponse, status_code=status.HTTP_200_OK)
async def update_question(db: DBDep, id: PositiveInt, data: QuestionUpdate):
    """Complete or partial update of question."""
    db_question = await questions.get(db, key=id)
    if not db_question:
        raise KeyNotFoundException(Question, id)

    updated_question = await questions.update(db, key=id, obj_in=data)

    return updated_question


@router.get(
    "/{id}/responses",
    response_model=list[ResponseResponse],
    status_code=status.HTTP_200_OK,
)
async def get_all_responses_to_question(db: DBDep, id: PositiveInt):
    """Get hierarchical nested json of all responses to this question."""
    db_question = await questions.get(db, key=id)
    if not db_question:
        raise KeyNotFoundException(Question, id)

    q_responses = await responses.all_responses_to_question(db, question_id=id)

    return q_responses
