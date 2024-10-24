from enum import Enum

from pydantic import (
    EmailStr,
    Field,
    PositiveInt,
    PostgresDsn,
    ValidationError,
    field_validator,
)
from pydantic_core.core_schema import ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict


class NodeEnum(str, Enum):
    """Enumeration for possible api environment states."""

    development = "development"
    production = "production"
    testing = "testing"


class APISettings(BaseSettings):
    """Settings for the API."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="allow"
    )

    NODE: NodeEnum = NodeEnum.development
    API_VERSION: str = "v1"
    API_V1_STR: str = f"/api_{API_VERSION}"
    MEILI_HTTP_ADDR: str  # port included
    MEILI_IS_HTTPS_URL: bool = False
    MEILISEARCH_URL: str = "http://localhost:7700"
    MEILISEARCH_API_KEY: str | None = Field(None, validation_alias="MEILI_MASTER_KEY")
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    DATABASE_HOST: str
    DATABASE_PORT: PositiveInt = 5432
    DATABASE_NAME: str

    # Fields validated last
    ASYNC_DATABASE_URI: PostgresDsn | str = ""

    @field_validator("ASYNC_DATABASE_URI", mode="after")
    def assemble_db_connection(
        cls, v: str | None, info: ValidationInfo
    ) -> str | PostgresDsn:
        """Create HTTP URL from postgres info."""
        if isinstance(v, str):
            if v == "":
                return PostgresDsn.build(
                    scheme="postgresql+asyncpg",
                    username=info.data["DATABASE_USER"],
                    password=info.data["DATABASE_PASSWORD"],
                    host=info.data["DATABASE_HOST"],
                    port=info.data["DATABASE_PORT"],
                    path=info.data["DATABASE_NAME"],
                )
        return v

    @field_validator("MEILISEARCH_URL", mode="before")
    def assemble_meili_url(cls, v: str, info: ValidationInfo) -> str:
        """Create either the HTTPS or HTTP url for connecting to meilisearch."""
        if not info.data["MEILI_HTTP_ADDR"]:
            raise ValidationError("A MEILI_HTTP_ADDR value is required")

        https = False

        if info.data["MEILI_IS_HTTPS_URL"] is True or (
            isinstance(info.data["MEILI_IS_HTTPS_URL"], str)
            and info.data["MEILI_IS_HTTPS_URL"].lower() == "true"
        ):
            https = True

        if https:
            return f"https://{info.data['MEILI_HTTP_ADDR']}"

        return f"http://{info.data['MEILI_HTTP_ADDR']}"

    def get_db_uri_string(self) -> str:
        """Return string representation of Database URI."""
        if isinstance(self.ASYNC_DATABASE_URI, str):
            return self.ASYNC_DATABASE_URI
        return self.ASYNC_DATABASE_URI.unicode_string()

    FIRST_SUPERUSER_EMAIL: EmailStr = "super@fakewebsite.com"
    FIRST_SUPERUSER_PASSWORD: str = "superuser"


settings = APISettings()
