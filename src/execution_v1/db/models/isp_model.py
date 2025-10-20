import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio.session import AsyncSession

from db.model import ISP

logger = logging.getLogger(__name__)


class ISPModel:
    """Repository class for ISP database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def read(
        self,
        id: Optional[int] = None,
        name: Optional[str] = None,
    ) -> Optional[ISP]:
        """
        Read a single ISP record based on provided filters.

        Args:
            id: Optional ISP ID to filter by
            name: Optional ISP name to filter by

        Returns:
            ISP object if found, None otherwise
        """
        try:
            statement = select(ISP)

            if id is not None:
                statement = statement.where(ISP.id == id)
            if name is not None:
                statement = statement.where(ISP.name == name)

            result = await self.session.execute(statement)
            isp = result.scalar_one_or_none()

            if isp:
                logger.info(
                    f"Successfully retrieved ISP with filters: id={id}, name={name}"
                )
            else:
                logger.warning(
                    f"No ISP found with filters: id={id}, name={name}"
                )

            return isp

        except SQLAlchemyError as e:
            logger.error(
                f"Database error while reading ISP: {str(e)}", exc_info=True
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error while reading ISP: {str(e)}", exc_info=True
            )
            raise

    async def read_last_record(self) -> Optional[ISP]:
        """
        Read the most recent ISP record.

        Returns:
            Most recent ISP object if found, None otherwise
        """
        try:
            statement = select(ISP).order_by(desc(ISP.id)).limit(1)

            result = await self.session.execute(statement)
            isp = result.scalar_one_or_none()

            if isp:
                logger.info("Successfully retrieved last ISP")
            else:
                logger.warning("No ISP found")

            return isp

        except SQLAlchemyError as e:
            logger.error(
                f"Database error while reading last ISP: {str(e)}",
                exc_info=True,
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error while reading last ISP: {str(e)}",
                exc_info=True,
            )
            raise

    async def read_all(self) -> List[ISP]:
        """
        Read all ISP records.

        Returns:
            List of ISP objects
        """
        try:
            statement = select(ISP).order_by(ISP.name)

            result = await self.session.execute(statement)
            isps = result.scalars().all()

            logger.info(f"Successfully retrieved {len(isps)} ISP records")

            return list(isps)

        except SQLAlchemyError as e:
            logger.error(
                f"Database error while reading all ISPs: {str(e)}",
                exc_info=True,
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error while reading all ISPs: {str(e)}",
                exc_info=True,
            )
            raise

    async def create(self, isp: ISP) -> ISP:
        """
        Create a new ISP record.

        Args:
            isp: ISP object to create

        Returns:
            Created ISP object with populated ID

        Raises:
            ValueError: If ISP name already exists (unique constraint)
        """
        try:
            self.session.add(isp)
            await self.session.commit()
            await self.session.refresh(isp)

            logger.info(
                f"Successfully created ISP with id={isp.id}, name={isp.name}"
            )

            return isp

        except IntegrityError as e:
            await self.session.rollback()
            if "unique" in str(e).lower() or "name" in str(e).lower():
                error_msg = f"ISP with name '{isp.name}' already exists"
                logger.error(error_msg, exc_info=True)
                raise ValueError(error_msg)
            else:
                logger.error(
                    f"Integrity constraint violation while creating ISP: {str(e)}",
                    exc_info=True,
                )
                raise ValueError(f"Database constraint violation: {str(e)}")
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(
                f"Database error while creating ISP: {str(e)}", exc_info=True
            )
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"Unexpected error while creating ISP: {str(e)}",
                exc_info=True,
            )
            raise

    async def update(self, id: int, update_fields: Dict[str, Any]) -> ISP:
        """
        Update an existing ISP record.

        Args:
            id: ID of the ISP to update
            update_fields: Dictionary of fields to update

        Returns:
            Updated ISP object

        Raises:
            ValueError: If ISP with given ID is not found or name constraint violated
        """
        try:
            statement = select(ISP).where(ISP.id == id)
            result = await self.session.execute(statement)
            isp = result.scalar_one_or_none()

            if not isp:
                error_msg = f"ISP with id={id} not found"
                logger.error(error_msg)
                raise ValueError(error_msg)

            for field, value in update_fields.items():
                if hasattr(isp, field):
                    setattr(isp, field, value)
                else:
                    logger.warning(
                        f"Field '{field}' does not exist on ISP model"
                    )

            self.session.add(isp)
            await self.session.commit()
            await self.session.refresh(isp)

            logger.info(
                f"Successfully updated ISP with id={id}. "
                f"Updated fields: {list(update_fields.keys())}"
            )

            return isp

        except ValueError:
            raise
        except IntegrityError as e:
            await self.session.rollback()
            if "unique" in str(e).lower() or "name" in str(e).lower():
                error_msg = (
                    f"ISP name must be unique. Constraint violation: {str(e)}"
                )
                logger.error(error_msg, exc_info=True)
                raise ValueError(error_msg)
            else:
                logger.error(
                    f"Integrity constraint violation while updating ISP: {str(e)}",
                    exc_info=True,
                )
                raise ValueError(f"Database constraint violation: {str(e)}")
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(
                f"Database error while updating ISP: {str(e)}", exc_info=True
            )
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"Unexpected error while updating ISP: {str(e)}",
                exc_info=True,
            )
            raise

    async def delete(self, id: int) -> bool:
        """
        Delete an ISP record.

        Args:
            id: ID of the ISP to delete

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If ISP with given ID is not found
        """
        try:
            statement = select(ISP).where(ISP.id == id)
            result = await self.session.execute(statement)
            isp = result.scalar_one_or_none()

            if not isp:
                error_msg = f"ISP with id={id} not found"
                logger.error(error_msg)
                raise ValueError(error_msg)

            await self.session.delete(isp)
            await self.session.commit()

            logger.info(f"Successfully deleted ISP with id={id}")
            return True

        except ValueError:
            raise
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(
                f"Database error while deleting ISP: {str(e)}", exc_info=True
            )
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"Unexpected error while deleting ISP: {str(e)}",
                exc_info=True,
            )
            raise
