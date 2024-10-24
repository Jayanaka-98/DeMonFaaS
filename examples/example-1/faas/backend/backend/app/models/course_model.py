from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String

from app.models import Base, User
from app.utils.misc import utc_now


class Course(Base):
    """Definition for Course table."""

    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(), default=utc_now, nullable=False)
    updated_at = Column(DateTime(), default=utc_now, nullable=False, onupdate=utc_now)
    name = Column(String, unique=True, index=True)
    creator_id = Column(Integer, ForeignKey(User.id), nullable=False)
    is_active = Column(Boolean, default=True)
