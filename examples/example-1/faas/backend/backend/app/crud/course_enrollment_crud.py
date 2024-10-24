from app.crud.base import CRUDBase
from app.models import CourseEnrollment
from app.schemas.course_enrollment_schema import (
    EnrollmentCreate,
    EnrollmentPrimaryKey,
    EnrollmentUpdate,
)


class CRUDCourseEnrollments(
    CRUDBase[CourseEnrollment, EnrollmentPrimaryKey, EnrollmentCreate, EnrollmentUpdate]
):
    """Inherited CRUD class for Course Enrollments table."""

    def __init__(self, *args, **kwargs):
        """Initialize the class."""
        super().__init__(*args, **kwargs)


enrollments = CRUDCourseEnrollments(CourseEnrollment)
