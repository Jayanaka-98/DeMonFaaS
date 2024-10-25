from app.crud import users
from app.models import User
from app.api.deps import get_db_session
from app.utils.exceptions.common_exceptions import (
    KeyNotFoundException,
)
from app.api.deps import DBDep
from app.schemas.user_schema import UserCreate, UserResponse, UserUpdate
from fastapi import FastAPI, Depends, status
from collections.abc import AsyncGenerator
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import sessionmanager

app = FastAPI()

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session."""
    async with sessionmanager.session() as session:
        yield session


DBDep = Annotated[AsyncSession, Depends(get_db_session)]

@app.get("/{id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_user_by_id(id: PositiveInt, db: DBDep):
    """Get user by ID."""
    db_user = await users.get(db, key=id)
    if not db_user:
        raise KeyNotFoundException(User, id)

    return db_user


@app.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(db: DBDep, data: UserCreate):
    """Create a user."""
    existing_user = await users.get_by_email(db, data.email)
    if existing_user:
        raise ExistingObjectFoundException(User, "email", data.email)

    db_user = await users.create(db, obj_in=data)
    return db_user


@app.delete(
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


@app.put("/{id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_user(db: DBDep, id: PositiveInt, data: UserUpdate):
    """Complete or partial update of user."""
    db_user = await users.get(db, key=id)
    if not db_user:
        raise KeyNotFoundException(User, id)

    updated_user = await users.update(db, key=id, obj_in=data)

    return updated_user


# async def handle(id):
#     """Get user by ID."""
#     db = get_db_session()
#     db_user = await users.get(db, key=id)
#     if not db_user:
#         raise KeyNotFoundException(User, id)

#     return db_user