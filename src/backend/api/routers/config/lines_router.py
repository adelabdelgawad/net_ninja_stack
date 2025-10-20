import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlmodel import func, select

from api.services.dependancies import SessionDep
from api.services.http_schemas import (
    LineCreate,
    LineResponse,
    LinesDashboardResponse,
    LineSummary,
    LineUpdate,
)
from db.models import ISP, Line

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/dashboard", response_model=LinesDashboardResponse)
async def get_lines_dashboard(
    session: SessionDep,
):
    """Retrieve dashboard statistics for lines including total, active, and inactive counts.

    This endpoint provides a comprehensive overview of line statistics for dashboard
    display. Active lines are defined as lines that have is_active=True,
    while inactive lines are those with is_active=False.

    Args:
        session: Database session dependency for database operations.

    Returns:
        LinesDashboardResponse: Dashboard statistics with line counts.

    Example:
        GET /lines/dashboard
        Returns: {
            "allLines": 25,
            "activeLines": 18,
            "inactiveLines": 7
        }
    """
    try:
        logger.info("Retrieving lines dashboard statistics")

        # Get total count of all lines
        all_lines_stmt = select(func.count(Line.id))
        all_lines_result = await session.execute(all_lines_stmt)
        all_lines_count = all_lines_result.scalar()

        # Get count of active lines (is_active = True)
        active_lines_stmt = select(func.count(Line.id)).where(
            Line.is_active == True
        )
        active_lines_result = await session.execute(active_lines_stmt)
        active_lines_count = active_lines_result.scalar()

        # Get count of inactive lines (is_active = False)
        inactive_lines_stmt = select(func.count(Line.id)).where(
            Line.is_active == False
        )
        inactive_lines_result = await session.execute(inactive_lines_stmt)
        inactive_lines_count = inactive_lines_result.scalar()

        logger.info(
            f"Dashboard stats: Total={all_lines_count}, "
            f"Active={active_lines_count}, Inactive={inactive_lines_count}"
        )

        return LinesDashboardResponse(
            all_lines=all_lines_count,
            active_lines=active_lines_count,
            inactive_lines=inactive_lines_count,
        )

    except Exception as e:
        logger.error(f"Error retrieving lines dashboard: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while retrieving dashboard statistics",
        )


@router.post("/", response_model=int)
async def create_line(
    line_data: LineCreate,
    session: SessionDep,
):
    """Create a new line with optional encrypted credentials.

    This endpoint creates a new line record with basic information and optionally
    stores encrypted portal credentials. The line number must be unique across
    the system and the specified ISP must exist.

    Args:
        line_data: LineCreate model containing line details and optional credentials.
        session: Database session dependency for database operations.

    Returns:
        int: The ID of the newly created line record.

    Example:
        POST /lines/
        {
            "lineNumber": "033262598",
            "name": "home",
            "description": "Home VDSL",
            "ipAddress": "10.23.1.90",
            "ispId": 1,
            "portalUsername": "user123",
            "portalPassword": "secret123"
        }
        Returns: 5 (line ID)
    """
    try:
        logger.info(f"Received line data: {line_data}")
        logger.info(f"Creating line {line_data.line_number}")

        # Check if line number already exists
        existing_stmt = select(Line).where(
            Line.line_number == line_data.line_number
        )
        existing_result = await session.execute(existing_stmt)
        existing_line = existing_result.scalar_one_or_none()

        if existing_line:
            logger.error(f"Line number {line_data.line_number} already exists")
            raise HTTPException(
                status_code=400,
                detail=f"Line number {line_data.line_number} already exists",
            )

        # Verify ISP exists
        isp_stmt = select(ISP).where(ISP.id == line_data.isp_id)
        isp_result = await session.execute(isp_stmt)
        isp = isp_result.scalar_one_or_none()

        if not isp:
            logger.error(f"ISP {line_data.isp_id} not found")
            raise HTTPException(
                status_code=404,
                detail=f"ISP with id {line_data.isp_id} not found",
            )

        # Create line with basic data
        line_dict = line_data.model_dump(exclude={"username", "password"})
        line = Line(**line_dict)

        # Set encrypted credentials if provided
        if line_data.username and line_data.password:
            line.set_username(line_data.username)
            line.set_password(line_data.password)

        session.add(line)
        await session.commit()
        await session.refresh(line)

        logger.info(f"Successfully created line {line.id}: {line.line_number}")
        return line.id

    except HTTPException:
        raise
    except IntegrityError as e:
        logger.error(f"Database integrity error creating line: {str(e)}")
        await session.rollback()

        if "Duplicate entry" in str(e) or "UNIQUE constraint failed" in str(e):
            raise HTTPException(
                status_code=400,
                detail=f"Line number {line_data.line_number} already exists",
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Database constraint violation: {str(e)}",
            )
    except Exception as e:
        logger.error(f"Error creating line: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error occurred while creating line: {str(e)}",
        )


@router.get("/{line_id}", response_model=LineResponse)
async def get_line(
    line_id: int,
    session: SessionDep,
    include_credentials: bool = Query(
        False, description="Include decrypted credentials in response"
    ),
):
    """Retrieve a specific line by ID with optional credential decryption.

    This endpoint fetches detailed information about a line including its
    associated ISP details. Optionally includes decrypted portal credentials
    when include_credentials is set to true.

    Args:
        line_id: Integer ID of the line to retrieve.
        session: Database session dependency for database operations.
        include_credentials: Boolean flag to include decrypted credentials.

    Returns:
        LineResponse: Complete line information with optional credentials.

    Example:
        GET /lines/1?include_credentials=true
        Returns line details with decrypted credentials
    """
    try:
        logger.info(f"Retrieving line {line_id}")

        stmt = select(Line).where(Line.id == line_id)
        result = await session.execute(stmt)
        line = result.scalar_one_or_none()

        if not line:
            logger.warning(f"Line {line_id} not found")
            raise HTTPException(
                status_code=404, detail=f"Line with id {line_id} not found"
            )

        # Prepare response data
        response_data = {
            "id": line.id,
            "name": line.name,
            "line_number": line.line_number,
            "description": line.description,
            "ip_address": line.ip_address,
            "isp_id": line.isp_id,
            "created_at": line.created_at,
            "updated_at": line.updated_at,
            "has_credentials": line.has_credentials(),
        }

        # Include credentials if requested and available
        if include_credentials and line.has_credentials():
            username, password = line.get_credentials()
            response_data.update({"username": username, "password": password})

        logger.info(f"Successfully retrieved line {line_id}")
        return LineResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving line {line_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while retrieving line",
        )


@router.put("/{line_id}")
async def update_line(
    line_id: int,
    line_update: LineUpdate,
    session: SessionDep,
):
    """Update an existing line's configuration and credentials.

    This endpoint updates the configuration of an existing line including
    basic information and portal credentials. All fields are optional in
    the update request, allowing partial updates while maintaining data integrity.

    Args:
        line_id: Integer ID of the line to update.
        line_update: LineUpdate model containing fields to update.
        session: Database session dependency for database operations.

    Returns:
        dict: Success message confirming the line update.

    Example:
        PUT /lines/1
        {
            "description": "Updated description",
            "ipAddress": "192.168.1.10",
            "portalUsername": "newuser",
            "portalPassword": "newpass"
        }
        Returns: {"message": "Line updated successfully"}
    """
    try:
        logger.info(f"Updating line {line_id}")

        stmt = select(Line).where(Line.id == line_id)
        result = await session.execute(stmt)
        line = result.scalar_one_or_none()

        if not line:
            logger.warning(f"Line {line_id} not found for update")
            raise HTTPException(
                status_code=404, detail=f"Line with id {line_id} not found"
            )

        # Update fields with provided data
        if line_update.line_number:
            line.line_number = line_update.line_number
        if line_update.name:
            line.name = line_update.name
        if line_update.description:
            line.description = line_update.description
        if line_update.ip_address:
            line.ip_address = line_update.ip_address
        if line_update.isp_id:
            line.isp_id = line_update.isp_id
        if line_update.is_active:
            line.is_active = line_update.is_active
        if line_update.username:
            line.set_username(line_update.username)
        if line_update.password:
            line.set_password(line_update.password)

        session.add(line)
        await session.commit()

        logger.info(f"Successfully updated line {line_id}")
        return {"message": "Line updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating line {line_id}: {str(e)}")
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while updating line",
        )


@router.delete("/{line_id}")
async def delete_line(
    line_id: int,
    session: SessionDep,
):
    """Delete a line and all associated records.

    This endpoint permanently removes a line and all its associated data
    including speed test results, quota results, and process logs. This
    operation cannot be undone and should be used with caution.

    Args:
        line_id: Integer ID of the line to delete.
        session: Database session dependency for database operations.

    Returns:
        dict: Success message confirming the line deletion.

    Example:
        DELETE /lines/1
        Returns: {"message": "Line deleted successfully"}
    """
    try:
        logger.info(f"Deleting line {line_id}")

        stmt = select(Line).where(Line.id == line_id)
        result = await session.execute(stmt)
        line = result.scalar_one_or_none()

        if not line:
            logger.warning(f"Line {line_id} not found for deletion")
            raise HTTPException(
                status_code=404, detail=f"Line with id {line_id} not found"
            )

        await session.delete(line)
        await session.commit()

        logger.info(f"Successfully deleted line {line_id}")
        return {"message": "Line deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting line {line_id}: {str(e)}")
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while deleting line",
        )


@router.get("/", response_model=List[LineSummary])
async def list_lines(
    session: SessionDep,
    isp_id: Optional[int] = Query(
        None, description="Filter lines by ISP ID", ge=1
    ),
    line_number: Optional[str] = Query(
        None, description="Filter lines by line number", max_length=50
    ),
    has_credentials: Optional[bool] = Query(
        None, description="Filter lines by credential availability"
    ),
    size: Optional[int] = Query(
        50, ge=1, le=1000, description="Number of lines to return"
    ),
    offset: int = Query(
        0, ge=0, description="Number of lines to skip for pagination"
    ),
):
    """Retrieve a list of lines with optional filtering.

    This endpoint returns a paginated list of lines with optional filtering
    by ISP, line number, or credential availability. The response includes
    summary information for each line suitable for listing and selection interfaces.

    Args:
        session: Database session dependency for database operations.
        isp_id: Optional integer to filter lines by specific ISP.
        line_number: Optional string to filter lines by line number.
        has_credentials: Optional boolean to filter lines by credential availability.
        size: Optional integer specifying the maximum number of lines to return.
        offset: Integer specifying the number of lines to skip for pagination.

    Returns:
        List[LineSummary]: List of line summaries with basic information.

    Example:
        GET /lines/?isp_id=1&has_credentials=true&size=10&offset=0
        Returns up to 10 lines for ISP with ID 1 that have credentials.
    """
    try:
        logger.info(
            f"Listing lines with filters: isp_id={isp_id}, line_number={line_number}, "
            f"has_credentials={has_credentials}, size={size}, offset={offset}"
        )

        stmt = select(Line)

        if isp_id:
            stmt = stmt.where(Line.isp_id == isp_id)
        if line_number:
            stmt = stmt.where(Line.line_number.contains(line_number))
        if has_credentials is not None:
            if has_credentials:
                stmt = stmt.where(Line.username.is_not(None))
            else:
                stmt = stmt.where(Line.username.is_(None))

        stmt = stmt.offset(offset).limit(size)

        result = await session.execute(stmt)
        lines = result.scalars().all()

        # Convert to summary format with credential status
        line_summaries = [
            LineSummary(
                id=line.id,
                line_number=line.line_number,
                name=line.name,
                isp_id=line.isp_id,
                has_credentials=line.has_credentials(),
            )
            for line in lines
        ]

        logger.info(f"Successfully retrieved {len(line_summaries)} lines")
        return line_summaries

    except Exception as e:
        logger.error(f"Error listing lines: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while listing lines",
        )
