import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio.session import AsyncSession

from db.model import Email

logger = logging.getLogger(__name__)


class EmailModel:
    """Repository class for Email database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def read(
        self,
        id: Optional[int] = None,
        recipient: Optional[str] = None,
    ) -> Optional[Email]:
        """
        Read a single Email record based on provided filters.

        Args:
            id: Optional email ID to filter by
            recipient: Optional recipient email to filter by

        Returns:
            Email object if found, None otherwise
        """
        try:
            statement = select(Email)

            if id is not None:
                statement = statement.where(Email.id == id)
            if recipient is not None:
                statement = statement.where(Email.recipient == recipient)

            result = await self.session.execute(statement)
            email = result.scalar_one_or_none()

            if email:
                logger.info(
                    f"Successfully retrieved Email with filters: "
                    f"id={id}, recipient={recipient}"
                )
            else:
                logger.warning(
                    f"No Email found with filters: id={id}, recipient={recipient}"
                )

            return email

        except SQLAlchemyError as e:
            logger.error(
                f"Database error while reading Email: {str(e)}", exc_info=True
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error while reading Email: {str(e)}",
                exc_info=True,
            )
            raise

    async def read_last_record(self) -> Optional[Email]:
        """
        Read the most recent Email record.

        Returns:
            Most recent Email object if found, None otherwise
        """
        try:
            statement = select(Email).order_by(desc(Email.id)).limit(1)

            result = await self.session.execute(statement)
            email = result.scalar_one_or_none()

            if email:
                logger.info("Successfully retrieved last Email")
            else:
                logger.warning("No Email found")

            return email

        except SQLAlchemyError as e:
            logger.error(
                f"Database error while reading last Email: {str(e)}",
                exc_info=True,
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error while reading last Email: {str(e)}",
                exc_info=True,
            )
            raise

    async def read_all(self) -> List[Email]:
        """
        Read all Email records.

        Returns:
            List of Email objects
        """
        try:
            statement = select(Email).order_by(Email.id)

            result = await self.session.execute(statement)
            emails = result.scalars().all()

            logger.info(f"Successfully retrieved {len(emails)} Email records")

            return list(emails)

        except SQLAlchemyError as e:
            logger.error(
                f"Database error while reading all Emails: {str(e)}",
                exc_info=True,
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error while reading all Emails: {str(e)}",
                exc_info=True,
            )
            raise

    async def create(self, email: Email) -> Email:
        """
        Create a new Email record.

        Args:
            email: Email object to create

        Returns:
            Created Email object with populated ID
        """
        try:
            self.session.add(email)
            await self.session.commit()
            await self.session.refresh(email)

            logger.info(
                f"Successfully created Email with id={email.id}, "
                f"recipient={email.recipient}"
            )

            return email

        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(
                f"Database error while creating Email: {str(e)}", exc_info=True
            )
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"Unexpected error while creating Email: {str(e)}",
                exc_info=True,
            )
            raise

    async def update(self, id: int, update_fields: Dict[str, Any]) -> Email:
        """
        Update an existing Email record.

        Args:
            id: ID of the Email to update
            update_fields: Dictionary of fields to update

        Returns:
            Updated Email object

        Raises:
            ValueError: If Email with given ID is not found
        """
        try:
            statement = select(Email).where(Email.id == id)
            result = await self.session.execute(statement)
            email = result.scalar_one_or_none()

            if not email:
                error_msg = f"Email with id={id} not found"
                logger.error(error_msg)
                raise ValueError(error_msg)

            for field, value in update_fields.items():
                if hasattr(email, field):
                    setattr(email, field, value)
                else:
                    logger.warning(
                        f"Field '{field}' does not exist on Email model"
                    )

            self.session.add(email)
            await self.session.commit()
            await self.session.refresh(email)

            logger.info(
                f"Successfully updated Email with id={id}. "
                f"Updated fields: {list(update_fields.keys())}"
            )

            return email

        except ValueError:
            raise
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(
                f"Database error while updating Email: {str(e)}", exc_info=True
            )
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"Unexpected error while updating Email: {str(e)}",
                exc_info=True,
            )
            raise

    async def delete(self, id: int) -> bool:
        """
        Delete an Email record.

        Args:
            id: ID of the Email to delete

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If Email with given ID is not found
        """
        try:
            statement = select(Email).where(Email.id == id)
            result = await self.session.execute(statement)
            email = result.scalar_one_or_none()

            if not email:
                error_msg = f"Email with id={id} not found"
                logger.error(error_msg)
                raise ValueError(error_msg)

            await self.session.delete(email)
            await self.session.commit()

            logger.info(f"Successfully deleted Email with id={id}")
            return True

        except ValueError:
            raise
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(
                f"Database error while deleting Email: {str(e)}", exc_info=True
            )
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"Unexpected error while deleting Email: {str(e)}",
                exc_info=True,
            )
            raise
