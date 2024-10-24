from copy import deepcopy
from typing import Any, Optional

from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo


# copied from: https://stackoverflow.com/a/76560886
# metaclass for pydantic schemas
def partial_model(model: type[BaseModel]):
    """Make all fields optional, but preserve the given default values.

    Optional fields will be given None as a default value.
    This decorator is designed to be used with Update Schemas to adhere to our
    data acceptance methodology. Which is:
    1. Throw an error when extra fields are passed (responsibility of model this decorator is attached to via ConfigDict)
    2. Allow partial updates by passing in any number of fields with values to the update route.
        - As opposed to accepting raw dictionaries from users with field names.
    """

    def make_field_optional(
        field: FieldInfo, default: Any = None
    ) -> tuple[Any, FieldInfo]:
        new = deepcopy(field)
        new.default = default
        new.annotation = Optional[field.annotation]  # noqa: UP007
        return new.annotation, new

    return create_model(
        f"Partial{model.__name__}",
        __base__=model,
        __module__=model.__module__,
        **{
            field_name: make_field_optional(field_info)
            for field_name, field_info in model.model_fields.items()
        },
    )
