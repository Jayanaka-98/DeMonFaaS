from fastapi.encoders import jsonable_encoder
from meilisearch_python_sdk import AsyncClient as SearchAsyncClient
from pydantic import PositiveInt
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import courses, questions
from app.schemas.question_schema import QuestionResponse


def course_index_id(course_id: PositiveInt) -> str:
    """Return the index id for a course's search indexed questions."""
    return f"course{course_id}"


async def index_all_questions_in_every_course(
    db: AsyncSession, client: SearchAsyncClient
):
    """Index every question in every course.

    Every course should have their own search index, given that there are questions posted.
    For every course, gather all questions that are not in the index.
    """
    all_courses = courses.get_all_course_names(db)
    all_tasks = []
    for c_id, _ in all_courses:
        tasks = await index_questions_in_course(db, client, course_id=c_id)
        all_tasks.append(tasks)
    return all_tasks


async def index_questions_in_course(
    db: AsyncSession, client: SearchAsyncClient, *, course_id: PositiveInt
):
    """For a specific course, index all questions."""
    quests = await questions.get_all_by_course_id(db, course_id)
    if quests is []:
        return

    quests = [
        QuestionResponse(**jsonable_encoder(quest)).model_dump(mode="json")
        for (quest,) in quests
    ]

    return await client.index(course_index_id(course_id)).add_documents_in_batches(
        quests, primary_key="id"
    )
