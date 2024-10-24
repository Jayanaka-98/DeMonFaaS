from fastapi import FastAPI

from app.api.v1.api import api_router as api_router_v1
from app.core.config import settings

############################
# Core API Instance
############################
app = FastAPI()


@app.get("/")
def root_of_whole_api():
    """Root of entire API application."""
    return {"message": "Root of API"}


app.include_router(api_router_v1, prefix=settings.API_V1_STR)
