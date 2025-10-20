import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select

from api.services.dependancies import SessionDep
from api.services.http_schemas import (EmailCreate, EmailResponse,
                                       EmailSummary, EmailUpdate)
from db.models import Email, EmailType

router = APIRouter(prefix="/emails", tags=["Emails"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=int)
async def create_email(
    email_data: EmailCreate,
    session: SessionDep,
):
    """Create a new email record with type association.

    This endpoint creates a new email record associated with a specific email type.
    The email type must exist in the system before creating email records. Email
    addresses are validated for proper format during creation.

    Args:
        email_data: EmailCreate model containing recipient and email type.
        session: Database session dependency for database operations.

    Returns:
        int: The ID of the newly created email record.

    Example:
        POST /emails/
        {
            "recipient": "user@example.com",
            "email_type_id": 1
        }
        Returns: 3 (email ID)
    """
    try:
        logger.info(f"Creating email for recipient {email_data.recipient}")

        # Verify email type exists
        type_stmt = select(EmailType).where(
            EmailType.id == email_data.email_type_id)
        type_result = await session.execute(type_stmt)
        email_type = type_result.scalar_one_or_none()

        if not email_type:
            logger.error(f"Email type {email_data.email_type_id} not found")
            raise HTTPException(
                status_code=404,
                detail=f"Email type with id {email_data.email_type_id} not found"
            )

        # Create email
        email = Email(**email_data.model_dump())
        session.add(email)
        await session.commit()
        await session.refresh(email)

        logger.info(
            f"Successfully created email {email.id} for {email.recipient}")
        return email.id

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating email: {str(e)}")
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while creating email"
        )


@router.get("/{email_id}", response_model=EmailResponse)
async def get_email(
    email_id: int,
    session: SessionDep,
):
    """Retrieve a specific email by ID with type information.

    This endpoint fetches detailed information about an email record including
    its associated email type. The response includes all email configuration
    data needed for notification management.

    Args:
        email_id: Integer ID of the email to retrieve.
        session: Database session dependency for database operations.

    Returns:
        EmailResponse: Complete email information including type details.

    Example:
        GET /emails/1
        Returns email details with type information
    """
    try:
        logger.info(f"Retrieving email {email_id}")

        stmt = select(Email).where(Email.id == email_id)
        result = await session.execute(stmt)
        email = result.scalar_one_or_none()

        if not email:
            logger.warning(f"Email {email_id} not found")
            raise HTTPException(
                status_code=404,
                detail=f"Email with id {email_id} not found"
            )

        logger.info(f"Successfully retrieved email {email_id}")
        return email

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving email {email_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while retrieving email"
        )


@router.put("/{email_id}")
async def update_email(
    email_id: int,
    email_update: EmailUpdate,
    session: SessionDep,
):
    """Update an existing email record.

    This endpoint updates the configuration of an existing email record.
    The recipient address and email type can be modified while maintaining
    referential integrity with email types.

    Args:
        email_id: Integer ID of the email to update.
        email_update: EmailUpdate model containing fields to update.
        session: Database session dependency for database operations.

    Returns:
        dict: Success message confirming the email update.

    Example:
        PUT /emails/1
        {
            "recipient": "newemail@example.com",
            "email_type_id": 2
        }
        Returns: {"message": "Email updated successfully"}
    """
    try:
        logger.info(f"Updating email {email_id}")

        stmt = select(Email).where(Email.id == email_id)
        result = await session.execute(stmt)
        email = result.scalar_one_or_none()

        if not email:
            logger.warning(f"Email {email_id} not found for update")
            raise HTTPException(
                status_code=404,
                detail=f"Email with id {email_id} not found"
            )

        # Update email with provided data
        if email_update.recipient:
            email.recipient = email_update.recipient
        if email_update.email_type_id:
            email.email_type_id = email_update.email_type_id

        session.add(email)
        await session.commit()

        logger.info(f"Successfully updated email {email_id}")
        return {"message": "Email updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating email {email_id}: {str(e)}")
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while updating email"
        )


@router.delete("/{email_id}")
async def delete_email(
    email_id: int,
    session: SessionDep,
):
    """Delete an email record.

    This endpoint permanently removes an email record from the system.
    This operation cannot be undone and should be used when email
    addresses are no longer valid or needed.

    Args:
        email_id: Integer ID of the email to delete.
        session: Database session dependency for database operations.

    Returns:
        dict: Success message confirming the email deletion.

    Example:
        DELETE /emails/1
        Returns: {"message": "Email deleted successfully"}
    """
    try:
        logger.info(f"Deleting email {email_id}")

        stmt = select(Email).where(Email.id == email_id)
        result = await session.execute(stmt)
        email = result.scalar_one_or_none()

        if not email:
            logger.warning(f"Email {email_id} not found for deletion")
            raise HTTPException(
                status_code=404,
                detail=f"Email with id {email_id} not found"
            )

        await session.delete(email)
        await session.commit()

        logger.info(f"Successfully deleted email {email_id}")
        return {"message": "Email deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting email {email_id}: {str(e)}")
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while deleting email"
        )


@router.get("/", response_model=List[EmailSummary])
async def list_emails(
    session: SessionDep,
    email_type_id: Optional[int] = Query(
        None, description="Filter emails by type ID", ge=1
    ),
    recipient_contains: Optional[str] = Query(
        None, description="Filter emails by recipient content", max_length=100
    ),
    size: Optional[int] = Query(
        50, ge=1, le=1000, description="Number of emails to return"
    ),
    offset: int = Query(
        0, ge=0, description="Number of emails to skip for pagination"
    ),
):
    """Retrieve a list of emails with optional filtering.

    This endpoint returns a paginated list of emails with optional filtering
    by email type or recipient pattern. The response includes summary
    information for each email suitable for management interfaces.

    Args:
        session: Database session dependency for database operations.
        email_type_id: Optional integer to filter emails by specific type.
        recipient_contains: Optional string to filter emails by recipient pattern.
        size: Optional integer specifying the maximum number of emails to return.
        offset: Integer specifying the number of emails to skip for pagination.

    Returns:
        List[EmailSummary]: List of email summaries with basic information.

    Example:
        GET /emails/?email_type_id=1&size=10&offset=0
        Returns up to 10 emails of type 1.
    """
    try:
        logger.info(
            f"Listing emails with filters: type_id={email_type_id}, recipient_contains={recipient_contains}, size={size}, offset={offset}")

        stmt = select(Email)

        if email_type_id:
            stmt = stmt.where(Email.email_type_id == email_type_id)

        if recipient_contains:
            stmt = stmt.where(Email.recipient.contains(recipient_contains))

        stmt = stmt.offset(offset).limit(size)

        result = await session.execute(stmt)
        emails = result.scalars().all()

        logger.info(f"Successfully retrieved {len(emails)} emails")
        return emails

    except Exception as e:
        logger.error(f"Error listing emails: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while listing emails"
        )
