import pytest
from fastapi.encoders import jsonable_encoder
from meilisearch_python_sdk import AsyncClient as SearchAsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import questions
from app.schemas.question_schema import QuestionResponse
from app.search.search_funcs import course_index_id, index_questions_in_course
from app.tests.utils.models import (
    create_random_enrollment,
    random_question_info,
)


@pytest.mark.anyio
async def test_create_index(db: AsyncSession, search_client: SearchAsyncClient):
    """Test creating an index with documents from course questions.

    1. Create a course with 20 questions
    2. Call function to index these questions
    3. Assert that these questions are the same as db ones.
        The docs can be returned in any order. Uses `map_to_q` to get right one
    """
    db_enroll = await create_random_enrollment(db)
    c_id = db_enroll.course_id
    u_id = db_enroll.user_id

    num_qs = 20
    q_infos = []
    map_to_q = {}
    for i in range(num_qs):
        q_info = random_question_info(c_id, u_id)
        db_q = await questions.create(db, obj_in=q_info)
        q_infos.append(
            QuestionResponse(**jsonable_encoder(db_q)).model_dump(mode="json")
        )
        map_to_q[db_q.id] = i

    tasks = await index_questions_in_course(db, search_client, course_id=c_id)
    assert tasks is not None

    for task in tasks:
        await search_client.wait_for_task(task.task_uid)

    docs = (
        await search_client.index(course_index_id(c_id)).get_documents(limit=num_qs)
    ).results

    for i in range(num_qs):
        doc_id = docs[i]["id"]
        assert docs[i] == q_infos[map_to_q[doc_id]]
