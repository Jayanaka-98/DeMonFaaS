import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer

from app.models import Base, Course, User
from app.utils.misc import utc_now


class EnrollmentType(str, enum.Enum):
    """All possible types of ways a user can be enrolled in a course.

    value must be same as variable name. Variable name as a string is what
    is persisted by SQLAlchemy, but python will pass the value when users write
    `EnrollmentType.<type>`.

    It subclasses `str` so that it is automatically json serializable.
    """

    member = "member"
    admin = "admin"
    owner = "owner"


class CourseEnrollment(Base):
    """Definition for table holding user enrollment in courses."""

    __tablename__ = "course_enrollments"

    created_at = Column(DateTime(), default=utc_now, nullable=False)
    updated_at = Column(DateTime(), default=utc_now, nullable=False, onupdate=utc_now)
    course_id = Column(Integer, ForeignKey(Course.id), primary_key=True)
    user_id = Column(Integer, ForeignKey(User.id), primary_key=True)
    role = Column(Enum(EnrollmentType))
