"""
Logging configuration for the backtesting framework.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logger(log_level: str = "INFO", log_file: str = None) -> logging.Logger:
    """
    Setup logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Path to log file (optional)

    Returns:
        Configured logger
    """
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    logger.handlers = []

    # Create formatters
    detailed_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    simple_formatter = logging.Formatter(
        "%(levelname)s - %(message)s"
    )

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)

    # File handler (if log_file specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Add timestamp to log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file_with_timestamp = log_path.parent / f"{log_path.stem}_{timestamp}.log"

        file_handler = logging.FileHandler(log_file_with_timestamp)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)

        logger.info(f"Logging to file: {log_file_with_timestamp}")

    return logger
