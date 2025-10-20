import asyncio

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import SQLModel

from core.config import settings

# Get the actual password value from SecretStr
db_password = settings.database.password.get_secret_value()

# URL for connecting *without* specifying a database (for initial creation check)
BASE_SYNC_URL = f"mysql+pymysql://{settings.database.username}:{db_password}@{settings.database.server}"
# URL for asynchronous operations *on the specific database* (table operations)
ASYNC_DATABASE_URL = f"mysql+aiomysql://{settings.database.username}:{db_password}@{settings.database.server}/{settings.database.name}?charset=utf8mb4"


async def drop_tables(engine: AsyncEngine):
    print("Dropping all tables...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.drop_all)
        print("All tables dropped.")
    except Exception as e:
        print(f"Error dropping tables: {e}")


def drop_database():
    print(f"Dropping database '{settings.database.name}'...")
    try:
        engine = create_engine(BASE_SYNC_URL, echo=False, future=True)
        with engine.connect() as conn:
            conn.execute(text(f"DROP DATABASE IF EXISTS {settings.database.name}"))
            conn.commit()  # Add commit for DDL operations
        print(f"Database '{settings.database.name}' deleted.")
    except Exception as e:
        print(f"Error deleting database: {e}")


async def main(delete_db: bool = False):
    engine = create_async_engine(ASYNC_DATABASE_URL, echo=False, future=True)
    await drop_tables(engine)
    await engine.dispose()
    if delete_db:
        drop_database()


if __name__ == "__main__":
    print("Starting database cleanup...")
    delete_db = input("Delete the entire database? (yes/no): ").strip().lower() == "yes"
    asyncio.run(main(delete_db))
    print("Cleanup complete.")
