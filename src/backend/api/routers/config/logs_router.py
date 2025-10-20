import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select

from api.services.dependancies import SessionDep
from api.services.http_schemas import LogResponse, LogSummary
from db.models import Log, Process

router = APIRouter(prefix="/logs", tags=["Logs"])
logger = logging.getLogger(__name__)


@router.get("/{process_id}", response_model=List[LogResponse])
async def get_logs_by_process(
    process_id: int,
    session: SessionDep,
):
    """Retrieve all log entries for a specific process.

    This endpoint fetches all log entries associated with a specific process ID.
    The response includes complete log information with timestamps ordered by
    creation time for easy monitoring and debugging.

    Args:
        process_id: Integer ID of the process to retrieve logs for.
        session: Database session dependency for database operations.

    Returns:
        List[LogResponse]: List of all log entries for the specified process.

    Example:
        GET /logs/1
        Returns all log entries for process with ID 1
    """
    try:
        logger.info(f"Retrieving logs for process {process_id}")

        # Verify process exists
        process_stmt = select(Process).where(Process.id == process_id)
        process_result = await session.execute(process_stmt)
        process = process_result.scalar_one_or_none()

        if not process:
            logger.warning(f"Process {process_id} not found")
            raise HTTPException(
                status_code=404,
                detail=f"Process with id {process_id} not found"
            )

        # Get all logs for the process
        stmt = select(Log).where(Log.process_id ==
                                 process_id).order_by(Log.timestamp.desc())
        result = await session.execute(stmt)
        log_entries = result.scalars().all()

        logger.info(
            f"Successfully retrieved {len(log_entries)} logs for process {process_id}")
        return log_entries

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error retrieving logs for process {process_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while retrieving logs"
        )


@router.get("/", response_model=List[LogSummary])
async def list_logs(
    session: SessionDep,
    process_id: Optional[int] = Query(
        None, description="Filter logs by process ID", ge=1
    ),
    message_contains: Optional[str] = Query(
        None, description="Filter logs by message content", max_length=100
    ),
    from_date: Optional[datetime] = Query(
        None, description="Filter logs from this date"
    ),
    to_date: Optional[datetime] = Query(
        None, description="Filter logs until this date"
    ),
    size: Optional[int] = Query(
        50, ge=1, le=1000, description="Number of logs to return"
    ),
    offset: int = Query(
        0, ge=0, description="Number of logs to skip for pagination"
    ),
):
    """Retrieve a list of log entries with optional filtering.

    This endpoint returns a paginated list of log entries with optional filtering
    by process, message content, or date range. The response includes summary
    information for each log entry suitable for monitoring interfaces.

    Args:
        session: Database session dependency for database operations.
        process_id: Optional integer to filter logs by specific process.
        message_contains: Optional string to filter logs by message content.
        from_date: Optional datetime to filter logs from specific date.
        to_date: Optional datetime to filter logs until specific date.
        size: Optional integer specifying the maximum number of logs to return.
        offset: Integer specifying the number of logs to skip for pagination.

    Returns:
        List[LogSummary]: List of log summaries with basic information.

    Example:
        GET /logs/?process_id=1&size=10&offset=0
        Returns up to 10 logs for process with ID 1.
    """
    try:
        logger.info(
            f"Listing logs with filters: process_id={process_id}, message_contains={message_contains}, size={size}, offset={offset}")

        stmt = select(Log)

        if process_id:
            stmt = stmt.where(Log.process_id == process_id)

        if message_contains:
            stmt = stmt.where(Log.message.contains(message_contains))

        if from_date:
            stmt = stmt.where(Log.timestamp >= from_date)

        if to_date:
            stmt = stmt.where(Log.timestamp <= to_date)

        stmt = stmt.order_by(Log.timestamp.desc()).offset(offset).limit(size)

        result = await session.execute(stmt)
        logs = result.scalars().all()

        logger.info(f"Successfully retrieved {len(logs)} logs")
        return logs

    except Exception as e:
        logger.error(f"Error listing logs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while listing logs"
        )
