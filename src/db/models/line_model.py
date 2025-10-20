import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload

from db.model import Line

logger = logging.getLogger(__name__)


class LineModel:
    """Repository class for Line database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def read(
        self,
        id: Optional[int] = None,
        line_number: Optional[str] = None,
        isp_id: Optional[int] = None,
    ) -> Optional[Line]:
        """
        Read a single Line record based on provided filters.

        Args:
            id: Optional line ID to filter by
            line_number: Optional line number to filter by
            isp_id: Optional ISP ID to filter by

        Returns:
            Line object if found, None otherwise
        """
        try:
            statement = select(Line)

            if id is not None:
                statement = statement.where(Line.id == id)
            if line_number is not None:
                statement = statement.where(Line.line_number == line_number)
            if isp_id is not None:
                statement = statement.where(Line.isp_id == isp_id)

            result = await self.session.execute(statement)
            line = result.scalar_one_or_none()

            if line:
                logger.info(
                    f"Successfully retrieved Line with filters: "
                    f"id={id}, line_number={line_number}, isp_id={isp_id}"
                )
            else:
                logger.warning(
                    f"No Line found with filters: "
                    f"id={id}, line_number={line_number}, isp_id={isp_id}"
                )

            return line

        except SQLAlchemyError as e:
            logger.error(
                f"Database error while reading Line: {str(e)}", exc_info=True
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error while reading Line: {str(e)}", exc_info=True
            )
            raise

    async def read_last_record(
        self, isp_id: Optional[int] = None
    ) -> Optional[Line]:
        """
        Read the most recent Line record, optionally filtered by isp_id.

        Args:
            isp_id: Optional ISP ID to filter by

        Returns:
            Most recent Line object if found, None otherwise
        """
        try:
            statement = select(Line).order_by(desc(Line.id))

            if isp_id is not None:
                statement = statement.where(Line.isp_id == isp_id)

            statement = statement.limit(1)

            result = await self.session.execute(statement)
            line = result.scalar_one_or_none()

            if line:
                logger.info(
                    f"Successfully retrieved last Line for isp_id={isp_id}"
                )
            else:
                logger.warning(f"No Line found for isp_id={isp_id}")

            return line

        except SQLAlchemyError as e:
            logger.error(
                f"Database error while reading last Line: {str(e)}",
                exc_info=True,
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error while reading last Line: {str(e)}",
                exc_info=True,
            )
            raise

    async def read_all(self, isp_id: Optional[int] = None) -> List[Line]:
        """
        Read all Line records with eager-loaded ISP relationship, optionally filtered by isp_id.

        Args:
            isp_id: Optional ISP ID to filter by

        Returns:
            List of Line objects with ISP data loaded
        """
        try:
            # Use eager loading to avoid N+1 queries
            statement = select(Line).options(selectinload(Line.isp))

            if isp_id is not None:
                statement = statement.where(Line.isp_id == isp_id)

            statement = statement.order_by(Line.id)

            result = await self.session.execute(statement)
            lines = result.scalars().all()

            logger.info(
                f"Successfully retrieved {len(lines)} Line records for isp_id={isp_id}"
            )

            return list(lines)

        except SQLAlchemyError as e:
            logger.error(
                f"Database error while reading all Lines: {str(e)}",
                exc_info=True,
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error while reading all Lines: {str(e)}",
                exc_info=True,
            )
            raise

    async def create(self, line: Line) -> Line:
        """
        Create a new Line record.

        Args:
            line: Line object to create

        Returns:
            Created Line object with populated ID

        Raises:
            ValueError: If validation fails or constraint is violated
        """
        try:
            self.session.add(line)
            await self.session.commit()
            await self.session.refresh(line)

            logger.info(
                f"Successfully created Line with id={line.id}, "
                f"line_number={line.line_number}, name={line.name}"
            )

            return line

        except IntegrityError as e:
            await self.session.rollback()
            error_msg = (
                f"Integrity constraint violation while creating Line: {str(e)}"
            )
            logger.error(error_msg, exc_info=True)
            raise ValueError(error_msg)
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(
                f"Database error while creating Line: {str(e)}", exc_info=True
            )
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"Unexpected error while creating Line: {str(e)}",
                exc_info=True,
            )
            raise

    async def update(self, id: int, update_fields: Dict[str, Any]) -> Line:
        """
        Update an existing Line record.

        Args:
            id: ID of the Line to update
            update_fields: Dictionary of fields to update

        Returns:
            Updated Line object

        Raises:
            ValueError: If Line with given ID is not found or constraint violated
        """
        try:
            statement = select(Line).where(Line.id == id)
            result = await self.session.execute(statement)
            line = result.scalar_one_or_none()

            if not line:
                error_msg = f"Line with id={id} not found"
                logger.error(error_msg)
                raise ValueError(error_msg)

            for field, value in update_fields.items():
                if hasattr(line, field):
                    setattr(line, field, value)
                else:
                    logger.warning(
                        f"Field '{field}' does not exist on Line model"
                    )

            self.session.add(line)
            await self.session.commit()
            await self.session.refresh(line)

            logger.info(
                f"Successfully updated Line with id={id}. "
                f"Updated fields: {list(update_fields.keys())}"
            )

            return line

        except ValueError:
            raise
        except IntegrityError as e:
            await self.session.rollback()
            error_msg = (
                f"Integrity constraint violation while updating Line: {str(e)}"
            )
            logger.error(error_msg, exc_info=True)
            raise ValueError(error_msg)
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(
                f"Database error while updating Line: {str(e)}", exc_info=True
            )
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"Unexpected error while updating Line: {str(e)}",
                exc_info=True,
            )
            raise

    async def delete(self, id: int) -> bool:
        """
        Delete a Line record.

        Args:
            id: ID of the Line to delete

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If Line with given ID is not found
        """
        try:
            statement = select(Line).where(Line.id == id)
            result = await self.session.execute(statement)
            line = result.scalar_one_or_none()

            if not line:
                error_msg = f"Line with id={id} not found"
                logger.error(error_msg)
                raise ValueError(error_msg)

            await self.session.delete(line)
            await self.session.commit()

            logger.info(f"Successfully deleted Line with id={id}")
            return True

        except ValueError:
            raise
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(
                f"Database error while deleting Line: {str(e)}", exc_info=True
            )
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"Unexpected error while deleting Line: {str(e)}",
                exc_info=True,
            )
            raise
