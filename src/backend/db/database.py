import logging

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from core.config import settings

# Logger setup
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

db_password = settings.database.password.get_secret_value()

DATABASE_URL = f"mysql+aiomysql://{settings.database.username}:{db_password}@{settings.database.server}/{settings.database.name}?charset=utf8mb4"

# Create the async engine and session factory once (module-level, for reuse)
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def get_application_session():
    """
    Provides an application-level async database session.
    Usage: async with get_application_session() as session:
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await engine.dispose()
            # Close the session after use
            await session.close()
