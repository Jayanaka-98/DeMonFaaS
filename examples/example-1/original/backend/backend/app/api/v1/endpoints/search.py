from fastapi import APIRouter
from pydantic import PositiveInt

from app.api.deps import DBDep, SearchDep
from app.search.search_funcs import course_index_id, index_questions_in_course

router = APIRouter()


@router.post("/{course_id}/index")
async def index_this_courses_questions(
    db: DBDep, search_client: SearchDep, course_id: PositiveInt
):
    """Index the questions in this course."""
    return await index_questions_in_course(db, search_client, course_id=course_id)


@router.post("/{course_id}")
async def search_in_course(
    search_client: SearchDep, course_id: PositiveInt, query: str
):
    """Search for query in this course."""
    results = await search_client.index(course_index_id(course_id)).search(query=query)

    return results
