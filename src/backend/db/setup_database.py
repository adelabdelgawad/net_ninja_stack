# setup_database.py

"""
An async-compatible database setup and seed script for a SQLModel project.

Handles:
1. Loading configuration from environment variables.
2. Creating the database if it doesn't exist (synchronous).
3. Creating tables based on SQLModel models if they don't exist (synchronous).
4. Seeding the database with default values (asynchronous).
"""

import logging
import sys
from datetime import datetime

import pytz
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel, select

from core.config import settings

# Import all models so SQLModel.metadata knows about them
from db.models import ISP, Job, TaskStatus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# Database URLs and Engines
# ------------------------------------------------------------------------------
# These URLs and engines are used to connect to the MySQL server and database.
# BASE_SYNC_URL connects to the server without specifying a database, used for creating the database if it doesn't exist.
# SYNC_DB_URL connects synchronously to the specific database for table creation.
# ASYNC_DB_URL connects asynchronously to the specific database for seeding data.

# Get the actual password value from SecretStr
db_password = settings.database.password.get_secret_value()

# URL for connecting *without* specifying a database (for initial creation check)
BASE_SYNC_URL = f"mysql+pymysql://{settings.database.username}:{db_password}@{settings.database.server}"
# URL for synchronous operations *on the specific database* (table creation)
SYNC_DB_URL = f"{BASE_SYNC_URL}/{settings.database.name}?charset=utf8mb4"
# URL for asynchronous operations (seeding)
ASYNC_DB_URL = f"mysql+aiomysql://{settings.database.username}:{db_password}@{settings.database.server}/{settings.database.name}?charset=utf8mb4"

# Create engines (deferring connection until needed)
sync_engine: Engine = create_engine(SYNC_DB_URL, echo=False, future=True)
async_engine: AsyncEngine = create_async_engine(
    ASYNC_DB_URL, echo=False, future=True
)

# ------------------------------------------------------------------------------
# Utility Functions
# ------------------------------------------------------------------------------


def cairo_now():
    """Get current time in Cairo timezone."""
    return datetime.now(tz=pytz.timezone("Africa/Cairo"))


# ------------------------------------------------------------------------------
# 1. Create Database If Not Exists (Synchronous)
# ------------------------------------------------------------------------------
# This function checks if the database exists by querying INFORMATION_SCHEMA.
# If the database does not exist, it creates it with utf8mb4 character set and collation.
# Uses a temporary engine connected to the server (no specific database).


def create_database_if_not_exists() -> None:
    """Creates the database if it does not already exist using a temporary base connection."""
    logger.info(f"Checking if database '{settings.database.name}' exists...")
    # Use a temporary engine connected to the server, not a specific DB
    base_engine = create_engine(BASE_SYNC_URL, echo=False, future=True)
    try:
        with base_engine.connect() as connection:
            # Check if database exists
            result = connection.execute(
                text(
                    "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA "
                    "WHERE SCHEMA_NAME = :db_name"
                ),
                {"db_name": settings.database.name},
            )
            exists = result.scalar()

            if not exists:
                # Create database with specific character set and collation
                connection.execute(
                    text(
                        f"CREATE DATABASE `{settings.database.name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                    )
                )
                # Important: Commit the transaction for DDL statements like CREATE DATABASE
                connection.commit()
                logger.info(
                    f"Database '{settings.database.name}' created successfully."
                )
            else:
                logger.info(
                    f"Database '{settings.database.name}' already exists."
                )
    except OperationalError as e:
        logger.error(
            f"Error connecting to the database server at {settings.database.server}: {e}"
        )
        logger.error(
            "Please check database credentials and ensure the server is running."
        )
        sys.exit(1)
    except ProgrammingError as e:
        logger.error(f"Database error during creation check: {e}")
        logger.error(
            f"Ensure user '{settings.database.username}' has privileges to check and create databases."
        )
        sys.exit(1)
    except Exception as e:
        logger.error(
            f"An unexpected error occurred during database creation check: {e}"
        )
        sys.exit(1)
    finally:
        # Dispose the temporary engine
        base_engine.dispose()


# ------------------------------------------------------------------------------
# 2. Create Tables If Not Exists (Synchronous)
# ------------------------------------------------------------------------------
# This function creates all tables defined in SQLModel metadata if they don't exist.
# It uses the synchronous engine connected to the specific database.


def create_tables(engine: Engine) -> None:
    """
    Creates all tables defined in SQLModel metadata if they don't exist.
    Uses a synchronous engine connected to the specific database.
    """
    logger.info("Attempting to create tables...")
    try:
        # SQLModel.metadata.create_all is synchronous
        SQLModel.metadata.create_all(engine)
        logger.info("Tables checked/created successfully.")
    except OperationalError as e:
        logger.error(
            f"Error connecting to database '{settings.database.name}' for table creation: {e}"
        )
        logger.error(
            "Ensure the database exists and connection details are correct."
        )
        sys.exit(1)
    except Exception as e:
        logger.error(
            f"An unexpected error occurred during table creation: {e}"
        )
        sys.exit(1)


# ------------------------------------------------------------------------------
# 3. Default Data Seeding Functions (Asynchronous)
# ------------------------------------------------------------------------------
# These functions create default records in the database if they don't already exist.
# They use async sessions and proper SQLModel select queries for data validation.


async def create_default_isp(session: AsyncSession):
    """Create default ISP record if it doesn't exist."""
    logger.info("Checking for default ISP...")
    result = await session.execute(select(ISP).where(ISP.name == "WE"))
    existing = result.scalar_one_or_none()
    if not existing:
        isp = ISP(name="WE", created_at=cairo_now(), updated_at=cairo_now())
        session.add(isp)
        await session.commit()
        logger.info("Default ISP 'WE' created successfully.")
    else:
        logger.info("Default ISP 'WE' already exists.")


async def create_default_task_statuses(session: AsyncSession):
    """Create unified task statuses for both manual and Celery-based task management."""
    logger.info("Checking for unified task statuses...")

    # Define all task statuses for complete task lifecycle
    unified_statuses = [
        # Planning/Setup Phase
        (
            "draft",
            "Task is being created/configured but not yet ready for scheduling",
        ),
        ("pending", "Task is ready and waiting to be scheduled"),
        (
            "scheduled",
            "Task has been scheduled and is waiting for its execution time",
        ),
        # Execution Phase
        (
            "queued",
            "Task has been sent to Celery queue but not yet picked up by a worker",
        ),
        ("in-progress", "Task is currently being executed"),
        ("retrying", "Task failed but is being retried"),
        # Completion Phase
        ("completed", "Task finished successfully"),
        ("failed", "Task failed after all retries exhausted"),
        ("timeout", "Task exceeded maximum execution time"),
        ("canceled", "Task was manually canceled before/during execution"),
        # Special States
        ("paused", "Task execution is temporarily suspended"),
        ("skipped", "Task was skipped due to conditions not being met"),
        ("revoked", "Task was revoked from Celery queue"),
    ]

    for status_name, description in unified_statuses:
        result = await session.execute(
            select(TaskStatus).where(TaskStatus.name == status_name)
        )
        existing = result.scalar_one_or_none()
        if not existing:
            status = TaskStatus(name=status_name, description=description)
            session.add(status)
            logger.info(f"Task status '{status_name}' created.")
        else:
            logger.info(f"Task status '{status_name}' already exists.")

    await session.commit()
    logger.info("Unified task statuses setup completed.")


async def create_default_jobs(session: AsyncSession):
    """Create default Job records if they don't exist."""
    logger.info("Checking for default jobs...")
    default_jobs = ["speedtest", "quotacheck", "speedtest_quotacheck"]

    for job_name in default_jobs:
        result = await session.execute(select(Job).where(Job.name == job_name))
        existing = result.scalar_one_or_none()
        if not existing:
            job = Job(
                name=job_name,
                description=None,
                created_at=cairo_now(),
                updated_at=cairo_now(),
            )
            session.add(job)
            logger.info(f"Default job '{job_name}' created.")
        else:
            logger.info(f"Default job '{job_name}' already exists.")

    await session.commit()
    logger.info("Default jobs setup completed.")


async def seed_default_data():
    """
    Seed the database with default data using async session.
    This function creates default records for ISP, TaskStatus, and Job tables.
    """
    logger.info("Starting default data seeding...")
    try:
        async with AsyncSession(async_engine) as session:
            await create_default_isp(session)
            await create_default_task_statuses(session)
            await create_default_jobs(session)
        logger.info("Default data seeding completed successfully.")
    except Exception as e:
        logger.error(f"Error during default data seeding: {e}")
        raise


# ------------------------------------------------------------------------------
# Main Orchestration Function
# ------------------------------------------------------------------------------
# This async function orchestrates the setup process:
# - Creates the database if needed (sync)
# - Creates tables if needed (sync)
# - Seeds default data asynchronously


async def setup_database() -> None:
    """
    Orchestrates the database setup process:
    - Create database (synchronous)
    - Create tables (synchronous)
    - Seed default values (asynchronous)
    """
    logger.info("Starting database setup process...")

    # Synchronous Steps
    create_database_if_not_exists()
    create_tables(sync_engine)  # Use the engine connected to the specific DB

    # Asynchronous seeding
    await seed_default_data()

    logger.info("Database setup process completed successfully.")
