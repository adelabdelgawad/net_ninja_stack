import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

import pytz
from sqlalchemy import Engine, create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from sqlmodel import SQLModel, select

from core.config import settings
from db.model import ISP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

# SQLite database path
db_path = Path("app.db")

# SQLite connection URLs
SYNC_DB_URL = f"sqlite:///{db_path}"
ASYNC_DB_URL = f"sqlite+aiosqlite:///{db_path}"

# Create engines
sync_engine: Engine = create_engine(
    SYNC_DB_URL,
    echo=False,
    connect_args={"check_same_thread": False, "timeout": 30},
)

async_engine: AsyncEngine = create_async_engine(
    ASYNC_DB_URL,
    echo=False,
    connect_args={"check_same_thread": False, "timeout": 30},
)


def cairo_now():
    """Get current time in Cairo timezone."""
    return datetime.now(tz=pytz.timezone("Africa/Cairo"))


def create_database_if_not_exists() -> None:
    """
    For SQLite, the database file is created automatically when connecting.
    This function ensures the parent directory exists.
    """
    logger.info(f"Checking SQLite database path: {db_path}")

    try:
        # Ensure parent directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)

        if db_path.exists():
            logger.info(f"SQLite database file '{db_path}' already exists.")
        else:
            logger.info(f"SQLite database file '{db_path}' will be created.")

    except Exception as e:
        logger.error(f"Error preparing database path: {e}")
        sys.exit(1)


def create_tables(engine: Engine) -> None:
    """
    Creates all tables defined in SQLModel metadata if they don't exist.
    Uses a synchronous engine connected to the SQLite database.
    """
    logger.info("Attempting to create tables...")
    try:
        # SQLModel.metadata.create_all is synchronous
        SQLModel.metadata.create_all(engine)
        logger.info("Tables checked/created successfully.")
    except OperationalError as e:
        logger.error(
            f"Error connecting to database '{db_path}' for table creation: {e}"
        )
        logger.error("Ensure the database path is accessible and writable.")
        sys.exit(1)
    except Exception as e:
        logger.error(
            f"An unexpected error occurred during table creation: {e}"
        )
        sys.exit(1)


async def seed_default_isps(session: AsyncSession):
    """
    Create default ISP records if they don't exist.
    Seeds: WE, Orange, Vodafone, Etisalat
    """
    logger.info("Checking for default ISPs...")
    default_isps = ["WE", "Orange", "Vodafone", "Etisalat"]
    isps_to_create = []
    isp_names_to_create = []  # Store names separately to avoid lazy loading

    for isp_name in default_isps:
        result = await session.execute(select(ISP).where(ISP.name == isp_name))
        existing = result.scalar_one_or_none()

        if not existing:
            new_isp = ISP(name=isp_name)
            isps_to_create.append(new_isp)
            isp_names_to_create.append(isp_name)  # Store the name directly
            logger.info(f"Preparing to create ISP '{isp_name}'.")
        else:
            logger.info(f"ISP '{isp_name}' already exists.")

    if isps_to_create:
        # Bulk insert all new ISPs
        session.add_all(isps_to_create)
        await session.commit()
        # Use the pre-stored names instead of accessing isp.name after commit
        logger.info(
            f"Successfully created {len(isps_to_create)} new ISP(s): "
            f"{', '.join(isp_names_to_create)}"
        )
    else:
        logger.info("All default ISPs already exist. No new ISPs created.")


async def seed_default_data():
    logger.info("Starting default data seeding...")
    try:
        async with AsyncSession(async_engine) as session:
            # Seed ISPs
            await seed_default_isps(session)
        logger.info("Default data seeding completed successfully.")
    except Exception as e:
        logger.error(f"Error during default data seeding: {e}")
        raise


async def setup_database() -> None:
    logger.info("Starting database setup process...")
    create_database_if_not_exists()
    create_tables(sync_engine)
    await seed_default_data()
    logger.info("Database setup process completed successfully.")
    await async_engine.dispose()


if __name__ == "__main__":
    asyncio.run(setup_database())
