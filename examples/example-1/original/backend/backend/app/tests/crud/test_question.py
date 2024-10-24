import pytest
from fastapi.encoders import jsonable_encoder
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import questions
from app.models import Question
from app.schemas.question_schema import QuestionCreate, QuestionUpdate
from app.tests.utils.models import (
    create_random_course,
    create_random_enrollment,
    create_random_question,
    random_question_info,
)
from app.tests.utils.utils import check_updated_fields, num_rows_in_tbl


@pytest.mark.anyio
async def test_fail_create_question_no_enroll(db: AsyncSession):
    """Test creating a question in a random course when the user isn't enrolled."""
    db_course = await create_random_course(db)

    create_data = QuestionCreate(
        creator_id=db_course.creator_id,
        course_id=db_course.id,
        title="A question title.",
        body="body for a question.",
    )

    rows = await num_rows_in_tbl(db, Question)
    with pytest.raises(IntegrityError):
        await questions.create(db, obj_in=create_data)
    await db.rollback()

    assert await num_rows_in_tbl(db, Question) == rows


@pytest.mark.anyio
async def test_create_question(db: AsyncSession):
    """Test creating a question when user is enrolled in a course."""
    db_enroll = await create_random_enrollment(db)

    q_create = random_question_info(db_enroll.course_id, db_enroll.user_id)

    rows = await num_rows_in_tbl(db, Question)
    await questions.create(db, obj_in=q_create)

    assert await num_rows_in_tbl(db, Question) == rows + 1


@pytest.mark.anyio
async def test_get_question(db: AsyncSession):
    """Test getting an existing question."""
    db_q = await create_random_question(db)

    got_q = await questions.get(db, db_q.id)

    assert db_q == got_q


@pytest.mark.anyio
async def test_get_nonexistent_question(db: AsyncSession):
    """Test getting a nonexistent question."""
    got_q = await questions.get(db, 10000000)

    assert got_q is None


@pytest.mark.anyio
async def test_delete_created_question(db: AsyncSession):
    """Test deleting a question."""
    db_q = await create_random_question(db)
    db_q_id = db_q.id

    rows = await num_rows_in_tbl(db, Question)

    del_q = await questions.delete(db, key=db_q_id)

    assert await num_rows_in_tbl(db, Question) == rows - 1
    assert await questions.get(db, db_q_id) is None
    assert del_q == db_q


@pytest.mark.anyio
async def test_fail_delete_nonexistent_question(db: AsyncSession):
    """Test failing to delete a nonexistent question."""
    assert await questions.delete(db, key=10000000) is None


@pytest.mark.anyio
async def test_updating_question(db: AsyncSession):
    """Test updating an existing question."""
    db_q = await create_random_question(db)
    old_data = jsonable_encoder(db_q)

    update_data = QuestionUpdate(is_anonymous=True, body="different body.")

    update_q = await questions.update(db, key=old_data.get("id"), obj_in=update_data)
    new_data = jsonable_encoder(update_q)

    check_updated_fields(Question, old_data, new_data, update_data)


@pytest.mark.anyio
async def test_fail_updating_nonexistent_question(db: AsyncSession):
    """Test failing to update a non-existent question."""
    update_data = QuestionUpdate(is_anonymous=True, body="different body.")

    update_q = await questions.update(db, key=10000000, obj_in=update_data)
    assert update_q is None


@pytest.mark.anyio
async def test_get_all_questions_by_course_id(db: AsyncSession):
    """Test getting all questions by course id.

    Also tests that an empty list is returned for course with no questions.
    """
    db_enroll = await create_random_enrollment(db)
    db_id = db_enroll.course_id
    db_creator = db_enroll.user_id
    num_questions = 20

    made_questions = []
    for _ in range(num_questions):
        q_info = random_question_info(course_id=db_id, user_id=db_creator)
        made_q = await questions.create(db, obj_in=q_info)
        made_questions.append(made_q)

    all_qs = await questions.get_all_by_course_id(db, db_id)
    assert len(all_qs) == num_questions

    for i in range(num_questions):
        assert all_qs[i][0] == made_questions[i]

    db_enroll = await create_random_enrollment(db)
    db_id = db_enroll.course_id
    num_questions = 0

    assert len(await questions.get_all_by_course_id(db, db_id)) == 0
