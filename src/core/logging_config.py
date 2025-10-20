"""
File-based logging configuration with automatic rotation.

This module provides simple file-based logging that replaces the complex
database logging system. Logs are written to timestamped files and
automatically rotated (keeping only the latest 7 files).
"""

import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_file_logging(log_dir: Path = Path("logs"), max_files: int = 7):
    """
    Setup file-based logging with rotation.

    Args:
        log_dir: Directory to store log files
        max_files: Number of log files to keep (default: 7)

    Returns:
        Path to the created log file

    Creates daily log files with format: netninja_YYYYMMDD_HHMMSS.log
    Automatically removes old log files keeping only the latest N files.
    """
    # Create logs directory
    log_dir.mkdir(exist_ok=True)

    # Generate log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"netninja_{timestamp}.log"

    # Clean up old log files (keep only latest max_files)
    cleanup_old_logs(log_dir, max_files)

    # Remove any existing handlers to avoid duplicates
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            # File handler - write to daily log file
            logging.FileHandler(log_file, encoding='utf-8'),
            # Console handler - write to stdout
            logging.StreamHandler(sys.stdout)
        ],
        force=True  # Override any existing configuration
    )

    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized - Log file: {log_file}")

    return log_file


def cleanup_old_logs(log_dir: Path, max_files: int = 7):
    """
    Remove old log files, keeping only the latest N files.

    Args:
        log_dir: Directory containing log files
        max_files: Number of most recent files to keep
    """
    # Get all log files sorted by modification time (newest first)
    log_files = sorted(
        log_dir.glob("netninja_*.log"),
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )

    # Remove files beyond max_files limit
    for old_file in log_files[max_files:]:
        try:
            old_file.unlink()
            print(f"Removed old log file: {old_file.name}")
        except Exception as e:
            print(f"Failed to remove {old_file.name}: {e}")


def get_logger(name: str) -> logging.Logger:
    """Get logger instance for a module"""
    return logging.getLogger(name)
