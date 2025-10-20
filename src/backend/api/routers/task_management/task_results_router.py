import logging
from typing import List

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select

from api.services.dependancies import SessionDep
from api.services.http_schemas import TaskResultResponse, TaskResultSummary
from db.models import Task, TaskResult

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[TaskResultSummary])
async def get_task_results(
    session: SessionDep,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000,
                       description="Number of records to return"),
):
    """Retrieve a list of all task results with pagination.

    This endpoint returns a paginated list of task results showing the
    execution outcomes of tasks. Results include success/failure status
    and execution timestamps.

    Args:
        session: Database session dependency for database operations.
        skip: Number of records to skip for pagination (default: 0).
        limit: Maximum number of records to return (default: 100, max: 1000).

    Returns:
        List[TaskResultSummary]: List of task result summary records.

    Example:
        GET /task-results/?skip=0&limit=10
        Returns: [
            {"id": 1, "taskId": 1, "isSucceed": true, "createdAt": "2025-06-02T08:00:00Z"},
            {"id": 2, "taskId": 1, "isSucceed": false, "createdAt": "2025-06-02T09:00:00Z"}
        ]
    """
    try:
        logger.info(f"Retrieving task results with skip={skip}, limit={limit}")

        stmt = select(TaskResult).offset(skip).limit(
            limit).order_by(TaskResult.created_at.desc())
        result = await session.execute(stmt)
        task_results = result.scalars().all()

        logger.info(f"Retrieved {len(task_results)} task results")
        return task_results

    except Exception as e:
        logger.error(f"Error retrieving task results: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while retrieving task results"
        )


@router.get("/task/{task_id}", response_model=List[TaskResultResponse])
async def get_task_results_by_task_id(
    task_id: int,
    session: SessionDep,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000,
                       description="Number of records to return"),
):
    """Retrieve task results for a specific task.

    This endpoint returns all execution results for a specific task,
    showing the history of task executions including success and failure records.

    Args:
        task_id: Integer ID of the task to retrieve results for.
        session: Database session dependency for database operations.
        skip: Number of records to skip for pagination (default: 0).
        limit: Maximum number of records to return (default: 100, max: 1000).

    Returns:
        List[TaskResultResponse]: List of task results for the specified task.

    Example:
        GET /task-results/task/1?skip=0&limit=10
        Returns task results for task with ID 1
    """
    try:
        logger.info(f"Retrieving task results for task {task_id}")

        # Verify task exists
        task_stmt = select(Task).where(Task.id == task_id)
        task_result = await session.execute(task_stmt)
        task = task_result.scalar_one_or_none()

        if not task:
            logger.warning(f"Task {task_id} not found")
            raise HTTPException(
                status_code=404,
                detail=f"Task with id {task_id} not found"
            )

        stmt = select(TaskResult).where(TaskResult.task_id == task_id).offset(
            skip).limit(limit).order_by(TaskResult.created_at.desc())
        result = await session.execute(stmt)
        task_results = result.scalars().all()

        logger.info(
            f"Retrieved {len(task_results)} task results for task {task_id}")
        return task_results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error retrieving task results for task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while retrieving task results"
        )


@router.get("/tasks", response_model=List[TaskResultResponse])
async def get_task_results_by_task_ids(
    session: SessionDep,

    task_ids: List[int] = Query(...,
                                description="List of task IDs to filter by"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000,
                       description="Number of records to return"),
):
    """Retrieve task results for multiple specific tasks.

    This endpoint returns execution results for multiple tasks specified
    by their IDs, useful for batch operations and dashboard views.

    Args:
        task_ids: List of task IDs to retrieve results for.
        session: Database session dependency for database operations.
        skip: Number of records to skip for pagination (default: 0).
        limit: Maximum number of records to return (default: 100, max: 1000).

    Returns:
        List[TaskResultResponse]: List of task results for the specified tasks.

    Example:
        GET /task-results/tasks?task_ids=1&task_ids=2&task_ids=3
        Returns task results for tasks with IDs 1, 2, and 3
    """
    try:
        logger.info(f"Retrieving task results for tasks {task_ids}")

        if not task_ids:
            raise HTTPException(
                status_code=400,
                detail="At least one task ID must be provided"
            )

        if len(task_ids) > 50:
            raise HTTPException(
                status_code=400,
                detail="Maximum 50 task IDs allowed per request"
            )

        stmt = select(TaskResult).where(TaskResult.task_id.in_(task_ids)).offset(
            skip).limit(limit).order_by(TaskResult.created_at.desc())
        result = await session.execute(stmt)
        task_results = result.scalars().all()

        logger.info(
            f"Retrieved {len(task_results)} task results for {len(task_ids)} tasks")
        return task_results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error retrieving task results for tasks {task_ids}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while retrieving task results"
        )


@router.get("/status/{is_succeed}", response_model=List[TaskResultResponse])
async def get_task_results_by_success_status(
    is_succeed: bool,
    session: SessionDep,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000,
                       description="Number of records to return"),
):
    """Retrieve task results filtered by success status.

    This endpoint returns task results filtered by their success or failure status,
    useful for monitoring and troubleshooting task execution issues.

    Args:
        is_succeed: Boolean indicating whether to retrieve successful (true) or failed (false) results.
        session: Database session dependency for database operations.
        skip: Number of records to skip for pagination (default: 0).
        limit: Maximum number of records to return (default: 100, max: 1000).

    Returns:
        List[TaskResultResponse]: List of task results matching the success status.

    Example:
        GET /task-results/status/false?skip=0&limit=10
        Returns the last 10 failed task results
    """
    try:
        status_text = "successful" if is_succeed else "failed"
        logger.info(f"Retrieving {status_text} task results")

        stmt = select(TaskResult).where(TaskResult.is_succeed == is_succeed).offset(
            skip).limit(limit).order_by(TaskResult.created_at.desc())
        result = await session.execute(stmt)
        task_results = result.scalars().all()

        logger.info(
            f"Retrieved {len(task_results)} {status_text} task results")
        return task_results

    except Exception as e:
        logger.error(
            f"Error retrieving task results by success status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while retrieving task results"
        )
