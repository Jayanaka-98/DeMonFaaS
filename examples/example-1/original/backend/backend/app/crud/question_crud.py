from pydantic import PositiveInt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models import Question
from app.schemas.question_schema import QuestionCreate, QuestionUpdate


class CRUDQuestions(CRUDBase[Question, PositiveInt, QuestionCreate, QuestionUpdate]):
    """Inherited CRUD class for Questions table."""

    def __init__(self, *args, **kwargs):
        """Initialize the class."""
        super().__init__(*args, **kwargs)

    async def get_all_by_course_id(self, db: AsyncSession, c_id: PositiveInt):
        """Get all course names by ID."""
        result = await db.execute(
            select(self.model).where(self.model.course_id == c_id)
        )
        return result.all()


questions = CRUDQuestions(Question)
