from sqlalchemy import Boolean, Column, DateTime, ForeignKeyConstraint, Integer, String

from app.models import Base, CourseEnrollment
from app.utils.misc import utc_now


class Question(Base):
    """Question table.

    A question can only be posted by a user enrolled in that course.
    """

    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(), default=utc_now, nullable=False)
    updated_at = Column(DateTime(), default=utc_now, nullable=False, onupdate=utc_now)

    creator_id = Column(Integer, nullable=False)
    course_id = Column(Integer, nullable=False)
    __table_args__ = (
        ForeignKeyConstraint(
            ["creator_id", "course_id"],
            [CourseEnrollment.user_id, CourseEnrollment.course_id],
        ),
    )

    is_anonymous = Column(Boolean, default=False)
    is_private = Column(Boolean, default=False)
    is_resolved = Column(Boolean, default=False)
    is_starred_for_course = Column(Boolean, default=False)
    title = Column(String, nullable=False)
    # TODO: Integrate Rich Text Body
    body = Column(String)
