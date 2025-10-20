import logging
from typing import List

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from api.services.dependancies import SessionDep
from api.services.http_schemas import TaskStatusResponse, TaskStatusSummary
from db.models import TaskStatus

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[TaskStatusSummary])
async def get_task_statuses(session: SessionDep):
    """Retrieve a list of all task statuses.

    This endpoint returns all available task statuses in the system. Task statuses
    represent the different states a task can be in during its lifecycle,
    such as pending, in-progress, complete, or in-schedule.

    Args:
        session: Database session dependency for database operations.

    Returns:
        List[TaskStatusSummary]: List of all task status summaries.

    Example:
        GET /task-statuses/
        Returns: [
            {"id": 1, "name": "pending", "description": "Task is waiting to be executed"},
            {"id": 2, "name": "in-progress", "description": "Task is currently running"}
        ]
    """
    try:
        logger.info("Retrieving all task statuses")
        stmt = select(TaskStatus)
        result = await session.execute(stmt)
        task_statuses = result.scalars().all()
        logger.info(f"Retrieved {len(task_statuses)} task statuses")
        return task_statuses
    except Exception as e:
        logger.error(f"Error retrieving task statuses: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while retrieving task statuses"
        )


@router.get("/{task_status_id}", response_model=TaskStatusResponse)
async def get_task_status(task_status_id: int, session: SessionDep):
    """Retrieve a specific task status by ID.

    This endpoint fetches detailed information about a specific task status
    including its name and description. Task statuses define the current
    state of tasks in the system workflow.

    Args:
        task_status_id: Integer ID of the task status to retrieve.
        session: Database session dependency for database operations.

    Returns:
        TaskStatusResponse: Complete task status information with all details.

    Example:
        GET /task-statuses/1
        Returns: {
            "id": 1,
            "name": "pending",
            "description": "Task is waiting to be executed"
        }
    """
    try:
        logger.info(f"Retrieving task status {task_status_id}")
        stmt = select(TaskStatus).where(TaskStatus.id == task_status_id)
        result = await session.execute(stmt)
        task_status = result.scalar_one_or_none()

        if not task_status:
            logger.warning(f"Task status {task_status_id} not found")
            raise HTTPException(
                status_code=404,
                detail=f"Task status with id {task_status_id} not found"
            )

        logger.info(f"Successfully retrieved task status {task_status_id}")
        return task_status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error retrieving task status {task_status_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while retrieving task status"
        )
