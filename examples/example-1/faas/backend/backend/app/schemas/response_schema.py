from datetime import datetime

from pydantic import BaseModel, ConfigDict, PositiveInt

from app.schemas.metaclass import partial_model


class ResponseCreate(BaseModel):
    """Information required to create response."""

    creator_id: PositiveInt
    question_id: PositiveInt

    is_anonymous: bool = False
    is_private: bool = False

    body: str

    parent_id: PositiveInt | None = None


class ResponseResponse(BaseModel):
    """Info sent upon request for response's information.

    Requestd from database
    """

    id: PositiveInt
    creator_id: PositiveInt
    question_id: PositiveInt
    parent_id: PositiveInt | None = None

    created_at: datetime
    updated_at: datetime

    is_resolved: bool
    is_anonymous: bool = False
    is_private: bool = False

    body: str

    children: list["ResponseResponse"]

    model_config = {
        "from_attributes": True,
    }


ResponseResponse.model_rebuild()


@partial_model
class ResponseUpdate(BaseModel):
    """All optional."""

    model_config: ConfigDict = {"extra": "forbid"}

    is_anonymous: bool
    is_private: bool
    is_resolved: bool

    body: str
