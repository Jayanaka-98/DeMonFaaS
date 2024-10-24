from datetime import datetime

from pydantic import BaseModel, ConfigDict, PositiveInt

from app.schemas.metaclass import partial_model


class QuestionCreate(BaseModel):
    """Required information to create a question."""

    creator_id: PositiveInt
    course_id: PositiveInt

    is_anonymous: bool = False
    is_private: bool = False
    is_resolved: bool = False
    is_starred_for_course: bool = False
    title: str
    body: str = ""


class QuestionResponse(BaseModel):
    """Information returned when question queried for."""

    id: PositiveInt
    created_at: datetime
    updated_at: datetime

    creator_id: PositiveInt
    course_id: PositiveInt
    is_anonymous: bool
    is_private: bool
    is_resolved: bool
    is_starred_for_course: bool
    title: str
    body: str


@partial_model
class QuestionUpdate(BaseModel):
    """Fields able to be updated."""

    model_config: ConfigDict = {"extra": "forbid"}

    is_anonymous: bool
    is_private: bool
    is_resolved: bool
    is_starred_for_course: bool
    title: str
    body: str = ""
