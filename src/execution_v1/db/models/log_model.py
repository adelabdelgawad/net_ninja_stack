import logging
from typing import Optional

from sqlalchemy import desc, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio.session import AsyncSession

from db.model import Log

logger = logging.getLogger(__name__)


class LogModel:
    """Repository class for Log database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def read(
        self,
        id: Optional[int] = None,
        process_id: Optional[str] = None,
        level: Optional[str] = None,
        function: Optional[str] = None,
    ) -> Optional[Log]:
        """
        Read a single Log record based on provided filters.

        Args:
            id: Optional log ID to filter by
            process_id: Optional process ID to filter by
            level: Optional log level to filter by
            function: Optional function name to filter by

        Returns:
            Log object if found, None otherwise
        """
        try:
            statement = select(Log)

            if id is not None:
                statement = statement.where(Log.id == id)
            if process_id is not None:
                statement = statement.where(Log.process_id == process_id)
            if level is not None:
                statement = statement.where(Log.level == level)
            if function is not None:
                statement = statement.where(Log.function == function)

            result = await self.session.execute(statement)
            log = result.scalar_one_or_none()

            if log:
                logger.info(
                    f"Successfully retrieved Log with filters: id={id}, "
                    f"process_id={process_id}, level={level}, function={function}"
                )
            else:
                logger.warning(
                    f"No Log found with filters: id={id}, process_id={process_id}, "
                    f"level={level}, function={function}"
                )

            return log

        except SQLAlchemyError as e:
            logger.error(
                f"Database error while reading Log: {str(e)}", exc_info=True
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error while reading Log: {str(e)}", exc_info=True
            )
            raise

    async def read_last_record(
        self, process_id: Optional[str] = None
    ) -> Optional[Log]:
        """
        Read the most recent Log record, optionally filtered by process_id.

        Args:
            process_id: Optional process ID to filter by

        Returns:
            Most recent Log object if found, None otherwise
        """
        try:
            statement = select(Log).order_by(desc(Log.created_date))

            if process_id is not None:
                statement = statement.where(Log.process_id == process_id)

            statement = statement.limit(1)

            result = await self.session.execute(statement)
            log = result.scalar_one_or_none()

            if log:
                logger.info(
                    f"Successfully retrieved last Log for process_id={process_id}"
                )
            else:
                logger.warning(f"No Log found for process_id={process_id}")

            return log

        except SQLAlchemyError as e:
            logger.error(
                f"Database error while reading last: {str(e)}", exc_info=True
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error while reading Log: {str(e)}", exc_info=True
            )
            raise
