import inspect
import asyncio
from contextvars import ContextVar
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from db.model import Log
from db.database import engine
from typing import Optional


class Logger:
    _instance = None
    _session_factory = None
    _lock = asyncio.Lock()
    _context_process_id: ContextVar[Optional[str]] = ContextVar(
        "process_id", default=None
    )

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            asyncio.run(cls._initialize_session())
        return cls._instance

    @classmethod
    async def _initialize_session(cls):
        async with cls._lock:
            if cls._session_factory is None:
                cls._session_factory = async_sessionmaker(
                    engine, expire_on_commit=False
                )

    @classmethod
    async def _get_session(cls) -> AsyncSession:
        if cls._session_factory is None:
            await cls._initialize_session()
        return cls._session_factory()

    async def _log(self, process_id, level_name, message):
        frame = inspect.currentframe().f_back
        function = frame.f_code.co_name

        log_entry = Log(
            process_id=process_id,
            function=function,
            level=level_name,
            message=message,
        )
        try:
            async with await self._get_session() as session:
                async with session.begin():
                    session.add(log_entry)
        except SQLAlchemyError as e:
            # Handle logging failure (optional: print to stderr or another logging mechanism)
            print(f"Failed to log message: {e}")

    async def info(self, process_id, message):
        await self._log(process_id, "INFO", message)

    async def warning(self, process_id, message):
        await self._log(process_id, "WARNING", message)

    async def error(self, process_id, message):
        await self._log(process_id, "ERROR", message)

    async def debug(self, process_id, message):
        await self._log(process_id, "DEBUG", message)


# Usage example
logger = Logger()


async def main():
    logger.set_process_id("12345")
    await logger.info("This is an info message")
    await logger.error("This is an error message")


if __name__ == "__main__":
    asyncio.run(main())
