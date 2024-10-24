from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def api_root():
    """Root route of entire API."""
    return {"message": "Root of API Version 1."}
