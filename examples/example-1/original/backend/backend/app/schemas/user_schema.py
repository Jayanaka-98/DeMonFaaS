from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, PositiveInt

from app.schemas.metaclass import partial_model


class UserCreate(BaseModel):
    """Info required to create a user."""

    email: EmailStr
    name: str


class UserCreateSuper(UserCreate):
    """Info required to create a super user."""

    is_superuser: bool


class UserResponse(BaseModel):
    """Info to return to client requesting user."""

    name: str
    email: EmailStr
    id: PositiveInt
    created_at: datetime
    updated_at: datetime
    is_active: bool


@partial_model
class UserUpdate(BaseModel):
    """All optional."""

    model_config: ConfigDict = {"extra": "forbid"}

    name: str
    email: EmailStr
