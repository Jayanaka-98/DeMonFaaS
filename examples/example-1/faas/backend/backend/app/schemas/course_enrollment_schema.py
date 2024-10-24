from datetime import datetime

from pydantic import BaseModel, ConfigDict, PositiveInt

from app.models.course_enrollment_model import EnrollmentType
from app.schemas.metaclass import partial_model


class EnrollmentPrimaryKey(BaseModel):
    """Composite key information for CourseEnrollment table."""

    model_config: ConfigDict = {"extra": "ignore"}

    course_id: PositiveInt
    user_id: PositiveInt


class EnrollmentCreate(EnrollmentPrimaryKey):
    """Information required to enroll a user in a course."""

    role: EnrollmentType = EnrollmentType.member


@partial_model
class EnrollmentUpdate(BaseModel):
    """All optional."""

    model_config: ConfigDict = {"extra": "forbid"}

    role: EnrollmentType


class EnrollmentResponse(EnrollmentPrimaryKey):
    """Information about an enrollment."""

    role: EnrollmentType
    created_at: datetime
    updated_at: datetime
