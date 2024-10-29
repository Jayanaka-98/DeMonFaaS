from fastapi import APIRouter

from app.api.v1.endpoints import (
    # course,
    # course_enrollment,
    # question,
    # response,
    root,
    # search,
    # user,
)

api_router = APIRouter()
api_router.include_router(root.router, tags=["root"])
# api_router.include_router(user.router, prefix="/user", tags=["user"])
# api_router.include_router(course.router, prefix="/course", tags=["course"])
# api_router.include_router(
#     course_enrollment.router, prefix="/enrollment", tags=["enrollment"]
# )
# api_router.include_router(question.router, prefix="/question", tags=["question"])
# api_router.include_router(response.router, prefix="/response", tags=["response"])
# api_router.include_router(search.router, prefix="/search", tags=["search"])
