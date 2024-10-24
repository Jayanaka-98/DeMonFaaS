from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase


class Base(AsyncAttrs, DeclarativeBase):
    """Declarative Base class.

    With async attribtues to prevent implicit IO
    https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#asyncio-orm-avoid-lazyloads
    """

    pass


# Import all models from below like
# This is so alembic can grab the metadata for the tables and
# attach them to Base
# from app.models.posts import Post # noqa
from app.models.user_model import User  # noqa
from app.models.course_model import Course  # noqa
from app.models.course_enrollment_model import CourseEnrollment  # noqa
from app.models.question_model import Question  # noqa
from app.models.response_model import Response  # noqa
