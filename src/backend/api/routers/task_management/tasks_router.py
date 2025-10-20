import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select

from api.services.dependancies import SessionDep
from api.services.http_schemas import (TaskCreate, TaskResponse, TaskSummary,
                                       TaskUpdate)
from db.models import Job, Task, TaskStatus

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=int)
async def create_task(
    task_data: TaskCreate,
    session: SessionDep,
):
    """Create a new task with status and job association.

    This endpoint creates a new task record associated with a specific status and job.
    Both the status and job must exist in the system before creating task records.

    Args:
        task_data: TaskCreate model containing task details, status and job IDs.
        session: Database session dependency for database operations.

    Returns:
        int: The ID of the newly created task record.

    Example:
        POST /tasks/
        {
            "name": "Daily Speed Test",
            "description": "Run speed tests on all lines",
            "status_id": 1,
            "job_id": 2
        }
        Returns: 5 (task ID)
    """
    try:
        logger.info(f"Creating task {task_data.name}")

        # Verify status exists
        status_stmt = select(TaskStatus).where(
            TaskStatus.id == task_data.status_id)
        status_result = await session.execute(status_stmt)
        task_status = status_result.scalar_one_or_none()

        if not task_status:
            logger.error(f"Task status {task_data.status_id} not found")
            raise HTTPException(
                status_code=404,
                detail=f"Task status with id {task_data.status_id} not found"
            )

        # Verify job exists
        job_stmt = select(Job).where(Job.id == task_data.job_id)
        job_result = await session.execute(job_stmt)
        job = job_result.scalar_one_or_none()

        if not job:
            logger.error(f"Job {task_data.job_id} not found")
            raise HTTPException(
                status_code=404,
                detail=f"Job with id {task_data.job_id} not found"
            )

        # Create task
        task = Task(**task_data.model_dump())
        session.add(task)
        await session.commit()
        await session.refresh(task)

        logger.info(f"Successfully created task {task.id}: {task.name}")
        return task.id

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating task: {str(e)}")
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while creating task"
        )


@router.put("/{task_id}")
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    session: SessionDep,
):
    """Update an existing task record.

    This endpoint updates the configuration of an existing task record.
    The name, description, status, and job can be modified while maintaining
    referential integrity.

    Args:
        task_id: Integer ID of the task to update.
        task_update: TaskUpdate model containing fields to update.
        session: Database session dependency for database operations.

    Returns:
        dict: Success message confirming the task update.

    Example:
        PUT /tasks/1
        {
            "name": "Updated Task Name",
            "description": "Updated description",
            "status_id": 2
        }
        Returns: {"message": "Task updated successfully"}
    """
    try:
        logger.info(f"Updating task {task_id}")

        stmt = select(Task).where(Task.id == task_id)
        result = await session.execute(stmt)
        task = result.scalar_one_or_none()

        if not task:
            logger.warning(f"Task {task_id} not found for update")
            raise HTTPException(
                status_code=404,
                detail=f"Task with id {task_id} not found"
            )

        # Verify status exists if being updated
        update_data = task_update.model_dump(exclude_unset=True)
        if "status_id" in update_data:
            status_stmt = select(TaskStatus).where(
                TaskStatus.id == update_data["status_id"])
            status_result = await session.execute(status_stmt)
            task_status = status_result.scalar_one_or_none()

            if not task_status:
                logger.error(
                    f"Task status {update_data['status_id']} not found")
                raise HTTPException(
                    status_code=404,
                    detail=f"Task status with id {update_data['status_id']} not found"
                )

        # Verify job exists if being updated
        if "job_id" in update_data:
            job_stmt = select(Job).where(Job.id == update_data["job_id"])
            job_result = await session.execute(job_stmt)
            job = job_result.scalar_one_or_none()

            if not job:
                logger.error(f"Job {update_data['job_id']} not found")
                raise HTTPException(
                    status_code=404,
                    detail=f"Job with id {update_data['job_id']} not found"
                )

        # Update task with provided data
        if task_update.name:
            task.name = task_update.name
        if task_update.description:
            task.description = task_update.description
        if task_update.status_id:
            task.status_id = task_update.status_id
        if task_update.job_id:
            task.job_id = task_update.job_id

        session.add(task)
        await session.commit()

        logger.info(f"Successfully updated task {task_id}")
        return {"message": "Task updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating task {task_id}: {str(e)}")
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while updating task"
        )


@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    session: SessionDep,
):
    """Delete a task record.

    This endpoint permanently removes a task record from the system.
    This operation cannot be undone and will also remove associated
    task targets and schedules.

    Args:
        task_id: Integer ID of the task to delete.
        session: Database session dependency for database operations.

    Returns:
        dict: Success message confirming the task deletion.

    Example:
        DELETE /tasks/1
        Returns: {"message": "Task deleted successfully"}
    """
    try:
        logger.info(f"Deleting task {task_id}")

        stmt = select(Task).where(Task.id == task_id)
        result = await session.execute(stmt)
        task = result.scalar_one_or_none()

        if not task:
            logger.warning(f"Task {task_id} not found for deletion")
            raise HTTPException(
                status_code=404,
                detail=f"Task with id {task_id} not found"
            )

        await session.delete(task)
        await session.commit()

        logger.info(f"Successfully deleted task {task_id}")
        return {"message": "Task deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting task {task_id}: {str(e)}")
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while deleting task"
        )


@router.get("/", response_model=List[TaskSummary])
async def get_tasks(
    session: SessionDep,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000,
                       description="Number of records to return"),
    status_id: Optional[int] = Query(None, description="Filter by status ID"),
    job_id: Optional[int] = Query(None, description="Filter by job ID"),
):
    """Retrieve a list of tasks with optional filtering.

    This endpoint returns a paginated list of tasks. You can filter by
    status or job, and control pagination with skip and limit parameters.

    Args:
        session: Database session dependency for database operations.
        skip: Number of records to skip for pagination (default: 0).
        limit: Maximum number of records to return (default: 100, max: 1000).
        status_id: Optional filter to show only tasks with specific status.
        job_id: Optional filter to show only tasks with specific job.

    Returns:
        List[TaskSummary]: List of task summary records.

    Example:
        GET /tasks/?skip=0&limit=10&status_id=1
        Returns: [{"id": 1, "name": "Daily Check", "statusId": 1, "jobId": 2}, ...]
    """
    try:
        logger.info(
            f"Retrieving tasks with skip={skip}, limit={limit}, status_id={status_id}, job_id={job_id}")

        stmt = select(Task)

        # Apply filters
        if status_id is not None:
            stmt = stmt.where(Task.status_id == status_id)
        if job_id is not None:
            stmt = stmt.where(Task.job_id == job_id)

        # Apply pagination
        stmt = stmt.offset(skip).limit(limit)

        result = await session.execute(stmt)
        tasks = result.scalars().all()

        logger.info(f"Retrieved {len(tasks)} tasks")
        return tasks

    except Exception as e:
        logger.error(f"Error retrieving tasks: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while retrieving tasks"
        )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    session: SessionDep,
):
    """Retrieve a specific task by ID.

    This endpoint returns detailed information about a single task
    including all its properties and metadata.

    Args:
        task_id: Integer ID of the task to retrieve.
        session: Database session dependency for database operations.

    Returns:
        TaskResponse: Complete task record with all details.

    Example:
        GET /tasks/1
        Returns: {
            "id": 1,
            "name": "Daily Speed Test",
            "description": "Run speed tests on all lines",
            "statusId": 1,
            "jobId": 2,
            "createdAt": "2025-06-02T08:00:00Z",
            "updatedAt": "2025-06-02T08:00:00Z"
        }
    """
    try:
        logger.info(f"Retrieving task {task_id}")

        stmt = select(Task).where(Task.id == task_id)
        result = await session.execute(stmt)
        task = result.scalar_one_or_none()

        if not task:
            logger.warning(f"Task {task_id} not found")
            raise HTTPException(
                status_code=404,
                detail=f"Task with id {task_id} not found"
            )

        logger.info(f"Successfully retrieved task {task_id}")
        return task

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while retrieving task"
        )
