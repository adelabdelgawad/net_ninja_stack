import logging
from typing import List

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from api.services.dependancies import SessionDep
from api.services.http_schemas import JobResponse, JobSummary
from db.models import Job

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[JobSummary])
async def get_jobs(session: SessionDep):
    """Retrieve a list of all jobs.

    This endpoint returns all available jobs in the system. Jobs represent
    different types of tasks that can be executed, such as speed tests,
    quota checks, or combined operations.

    Args:
        session: Database session dependency for database operations.

    Returns:
        List[JobSummary]: List of all job summaries.

    Example:
        GET /jobs/
        Returns: [
            {"id": 1, "name": "speedtest", "description": "Run speed test"},
            {"id": 2, "name": "quotacheck", "description": "Check quota usage"}
        ]
    """
    try:
        logger.info("Retrieving all jobs")
        stmt = select(Job)
        result = await session.execute(stmt)
        jobs = result.scalars().all()
        logger.info(f"Retrieved {len(jobs)} jobs")
        return jobs
    except Exception as e:
        logger.error(f"Error retrieving jobs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while retrieving jobs"
        )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, session: SessionDep):
    """Retrieve a specific job by ID.

    This endpoint fetches detailed information about a specific job including
    its name, description, and metadata. Jobs define the type of work that
    tasks can perform.

    Args:
        job_id: Integer ID of the job to retrieve.
        session: Database session dependency for database operations.

    Returns:
        JobResponse: Complete job information with all details.

    Example:
        GET /jobs/1
        Returns: {
            "id": 1,
            "name": "speedtest",
            "description": "Run speed test on network lines",
            "createdAt": "2025-06-02T08:00:00Z",
            "updatedAt": "2025-06-02T08:00:00Z"
        }
    """
    try:
        logger.info(f"Retrieving job {job_id}")
        stmt = select(Job).where(Job.id == job_id)
        result = await session.execute(stmt)
        job = result.scalar_one_or_none()

        if not job:
            logger.warning(f"Job {job_id} not found")
            raise HTTPException(
                status_code=404,
                detail=f"Job with id {job_id} not found"
            )

        logger.info(f"Successfully retrieved job {job_id}")
        return job
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while retrieving job"
        )
