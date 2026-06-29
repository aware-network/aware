"""
Rotating log configuration for AWARE system.
Provides file-based rotating logs with size and time-based rotation.
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional
import os


def setup_rotating_logs(
    log_dir: Optional[Path] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB default
    backup_count: int = 5,
    log_level: int = logging.INFO,
    logger_name: str = "aware",
) -> logging.Logger:
    """
    Set up rotating file logs for better debugging.

    Args:
        log_dir: Directory for log files (defaults to ~/aware_logs)
        max_bytes: Maximum size of each log file before rotation
        backup_count: Number of backup files to keep
        log_level: Logging level
        logger_name: Name of logger to enhance (defaults to "aware")

    Returns:
        Configured logger
    """

    # Create log directory
    if log_dir is None:
        log_dir = Path.home() / "aware_logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Get existing logger (don't create new)
    logger = logging.getLogger(logger_name)

    # Only set level if not already set
    if logger.level == logging.NOTSET:
        logger.setLevel(log_level)

    # Don't remove existing handlers - add to them
    # Check if we already have rotating handlers to avoid duplicates
    has_rotating = any(isinstance(h, logging.handlers.RotatingFileHandler) for h in logger.handlers)

    if has_rotating:
        logger.info("Rotating handlers already configured, skipping setup")
        return logger

    # Create formatters
    detailed_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    simple_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S")

    # Main application log (rotating)
    app_log_file = log_dir / "aware_app.log"
    app_handler = logging.handlers.RotatingFileHandler(app_log_file, maxBytes=max_bytes, backupCount=backup_count)
    app_handler.setLevel(log_level)
    app_handler.setFormatter(detailed_formatter)
    logger.addHandler(app_handler)

    # Control center specific log
    control_log_file = log_dir / "control_center.log"
    control_handler = logging.handlers.RotatingFileHandler(
        control_log_file, maxBytes=max_bytes, backupCount=backup_count
    )
    control_handler.setLevel(logging.DEBUG)  # More verbose for control center
    control_handler.setFormatter(detailed_formatter)
    control_handler.addFilter(
        lambda record: "control_center" in record.pathname or "listener_service" in record.pathname
    )
    logger.addHandler(control_handler)

    # Error log (separate file for errors only)
    error_log_file = log_dir / "aware_errors.log"
    error_handler = logging.handlers.RotatingFileHandler(error_log_file, maxBytes=max_bytes, backupCount=backup_count)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    logger.addHandler(error_handler)

    # Don't add console handler - the main logger already has it

    # Log initial message
    logger.info(f"Rotating logs initialized - Main: {app_log_file}, Errors: {error_log_file}")

    return logger


def get_log_tail(log_name: str = "aware_app.log", lines: int = 50) -> str:
    """
    Get the tail of a log file for quick debugging.

    Args:
        log_name: Name of the log file
        lines: Number of lines to return

    Returns:
        Last N lines of the log file
    """
    log_dir = Path.home() / "aware_logs"
    log_file = log_dir / log_name

    if not log_file.exists():
        return f"Log file {log_file} does not exist"

    with open(log_file, "r") as f:
        all_lines = f.readlines()
        return "".join(all_lines[-lines:])
