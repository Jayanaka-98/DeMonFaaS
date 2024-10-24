from fastapi import APIRouter, HTTPException, status
from pydantic import PositiveInt

from app.api.deps import DBDep
from app.crud import users
from app.models import User
from app.schemas.user_schema import UserCreate, UserResponse, UserUpdate
from app.utils.exceptions.common_exceptions import (
    ExistingObjectFoundException,
    KeyNotFoundException,
)

router = APIRouter()


@router.get("/{id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_user_by_id(id: PositiveInt, db: DBDep):
    """Get user by ID."""
    db_user = await users.get(db, key=id)
    if not db_user:
        raise KeyNotFoundException(User, id)

    return db_user


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(db: DBDep, data: UserCreate):
    """Create a user."""
    existing_user = await users.get_by_email(db, data.email)
    if existing_user:
        raise ExistingObjectFoundException(User, "email", data.email)

    db_user = await users.create(db, obj_in=data)
    return db_user


@router.delete(
    "/{id}", response_model=UserResponse, status_code=status.HTTP_202_ACCEPTED
)
async def delete_user(db: DBDep, id: PositiveInt):
    """Delete a user with the given ID."""
    db_user = await users.get(db, key=id)
    if not db_user:
        raise KeyNotFoundException(User, id)

    if db_user.is_superuser:
        raise HTTPException(status.HTTP_403_FORBIDDEN)

    deleted_user = await users.delete(db, key=id)

    return deleted_user


@router.put("/{id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_user(db: DBDep, id: PositiveInt, data: UserUpdate):
    """Complete or partial update of user."""
    db_user = await users.get(db, key=id)
    if not db_user:
        raise KeyNotFoundException(User, id)

    updated_user = await users.update(db, key=id, obj_in=data)

    return updated_user
