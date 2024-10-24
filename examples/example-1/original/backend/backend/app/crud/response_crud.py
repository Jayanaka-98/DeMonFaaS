from pydantic import PositiveInt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.models import Response
from app.schemas.response_schema import ResponseCreate, ResponseUpdate


class CRUDResponses(CRUDBase[Response, PositiveInt, ResponseCreate, ResponseUpdate]):
    """Inherited CRUD class for Responses table."""

    def __init__(self, *args, **kwargs):
        """Initialize the class."""
        super().__init__(*args, **kwargs)

    async def all_responses_to_question(
        self, db: AsyncSession, *, question_id: PositiveInt
    ) -> list[Response]:
        """Recursively load all comments all the way down."""
        stmt = (
            select(Response)
            .where(Response.question_id == question_id)
            .where(Response.parent_id == None)  # noqa
            .options(selectinload(Response.children, recursion_depth=-1))
        )
        result = [response for (response,) in (await db.execute(stmt)).all()]
        return result


responses = CRUDResponses(Response)
