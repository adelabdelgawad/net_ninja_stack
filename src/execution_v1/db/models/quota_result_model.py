import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio.session import AsyncSession

from db.model import QuotaResult

logger = logging.getLogger(__name__)


class QuotaResultModel:
    """Repository class for QuotaResult database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def read(
        self,
        line_id: Optional[int] = None,
        id: Optional[int] = None,
        process_id: Optional[str] = None,
    ) -> Optional[QuotaResult]:
        """
        Read a single QuotaResult record based on provided filters.

        Args:
            line_id: Optional line ID to filter by
            id: Optional quota result ID to filter by
            process_id: Optional process ID to filter by

        Returns:
            QuotaResult object if found, None otherwise
        """
        try:
            statement = select(QuotaResult)

            if id is not None:
                statement = statement.where(QuotaResult.id == id)
            if line_id is not None:
                statement = statement.where(QuotaResult.line_id == line_id)
            if process_id is not None:
                statement = statement.where(
                    QuotaResult.process_id == process_id
                )

            result = await self.session.execute(statement)
            quota_result = result.scalar_one_or_none()

            if quota_result:
                logger.info(
                    f"Successfully retrieved QuotaResult with filters: "
                    f"id={id}, line_id={line_id}, process_id={process_id}"
                )
            else:
                logger.warning(
                    f"No QuotaResult found with filters: "
                    f"id={id}, line_id={line_id}, process_id={process_id}"
                )

            return quota_result

        except SQLAlchemyError as e:
            logger.error(
                f"Database error while reading QuotaResult: {str(e)}",
                exc_info=True,
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error while reading QuotaResult: {str(e)}",
                exc_info=True,
            )
            raise

    async def read_last_record(
        self, line_id: Optional[int] = None
    ) -> Optional[QuotaResult]:
        """
        Read the most recent QuotaResult record, optionally filtered by line_id.

        Args:
            line_id: Optional line ID to filter by

        Returns:
            Most recent QuotaResult object if found, None otherwise
        """
        try:
            statement = select(QuotaResult).order_by(
                desc(QuotaResult.created_date)
            )

            if line_id is not None:
                statement = statement.where(QuotaResult.line_id == line_id)

            statement = statement.limit(1)

            result = await self.session.execute(statement)
            quota_result = result.scalar_one_or_none()

            if quota_result:
                logger.info(
                    f"Successfully retrieved last QuotaResult for line_id={line_id}"
                )
            else:
                logger.warning(f"No QuotaResult found for line_id={line_id}")

            return quota_result

        except SQLAlchemyError as e:
            logger.error(
                f"Database error while reading last QuotaResult: {str(e)}",
                exc_info=True,
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error while reading last QuotaResult: {str(e)}",
                exc_info=True,
            )
            raise

    async def read_all(
        self, line_id: Optional[int] = None
    ) -> List[QuotaResult]:
        """
        Read all QuotaResult records, optionally filtered by line_id.

        Args:
            line_id: Optional line ID to filter by

        Returns:
            List of QuotaResult objects
        """
        try:
            statement = select(QuotaResult)

            if line_id is not None:
                statement = statement.where(QuotaResult.line_id == line_id)

            statement = statement.order_by(desc(QuotaResult.created_date))

            result = await self.session.execute(statement)
            quota_results = result.scalars().all()

            logger.info(
                f"Successfully retrieved {len(quota_results)} QuotaResult records "
                f"for line_id={line_id}"
            )

            return list(quota_results)

        except SQLAlchemyError as e:
            logger.error(
                f"Database error while reading all QuotaResults: {str(e)}",
                exc_info=True,
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error while reading all QuotaResults: {str(e)}",
                exc_info=True,
            )
            raise

    async def create(self, quota_result: QuotaResult) -> QuotaResult:
        """
        Create a new QuotaResult record.

        Args:
            quota_result: QuotaResult object to create

        Returns:
            Created QuotaResult object with populated ID
        """
        try:
            self.session.add(quota_result)
            await self.session.commit()
            await self.session.refresh(quota_result)

            logger.info(
                f"Successfully created QuotaResult with id={quota_result.id}, "
                f"line_id={quota_result.line_id}, process_id={quota_result.process_id}"
            )

            return quota_result

        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(
                f"Database error while creating QuotaResult: {str(e)}",
                exc_info=True,
            )
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"Unexpected error while creating QuotaResult: {str(e)}",
                exc_info=True,
            )
            raise

    async def update(
        self, id: int, update_fields: Dict[str, Any]
    ) -> QuotaResult:
        """
        Update an existing QuotaResult record.

        Args:
            id: ID of the QuotaResult to update
            update_fields: Dictionary of fields to update

        Returns:
            Updated QuotaResult object

        Raises:
            ValueError: If QuotaResult with given ID is not found
        """
        try:
            statement = select(QuotaResult).where(QuotaResult.id == id)
            result = await self.session.execute(statement)
            quota_result = result.scalar_one_or_none()

            if not quota_result:
                error_msg = f"QuotaResult with id={id} not found"
                logger.error(error_msg)
                raise ValueError(error_msg)

            for field, value in update_fields.items():
                if hasattr(quota_result, field):
                    setattr(quota_result, field, value)
                else:
                    logger.warning(
                        f"Field '{field}' does not exist on QuotaResult model"
                    )

            self.session.add(quota_result)
            await self.session.commit()
            await self.session.refresh(quota_result)

            logger.info(
                f"Successfully updated QuotaResult with id={id}. "
                f"Updated fields: {list(update_fields.keys())}"
            )

            return quota_result

        except ValueError:
            raise
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(
                f"Database error while updating QuotaResult: {str(e)}",
                exc_info=True,
            )
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"Unexpected error while updating QuotaResult: {str(e)}",
                exc_info=True,
            )
            raise
