"""Generic CRUD interface.

Shamelessly copied from https://github.com/tiangolo/full-stack-fastapi-postgresql/blob/master/src/backend/app/app/crud/base.py.
"""
from typing import Generic, TypeVar

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, PositiveInt
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

ModelType = TypeVar("ModelType", bound=DeclarativeBase)
PrimaryKeySchemaType = TypeVar("PrimaryKeySchemaType", BaseModel, PositiveInt)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(
    Generic[ModelType, PrimaryKeySchemaType, CreateSchemaType, UpdateSchemaType]
):
    """Generic CRUD class."""

    def __init__(self, model: type[ModelType]):
        """CRUD object with default methods to Create, Read, Update, Delete (CRUD).

        **Parameters**

        * `model`: A SQLAlchemy model class

        PrimaryKeySchemaType can be either a pydantic model or a single positive int.

        This was allowed because the CRUDBase class should still work for composite key tables.
        Most tables are single primary key (with the name being ID if that is the case by convention),
        so we want this base class to allow simply querying by that integer instead of having to pass a
        pydantic model with one field (id).
        """
        self.model = model

    async def get(
        self, db: AsyncSession, key: PrimaryKeySchemaType
    ) -> ModelType | None:
        """Retrieve the object of type ModelType given it's id."""
        if isinstance(key, BaseModel):
            key = key.model_dump()
        return await db.get(self.model, key)

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        """Create object of type ModelType in database given passed in Data.

        Will fail if primary key is a foreign key, and it doesn't point to an existing object.
        """
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        key: PrimaryKeySchemaType,
        obj_in: UpdateSchemaType,
    ) -> ModelType | None:
        """Update ModelType passed in with values from relevant fields found in `obj_in`.

        Will fail if primary key is a foreign key, and it doesn't point to an existing object.
        """
        update_data = obj_in.model_dump(exclude_unset=True)

        update_stmt = update(
            self.model
        )  # .where(self.model.id == id).values(**update_data)

        if isinstance(key, BaseModel):
            for column, val in key.model_dump().items():
                update_stmt = update_stmt.where(getattr(self.model, column) == val)
        else:
            update_stmt = update_stmt.where(self.model.id == key)

        update_stmt = update_stmt.values(**update_data)

        await db.execute(update_stmt)
        await db.commit()
        if isinstance(key, BaseModel):
            key = key.model_dump()
        return await db.get(self.model, key)

    async def delete(
        self, db: AsyncSession, *, key: PrimaryKeySchemaType
    ) -> ModelType | None:
        """Remove object from ModelType with matching primary key."""
        if isinstance(key, BaseModel):
            key = key.model_dump()
        obj_to_delete = await db.get(self.model, key)
        if not obj_to_delete:
            return None

        if isinstance(key, BaseModel):
            key = key.model_dump()

        result_obj = await db.get(self.model, key)
        await db.delete(result_obj)
        await db.commit()
        return result_obj
