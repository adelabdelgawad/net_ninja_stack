import logging
from contextlib import asynccontextmanager
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from core.config import settings

logger = logging.getLogger(__name__)

# SQLite database path
db_path = Path(
    settings.database.name if hasattr(settings.database, "name") else "app.db"
)

# For SQLite, use aiosqlite driver
database_url = f"sqlite+aiosqlite:///{db_path}"

# Create the async engine and session factory once (module-level, for reuse)
engine = create_async_engine(
    database_url,
    echo=False,
    connect_args={
        "check_same_thread": False,
        "timeout": 30,
    },
    pool_pre_ping=True,
    pool_recycle=300,
)

AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


@asynccontextmanager
async def get_session():
    async with AsyncSessionLocal() as session:
        yield session


def get_session_factory():
    """Return the session factory for creating multiple sessions"""
    return AsyncSessionLocal
