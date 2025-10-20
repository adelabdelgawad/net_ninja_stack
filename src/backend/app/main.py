import argparse
import asyncio
from tasks.task_runner import run_tasks
import logging

# Configure basic logging
logging.basicConfig(
    format="%(asctime)s [%(name)s] | [%(funcName)s] [%(levelname)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# Main function to run the task
if __name__ == "__main__":

    # Argument parser to handle CLI arguments
    parser = argparse.ArgumentParser(
        description="Run quota check and speedtest.")
    parser.add_argument("--headless", action="store_true",
                        help="Run in headless mode")
    args = parser.parse_args()

    # Run the tasks using asyncio
    try:
        logger.info("Starting task runner...")
        asyncio.run(run_tasks(args.headless))
        logger.info("Task runner completed successfully.")
    except Exception as e:
        logger.error(f"Error while running tasks: {e}")
        raise
