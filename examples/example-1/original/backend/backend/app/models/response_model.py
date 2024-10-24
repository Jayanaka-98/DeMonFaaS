from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.models import Base, Question, User
from app.utils.misc import utc_now


class Response(Base):
    """Response model.

    Notes
    -----
    parent_id is NULL for responses which are direct responses to the question.

    for `children`, following guidelines to not use cascade 'all' and to eager load:
    https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#asyncio-orm-avoid-lazyloads
    https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html#joined-eager-loading
    The eager load is one level deep. However, this will almost never be used, as the API will
    rely on CRUD routes that select all children given a parent response/question root.
    The next level for a response must be accessed using `await <Response>.awaitable_attrs.children`

    """

    __tablename__ = "responses"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    question_id = Column(Integer, ForeignKey(Question.id), nullable=False)
    creator_id = Column(Integer, ForeignKey(User.id), nullable=False)
    parent_id = Column(Integer, ForeignKey("responses.id"), nullable=True)
    is_anonymous = Column(Boolean, default=False)
    is_private = Column(Boolean, default=False)
    is_resolved = Column(Boolean, default=False)
    body = Column(String)

    children = relationship(
        "Response",
        cascade="save-update, merge, expunge, delete, delete-orphan",
        lazy="selectin",
    )
