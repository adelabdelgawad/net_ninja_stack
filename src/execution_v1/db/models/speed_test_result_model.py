import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio.session import AsyncSession

from db.model import SpeedTestResult

logger = logging.getLogger(__name__)


class SpeedTestResultModel:
    """Repository class for SpeedTestResult database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def read(
        self,
        line_id: Optional[int] = None,
        id: Optional[int] = None,
        process_id: Optional[str] = None,
    ) -> Optional[SpeedTestResult]:
        """
        Read a single SpeedTestResult record based on provided filters.

        Args:
            line_id: Optional line ID to filter by
            id: Optional speed test result ID to filter by
            process_id: Optional process ID to filter by

        Returns:
            SpeedTestResult object if found, None otherwise
        """
        try:
            statement = select(SpeedTestResult)

            if id is not None:
                statement = statement.where(SpeedTestResult.id == id)
            if line_id is not None:
                statement = statement.where(SpeedTestResult.line_id == line_id)
            if process_id is not None:
                statement = statement.where(
                    SpeedTestResult.process_id == process_id
                )

            result = await self.session.execute(statement)
            speed_test = result.scalar_one_or_none()

            if speed_test:
                logger.info(
                    f"Successfully retrieved SpeedTestResult with filters: "
                    f"id={id}, line_id={line_id}, process_id={process_id}"
                )
            else:
                logger.warning(
                    f"No SpeedTestResult found with filters: "
                    f"id={id}, line_id={line_id}, process_id={process_id}"
                )

            return speed_test

        except SQLAlchemyError as e:
            logger.error(
                f"Database error while reading SpeedTestResult: {str(e)}",
                exc_info=True,
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error while reading SpeedTestResult: {str(e)}",
                exc_info=True,
            )
            raise

    async def read_last_record(
        self, line_id: Optional[int] = None
    ) -> Optional[SpeedTestResult]:
        """
        Read the most recent SpeedTestResult record, optionally filtered by line_id.

        Args:
            line_id: Optional line ID to filter by

        Returns:
            Most recent SpeedTestResult object if found, None otherwise
        """
        try:
            statement = select(SpeedTestResult).order_by(
                desc(SpeedTestResult.created_date)
            )

            if line_id is not None:
                statement = statement.where(SpeedTestResult.line_id == line_id)

            statement = statement.limit(1)

            result = await self.session.execute(statement)
            speed_test = result.scalar_one_or_none()

            if speed_test:
                logger.info(
                    f"Successfully retrieved last SpeedTestResult for line_id={line_id}"
                )
            else:
                logger.warning(
                    f"No SpeedTestResult found for line_id={line_id}"
                )

            return speed_test

        except SQLAlchemyError as e:
            logger.error(
                f"Database error while reading last SpeedTestResult: {str(e)}",
                exc_info=True,
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error while reading last SpeedTestResult: {str(e)}",
                exc_info=True,
            )
            raise

    async def read_all(
        self, line_id: Optional[int] = None
    ) -> List[SpeedTestResult]:
        """
        Read all SpeedTestResult records, optionally filtered by line_id.

        Args:
            line_id: Optional line ID to filter by

        Returns:
            List of SpeedTestResult objects
        """
        try:
            statement = select(SpeedTestResult)

            if line_id is not None:
                statement = statement.where(SpeedTestResult.line_id == line_id)

            statement = statement.order_by(desc(SpeedTestResult.created_date))

            result = await self.session.execute(statement)
            speed_tests = result.scalars().all()

            logger.info(
                f"Successfully retrieved {len(speed_tests)} SpeedTestResult records "
                f"for line_id={line_id}"
            )

            return list(speed_tests)

        except SQLAlchemyError as e:
            logger.error(
                f"Database error while reading all SpeedTestResults: {str(e)}",
                exc_info=True,
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error while reading all SpeedTestResults: {str(e)}",
                exc_info=True,
            )
            raise

    async def create(self, speed_test: SpeedTestResult) -> SpeedTestResult:
        """
        Create a new SpeedTestResult record.

        Args:
            speed_test: SpeedTestResult object to create

        Returns:
            Created SpeedTestResult object with populated ID
        """
        try:
            self.session.add(speed_test)
            await self.session.commit()
            await self.session.refresh(speed_test)

            logger.info(
                f"Successfully created SpeedTestResult with id={speed_test.id}, "
                f"line_id={speed_test.line_id}, process_id={speed_test.process_id}"
            )

            return speed_test

        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(
                f"Database error while creating SpeedTestResult: {str(e)}",
                exc_info=True,
            )
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"Unexpected error while creating SpeedTestResult: {str(e)}",
                exc_info=True,
            )
            raise

    async def update(
        self, id: int, update_fields: Dict[str, Any]
    ) -> SpeedTestResult:
        """
        Update an existing SpeedTestResult record.

        Args:
            id: ID of the SpeedTestResult to update
            update_fields: Dictionary of fields to update

        Returns:
            Updated SpeedTestResult object

        Raises:
            ValueError: If SpeedTestResult with given ID is not found
        """
        try:
            statement = select(SpeedTestResult).where(SpeedTestResult.id == id)
            result = await self.session.execute(statement)
            speed_test = result.scalar_one_or_none()

            if not speed_test:
                error_msg = f"SpeedTestResult with id={id} not found"
                logger.error(error_msg)
                raise ValueError(error_msg)

            for field, value in update_fields.items():
                if hasattr(speed_test, field):
                    setattr(speed_test, field, value)
                else:
                    logger.warning(
                        f"Field '{field}' does not exist on SpeedTestResult model"
                    )

            self.session.add(speed_test)
            await self.session.commit()
            await self.session.refresh(speed_test)

            logger.info(
                f"Successfully updated SpeedTestResult with id={id}. "
                f"Updated fields: {list(update_fields.keys())}"
            )

            return speed_test

        except ValueError:
            raise
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(
                f"Database error while updating SpeedTestResult: {str(e)}",
                exc_info=True,
            )
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"Unexpected error while updating SpeedTestResult: {str(e)}",
                exc_info=True,
            )
            raise
