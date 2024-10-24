import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.user_crud import users
from app.db.session import sessionmanager
from app.schemas.user_schema import UserCreateSuper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_db(db: AsyncSession):
    """Load initial data into database."""
    user = await users.get_by_email(db, settings.FIRST_SUPERUSER_EMAIL)
    if not user:
        user_in = UserCreateSuper(
            email=settings.FIRST_SUPERUSER_EMAIL,
            name="Super User",
            # password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        user = await users.create_superuser(db, obj_in=user_in)


async def init() -> None:
    """Wrap loading initial db."""
    async with sessionmanager.session() as db:
        await init_db(db)


async def main() -> None:
    """Begin loading initial data."""
    logger.info("Creating initial data")
    await init()
    logger.info("Initial data created")


if __name__ == "__main__":
    asyncio.run(main())
