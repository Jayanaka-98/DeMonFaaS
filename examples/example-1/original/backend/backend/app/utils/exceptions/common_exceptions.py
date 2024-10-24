from typing import Any, Generic, TypeVar

from fastapi import HTTPException, status
from pydantic import BaseModel, PositiveInt
from sqlalchemy.orm import DeclarativeBase

ModelType = TypeVar("ModelType", bound=DeclarativeBase)
PrimaryKeySchemaType = TypeVar("PrimaryKeySchemaType", BaseModel, PositiveInt)


class KeyNotFoundException(HTTPException, Generic[ModelType]):
    """Exception for getting row in table with no/invalid ID."""

    key_present_msg = "Unable to find the {table_name} with key(s) {key}."
    no_key_msg = "{table_name} id not found."

    def __init__(
        self,
        model: type[ModelType],
        key: PrimaryKeySchemaType | None = None,
        headers: dict[str, Any] | None = None,
    ) -> None:
        """Initialize exception."""
        if key:
            msg = self.key_present_msg.format(table_name=model.__tablename__, key=key)
        else:
            msg = self.no_key_msg.format(table_name=model.__tablename__)
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=msg,
            headers=headers,
        )


class ExistingObjectFoundException(HTTPException, Generic[ModelType]):
    """Exception raised when an object already exists with same identifying data."""

    error_msg = (
        "A(n) {table_name} object already exists with {field} with value {value}"
    )

    def __init__(
        self,
        model: type[ModelType],
        field: str,
        value: str,
        headers: dict[str, Any] | None = None,
    ) -> None:
        """Initialize exception."""
        msg = self.error_msg.format(
            table_name=model.__tablename__, field=field, value=value
        )
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=msg,
            headers=headers,
        )
