import random
import string
from typing import Any

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import DeclarativeBase


async def num_rows_in_tbl(db: AsyncSession, table: type[DeclarativeBase]):
    """Return number of rows in passed in table."""
    num_rows = -1
    num_rows = await db.execute(select(func.count()).select_from(table))
    return num_rows.scalar()


def random_lower_string() -> str:
    """Create a random string of lowercase letters."""
    return "".join(random.choices(string.ascii_lowercase, k=32))


def random_email() -> str:
    """Create rdm email from combo of 2 rdm strings."""
    return f"{random_lower_string()}@{random_lower_string()}.com"


def check_updated_fields(
    model: type[DeclarativeBase] | type[BaseModel],
    old_data: dict,
    new_data: dict,
    updated_data: BaseModel | dict[str, Any],
):
    """Assert that updated_fields are the only fields that are different."""
    if not isinstance(updated_data, dict):
        updated_data: dict = updated_data.model_dump(exclude_unset=True)
    updated_fields = updated_data.keys()

    if issubclass(model, BaseModel):
        columns = model.model_fields.keys()
    else:
        columns = [column.name for column in inspect(model).c]

    for c in columns:
        if c == "updated_at":
            # Handled correctly by DB, don't worry about it
            continue
        if c in updated_fields:
            if updated_data.get(c) != old_data.get(c):
                assert old_data.get(c) != new_data.get(c)
            else:
                assert old_data.get(c) == new_data.get(c)
        else:
            assert old_data.get(c) == new_data.get(c)
