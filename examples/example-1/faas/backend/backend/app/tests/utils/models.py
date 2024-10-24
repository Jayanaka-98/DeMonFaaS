from pydantic import PositiveInt
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import courses, enrollments, questions, responses, users
from app.models import Course, CourseEnrollment, Question, Response, User
from app.models.course_enrollment_model import EnrollmentType
from app.schemas.course_enrollment_schema import EnrollmentCreate
from app.schemas.course_schema import CourseCreate
from app.schemas.question_schema import QuestionCreate
from app.schemas.response_schema import ResponseCreate
from app.schemas.user_schema import UserCreate
from app.tests.utils.utils import random_email, random_lower_string


def random_user_info() -> UserCreate:
    """Create pydantic model holding user information."""
    email = random_email()
    name = random_lower_string()
    user = UserCreate(email=email, name=name)
    return user


async def create_random_user(db: AsyncSession) -> User:
    """Create a random user and persist it to the database."""
    user_info = random_user_info()
    user = await users.create(db, obj_in=user_info)
    return user


def random_course_info(c_id: PositiveInt) -> CourseCreate:
    """Create pydantic model holding course information."""
    name = random_lower_string()
    course = CourseCreate(name=name, creator_id=c_id)
    return course


async def create_random_course(db: AsyncSession) -> Course:
    """Create a random course and a random user that made the course."""
    user: User = await create_random_user(db)
    course_info = random_course_info(user.id)
    created_course = await courses.create(db, obj_in=course_info)
    return created_course


async def create_random_enrollment(
    db: AsyncSession, role=EnrollmentType.member
) -> CourseEnrollment:
    """Create random course, and another rdm user to join that course."""
    course = (await create_random_course(db)).id
    user = (await create_random_user(db)).id
    enroll = EnrollmentCreate(course_id=course, user_id=user, role=role)
    created_enrollment = await enrollments.create(db, obj_in=enroll)
    return created_enrollment


def random_question_info(
    course_id: PositiveInt, user_id: PositiveInt
) -> QuestionCreate:
    """Create pydantic model holding question information."""
    q_create = QuestionCreate(
        creator_id=user_id,
        course_id=course_id,
        title=random_lower_string(),
        body=random_lower_string(),
    )
    return q_create


async def create_random_question(db: AsyncSession) -> Question:
    """Create a random question."""
    db_en = await create_random_enrollment(db)
    q_info = random_question_info(db_en.course_id, db_en.user_id)
    db_quest = await questions.create(db, obj_in=q_info)
    return db_quest


def random_response_info(
    question_id: PositiveInt, user_id: PositiveInt, parent_id: PositiveInt | None = None
) -> ResponseCreate:
    """Create pydantic model holding response info."""
    r_create = ResponseCreate(
        creator_id=user_id,
        question_id=question_id,
        parent_id=parent_id,
        body=random_lower_string(),
    )
    return r_create


async def create_random_response(db: AsyncSession) -> Response:
    """Create a random response to a question."""
    db_q = await create_random_question(db)
    r_create = random_response_info(db_q.id, db_q.creator_id)
    db_resp = await responses.create(db, obj_in=r_create)
    return db_resp


async def create_random_nested_responses(
    db: AsyncSession, depth: PositiveInt = 2
) -> Response:
    """Create many random responses and return the parent."""
    db_root = await create_random_response(db)
    u_id = db_root.creator_id
    q_id = db_root.question_id
    db_root_id = db_root.id
    last_parent_id = db_root.id
    for _ in range(depth - 1):
        nest_info = random_response_info(q_id, u_id, last_parent_id)
        db_nest = await responses.create(db, obj_in=nest_info)
        last_parent_id = db_nest.id

    return await responses.get(db, key=db_root_id)
