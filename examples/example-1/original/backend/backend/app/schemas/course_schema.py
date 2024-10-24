from datetime import datetime

from pydantic import BaseModel, ConfigDict, PositiveInt

from app.schemas.metaclass import partial_model


class CourseCreate(BaseModel):
    """Info required to create a course."""

    name: str
    creator_id: PositiveInt


class CourseResponse(BaseModel):
    """Info to return to client requesting course."""

    name: str
    id: PositiveInt
    creator_id: PositiveInt
    created_at: datetime
    updated_at: datetime
    is_active: bool


@partial_model
class CourseUpdate(BaseModel):
    """All optional."""

    model_config: ConfigDict = {"extra": "forbid"}

    name: str
