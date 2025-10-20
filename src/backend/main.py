import logging
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from api.routers.config.emails_router import router as emails_router
from api.routers.config.lines_router import router as lines_router
from api.routers.config.logs_router import router as logs_router
from api.routers.task_management.jobs_router import router as jobs_router
from api.routers.task_management.schedules_router import \
    router as schedules_router
from api.routers.task_management.task_results_router import \
    router as task_results_router
from api.routers.task_management.task_statuses_router import \
    router as task_statuses_router
from api.routers.task_management.task_targets_router import \
    router as task_targets_router
from api.routers.task_management.tasks_router import router as tasks_router
from core.config import settings
from db.setup_database import setup_database

# Import routers

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s | %(pathname)s:%(lineno)d",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

# Define API metadata
API_TITLE = settings.api.title
API_DESCRIPTION = settings.api.description
API_VERSION = settings.api.version


@asynccontextmanager
async def lifespan(app: FastAPI):

    # Startup: setup the database before the application starts
    logger.info("Starting up the application and setting up the database")
    try:
        await setup_database()
        logger.info("Database setup completed successfully")
    except Exception as e:
        logger.error(f"Database setup failed: {str(e)}")
        raise

    yield

    # Shutdown: cleanup operations when the application is shutting down
    logger.info("Shutting down the application")
    # Add any cleanup code here if needed


def format_validation_error(exc: RequestValidationError) -> Dict[str, Any]:
    """
    Format validation errors into a more user-friendly structure.
    """
    errors = []

    for error in exc.errors():
        error_detail = {
            "loc": error.get("loc", []),
            "field": error.get("loc", [])[-1] if error.get("loc") else None,
            "msg": error.get("msg", ""),
            "type": error.get("type", ""),
        }
        errors.append(error_detail)

    return {"status_code": 422, "error": "Validation Error", "detail": errors}


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    Returns the configured FastAPI instance.
    """
    app = FastAPI(
        title=API_TITLE,
        description=API_DESCRIPTION,
        version=API_VERSION,
        lifespan=lifespan,
    )

    # Register custom exception handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        """
        Handle validation errors and return detailed information.
        """
        logger.warning(f"Validation error: {exc}")
        return JSONResponse(
            status_code=422,
            content=format_validation_error(exc),
        )

    # Register routers with appropriate tags and prefixes
    register_routers(app)

    return app


def register_routers(app: FastAPI) -> None:
    """
    Register all API routers with the FastAPI application.
    """
    app.include_router(lines_router, prefix="/config/lines", tags=["Lines"])
    app.include_router(
        emails_router, prefix="/config/emails", tags=["Emails"])
    app.include_router(logs_router, prefix="/config/logs", tags=["Logs"])

    app.include_router(
        jobs_router, prefix="/task-management/jobs", tags=["Jobs"])
    app.include_router(
        task_statuses_router, prefix="/task-management/task-statuses", tags=["Task Statuses"])
    app.include_router(
        task_results_router, prefix="/task-management/task-results", tags=["Task Results"])
    app.include_router(
        schedules_router, prefix="/task-management/schedules", tags=["Schedules"])
    app.include_router(task_targets_router,
                       prefix="/task-management/task-targets", tags=["Task Targets"])
    app.include_router(tasks_router, prefix="/task-management/tasks",
                       tags=["Tasks"])


# Create the FastAPI app
app = create_application()
