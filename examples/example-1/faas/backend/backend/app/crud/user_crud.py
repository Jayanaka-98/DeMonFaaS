from fastapi.encoders import jsonable_encoder
from pydantic import EmailStr, PositiveInt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models import User
from app.schemas.user_schema import UserCreate, UserCreateSuper, UserUpdate


class CRUDUsers(CRUDBase[User, PositiveInt, UserCreate, UserUpdate]):
    """Inherited CRUD class for Users table."""

    def __init__(self, *args, **kwargs):
        """Initialize the class."""
        super().__init__(*args, **kwargs)

    async def get_by_email(self, db: AsyncSession, email: EmailStr):
        """Get user by email."""
        users = await db.execute(select(self.model).where(self.model.email == email))
        return users.scalar_one_or_none()

    async def create_superuser(self, db: AsyncSession, *, obj_in: UserCreateSuper):
        """Create super user in database."""
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


users = CRUDUsers(User)
