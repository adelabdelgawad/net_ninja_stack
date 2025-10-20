import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select

from api.services.dependancies import SessionDep
from api.services.http_schemas import (TaskTargetCreate, TaskTargetResponse,
                                       TaskTargetSummary)
from db.models import Line, Task, TaskTarget

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=int)
async def create_task_target(
    task_target_data: TaskTargetCreate,
    session: SessionDep,
):
    """Create a new task target linking a task to a line.

    This endpoint creates a new task target record that associates a specific
    task with a line. Both the task and line must exist in the system.

    Args:
        task_target_data: TaskTargetCreate model containing task and line IDs.
        session: Database session dependency for database operations.

    Returns:
        int: The ID of the newly created task target record.

    Example:
        POST /task-targets/
        {
            "task_id": 1,
            "line_id": 3
        }
        Returns: 7 (task target ID)
    """
    try:
        logger.info(
            f"Creating task target for task {task_target_data.task_id} and line {task_target_data.line_id}")

        # Verify task exists
        task_stmt = select(Task).where(Task.id == task_target_data.task_id)
        task_result = await session.execute(task_stmt)
        task = task_result.scalar_one_or_none()

        if not task:
            logger.error(f"Task {task_target_data.task_id} not found")
            raise HTTPException(
                status_code=404,
                detail=f"Task with id {task_target_data.task_id} not found"
            )

        # Verify line exists
        line_stmt = select(Line).where(Line.id == task_target_data.line_id)
        line_result = await session.execute(line_stmt)
        line = line_result.scalar_one_or_none()

        if not line:
            logger.error(f"Line {task_target_data.line_id} not found")
            raise HTTPException(
                status_code=404,
                detail=f"Line with id {task_target_data.line_id} not found"
            )

        # Check if task target already exists
        existing_stmt = select(TaskTarget).where(
            TaskTarget.task_id == task_target_data.task_id,
            TaskTarget.line_id == task_target_data.line_id
        )
        existing_result = await session.execute(existing_stmt)
        existing_target = existing_result.scalar_one_or_none()

        if existing_target:
            logger.error(
                f"Task target already exists for task {task_target_data.task_id} and line {task_target_data.line_id}")
            raise HTTPException(
                status_code=400,
                detail=f"Task target already exists for task {task_target_data.task_id} and line {task_target_data.line_id}"
            )

        # Create task target
        task_target = TaskTarget(**task_target_data.model_dump())
        session.add(task_target)
        await session.commit()
        await session.refresh(task_target)

        logger.info(f"Successfully created task target {task_target.id}")
        return task_target.id

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating task target: {str(e)}")
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while creating task target"
        )


@router.delete("/{task_target_id}")
async def delete_task_target(
    task_target_id: int,
    session: SessionDep,
):
    """Delete a task target record.

    This endpoint permanently removes a task target record from the system.
    This operation cannot be undone and will unlink the task from the line.

    Args:
        task_target_id: Integer ID of the task target to delete.
        session: Database session dependency for database operations.

    Returns:
        dict: Success message confirming the task target deletion.

    Example:
        DELETE /task-targets/1
        Returns: {"message": "Task target deleted successfully"}
    """
    try:
        logger.info(f"Deleting task target {task_target_id}")

        stmt = select(TaskTarget).where(TaskTarget.id == task_target_id)
        result = await session.execute(stmt)
        task_target = result.scalar_one_or_none()

        if not task_target:
            logger.warning(
                f"Task target {task_target_id} not found for deletion")
            raise HTTPException(
                status_code=404,
                detail=f"Task target with id {task_target_id} not found"
            )

        await session.delete(task_target)
        await session.commit()

        logger.info(f"Successfully deleted task target {task_target_id}")
        return {"message": "Task target deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting task target {task_target_id}: {str(e)}")
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while deleting task target"
        )


@router.get("/", response_model=List[TaskTargetSummary])
async def get_task_targets(
    session: SessionDep,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000,
                       description="Number of records to return"),
    task_id: Optional[int] = Query(None, description="Filter by task ID"),
    line_id: Optional[int] = Query(None, description="Filter by line ID"),
):
    """Retrieve a list of task targets with optional filtering.

    This endpoint returns a paginated list of task targets. You can filter by
    task or line, and control pagination with skip and limit parameters.

    Args:
        session: Database session dependency for database operations.
        skip: Number of records to skip for pagination (default: 0).
        limit: Maximum number of records to return (default: 100, max: 1000).
        task_id: Optional filter to show only targets for specific task.
        line_id: Optional filter to show only targets for specific line.

    Returns:
        List[TaskTargetSummary]: List of task target summary records.

    Example:
        GET /task-targets/?task_id=1
        Returns: [{"id": 1, "taskId": 1, "lineId": 3}, {"id": 2, "taskId": 1, "lineId": 5}]
    """
    try:
        logger.info(
            f"Retrieving task targets with skip={skip}, limit={limit}, task_id={task_id}, line_id={line_id}")

        stmt = select(TaskTarget)

        # Apply filters
        if task_id is not None:
            stmt = stmt.where(TaskTarget.task_id == task_id)
        if line_id is not None:
            stmt = stmt.where(TaskTarget.line_id == line_id)

        # Apply pagination
        stmt = stmt.offset(skip).limit(limit)

        result = await session.execute(stmt)
        task_targets = result.scalars().all()

        logger.info(f"Retrieved {len(task_targets)} task targets")
        return task_targets

    except Exception as e:
        logger.error(f"Error retrieving task targets: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while retrieving task targets"
        )


@router.get("/{task_target_id}", response_model=TaskTargetResponse)
async def get_task_target(
    task_target_id: int,
    session: SessionDep,
):
    """Retrieve a specific task target by ID.

    This endpoint returns detailed information about a single task target
    including all its properties and metadata.

    Args:
        task_target_id: Integer ID of the task target to retrieve.
        session: Database session dependency for database operations.

    Returns:
        TaskTargetResponse: Complete task target record with all details.

    Example:
        GET /task-targets/1
        Returns: {
            "id": 1,
            "taskId": 1,
            "lineId": 3,
            "createdAt": "2025-06-02T08:00:00Z"
        }
    """
    try:
        logger.info(f"Retrieving task target {task_target_id}")

        stmt = select(TaskTarget).where(TaskTarget.id == task_target_id)
        result = await session.execute(stmt)
        task_target = result.scalar_one_or_none()

        if not task_target:
            logger.warning(f"Task target {task_target_id} not found")
            raise HTTPException(
                status_code=404,
                detail=f"Task target with id {task_target_id} not found"
            )

        logger.info(f"Successfully retrieved task target {task_target_id}")
        return task_target

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error retrieving task target {task_target_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while retrieving task target"
        )
