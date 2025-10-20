import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select

from api.services.dependancies import SessionDep
from api.services.http_schemas import (ScheduleCreate, ScheduleResponse,
                                       ScheduleSummary, ScheduleUpdate)
from db.models import Schedule

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=int)
async def create_schedule(
    schedule_data: ScheduleCreate,
    session: SessionDep,
):
    """Create a new schedule for task execution.

    This endpoint creates a new schedule record that defines when tasks
    should be executed. Schedules can be daily or for specific dates.

    Args:
        schedule_data: ScheduleCreate model containing schedule details.
        session: Database session dependency for database operations.

    Returns:
        int: The ID of the newly created schedule record.

    Example:
        POST /schedules/
        {
            "name": "Daily Morning Check",
            "execution_time": "08:00:00",
            "is_daily": true,
            "is_active": true
        }
        Returns: 4 (schedule ID)
    """
    try:
        logger.info(f"Creating schedule {schedule_data.name}")

        # Create schedule
        schedule = Schedule(**schedule_data.model_dump())
        session.add(schedule)
        await session.commit()
        await session.refresh(schedule)

        logger.info(
            f"Successfully created schedule {schedule.id}: {schedule.name}")
        return schedule.id

    except Exception as e:
        logger.error(f"Error creating schedule: {str(e)}")
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while creating schedule"
        )


@router.put("/{schedule_id}")
async def update_schedule(
    schedule_id: int,
    schedule_update: ScheduleUpdate,
    session: SessionDep,
):
    """Update an existing schedule record.

    This endpoint updates the configuration of an existing schedule record.
    The name, execution time, date, and daily flag can be modified.

    Args:
        schedule_id: Integer ID of the schedule to update.
        schedule_update: ScheduleUpdate model containing fields to update.
        session: Database session dependency for database operations.

    Returns:
        dict: Success message confirming the schedule update.

    Example:
        PUT /schedules/1
        {
            "name": "Updated Schedule Name",
            "execution_time": "09:30:00",
            "is_daily": false,
            "execution_date": "2025-06-15"
        }
        Returns: {"message": "Schedule updated successfully"}
    """
    try:
        logger.info(f"Updating schedule {schedule_id}")

        stmt = select(Schedule).where(Schedule.id == schedule_id)
        result = await session.execute(stmt)
        schedule = result.scalar_one_or_none()

        if not schedule:
            logger.warning(f"Schedule {schedule_id} not found for update")
            raise HTTPException(
                status_code=404,
                detail=f"Schedule with id {schedule_id} not found"
            )

        # Update schedule with provided data
        if schedule_update.name:
            schedule.name == schedule_update.name
        if schedule_update.execution_time:
            schedule.execution_time == schedule_update.execution_time
        if schedule_update.execution_date:
            schedule.execution_date == schedule_update.execution_date
        if schedule_update.is_daily:
            schedule.is_daily == schedule_update.is_daily
        if schedule_update.is_active:
            schedule.is_active == schedule_update.is_active

        session.add(schedule)
        await session.commit()

        logger.info(f"Successfully updated schedule {schedule_id}")
        return {"message": "Schedule updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating schedule {schedule_id}: {str(e)}")
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while updating schedule"
        )


@router.patch("/{schedule_id}/active-status")
async def change_schedule_active_status(
    schedule_id: int,
    is_active: bool,
    session: SessionDep,
):
    """Change the active status of a schedule.

    This endpoint allows you to activate or deactivate a schedule without
    modifying other schedule properties. Inactive schedules will not trigger
    task executions.

    Args:
        schedule_id: Integer ID of the schedule to update.
        is_active: Boolean indicating whether the schedule should be active.
        session: Database session dependency for database operations.

    Returns:
        dict: Success message confirming the status change.

    Example:
        PATCH /schedules/1/active-status?is_active=false
        Returns: {"message": "Schedule status updated successfully", "is_active": false}
    """
    try:
        logger.info(
            f"Changing active status for schedule {schedule_id} to {is_active}")

        stmt = select(Schedule).where(Schedule.id == schedule_id)
        result = await session.execute(stmt)
        schedule = result.scalar_one_or_none()

        if not schedule:
            logger.warning(
                f"Schedule {schedule_id} not found for status update")
            raise HTTPException(
                status_code=404,
                detail=f"Schedule with id {schedule_id} not found"
            )

        # Update only the active status
        schedule.is_active = is_active
        session.add(schedule)
        await session.commit()

        status_text = "activated" if is_active else "deactivated"
        logger.info(f"Successfully {status_text} schedule {schedule_id}")
        return {
            "message": "Schedule status updated successfully",
            "is_active": is_active
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating schedule {schedule_id} status: {str(e)}")
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while updating schedule status"
        )


@router.get("/", response_model=List[ScheduleSummary])
async def get_schedules(
    session: SessionDep,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000,
                       description="Number of records to return"),
    is_active: Optional[bool] = Query(
        None, description="Filter by active status"),
    is_daily: Optional[bool] = Query(
        None, description="Filter by daily schedules"),
):
    """Retrieve a list of schedules with optional filtering.

    This endpoint returns a paginated list of schedules. You can filter by
    active status or daily flag, and control pagination with skip and limit parameters.

    Args:
        session: Database session dependency for database operations.
        skip: Number of records to skip for pagination (default: 0).
        limit: Maximum number of records to return (default: 100, max: 1000).
        is_active: Optional filter to show only active or inactive schedules.
        is_daily: Optional filter to show only daily or one-time schedules.

    Returns:
        List[ScheduleSummary]: List of schedule summary records.

    Example:
        GET /schedules/?is_active=true&is_daily=true
        Returns: [{"id": 1, "name": "Daily Morning", "executionTime": "08:00:00", "isDaily": true, "isActive": true}]
    """
    try:
        logger.info(
            f"Retrieving schedules with skip={skip}, limit={limit}, is_active={is_active}, is_daily={is_daily}")

        stmt = select(Schedule)

        # Apply filters
        if is_active is not None:
            stmt = stmt.where(Schedule.is_active == is_active)
        if is_daily is not None:
            stmt = stmt.where(Schedule.is_daily == is_daily)

        # Apply pagination
        stmt = stmt.offset(skip).limit(limit)

        result = await session.execute(stmt)
        schedules = result.scalars().all()

        logger.info(f"Retrieved {len(schedules)} schedules")
        return schedules

    except Exception as e:
        logger.error(f"Error retrieving schedules: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while retrieving schedules"
        )


@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(
    schedule_id: int,
    session: SessionDep,
):
    """Retrieve a specific schedule by ID.

    This endpoint returns detailed information about a single schedule
    including all its properties and metadata.

    Args:
        schedule_id: Integer ID of the schedule to retrieve.
        session: Database session dependency for database operations.

    Returns:
        ScheduleResponse: Complete schedule record with all details.

    Example:
        GET /schedules/1
        Returns: {
            "id": 1,
            "name": "Daily Morning Check",
            "executionTime": "08:00:00",
            "executionDate": null,
            "isDaily": true,
            "isActive": true,
            "createdAt": "2025-06-02T08:00:00Z",
            "updatedAt": "2025-06-02T08:00:00Z"
        }
    """
    try:
        logger.info(f"Retrieving schedule {schedule_id}")

        stmt = select(Schedule).where(Schedule.id == schedule_id)
        result = await session.execute(stmt)
        schedule = result.scalar_one_or_none()

        if not schedule:
            logger.warning(f"Schedule {schedule_id} not found")
            raise HTTPException(
                status_code=404,
                detail=f"Schedule with id {schedule_id} not found"
            )

        logger.info(f"Successfully retrieved schedule {schedule_id}")
        return schedule

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving schedule {schedule_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while retrieving schedule"
        )
