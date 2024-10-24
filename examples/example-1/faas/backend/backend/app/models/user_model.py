from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.models import Base
from app.utils.misc import utc_now


class User(Base):
    """Definition for User table."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(), default=utc_now, nullable=False)
    updated_at = Column(DateTime(), default=utc_now, nullable=False, onupdate=utc_now)
    email = Column(String, nullable=False, unique=True, index=True)
    name = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
