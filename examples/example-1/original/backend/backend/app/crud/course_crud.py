from pydantic import PositiveInt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models import Course
from app.schemas.course_schema import CourseCreate, CourseUpdate


class CRUDCourses(CRUDBase[Course, PositiveInt, CourseCreate, CourseUpdate]):
    """Inherited CRUD class for Courses table."""

    def __init__(self, *args, **kwargs):
        """Initialize the class."""
        super().__init__(*args, **kwargs)

    async def get_by_name(self, db: AsyncSession, name: str):
        """Get course by unique name."""
        course = await db.execute(select(self.model).where(self.model.name == name))
        return course.scalar_one_or_none()

    async def get_all_course_names(self, db: AsyncSession):
        """Get all course names and id's."""
        course = await db.execute(select(self.model.id, self.model.name))
        return course.all()


courses = CRUDCourses(Course)
