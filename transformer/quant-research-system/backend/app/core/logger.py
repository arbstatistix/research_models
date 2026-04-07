"""
================================================================================
QUANT RESEARCH PIPELINE - LOGGING CONFIGURATION
================================================================================

This module provides a comprehensive logging system with daily rotating file
handlers. It creates multiple log files filtered by severity level for easy
debugging and monitoring.

FEATURES:
---------
- Daily rotating log files (new file each day)
- Multiple severity-filtered files (all, info, warnings, errors)
- Detailed formatting with timestamps, module names, and line numbers
- Console output for immediate feedback
- Thread-safe logging

LOG FILE STRUCTURE:
-------------------
    logs/
    ├── 2026-04-07_all.log       ← DEBUG and above (everything)
    ├── 2026-04-07_info.log      ← INFO and above
    ├── 2026-04-07_warnings.log  ← WARNING and above
    └── 2026-04-07_errors.log    ← ERROR and above

LOG FORMAT:
-----------
    File:    2026-04-07 16:28:03 - module_name - INFO - [filename.py:42] - Message
    Console: 16:28:03 - INFO - Message

USAGE:
------
    from app.core.logger import setup_daily_logger, get_logger
    
    # Create a new logger for a module
    logger = setup_daily_logger("my_module", log_dir="logs")
    
    # Log at different levels
    logger.debug("Detailed debugging information")
    logger.info("General information")
    logger.warning("Warning messages")
    logger.error("Error messages")
    logger.critical("Critical failures")
    
    # Get existing logger
    logger = get_logger("my_module")

RELATIONSHIPS:
--------------
- Used by: All backend modules
- Creates: logs/ directory and daily log files
- Independent: No dependencies on other app modules

================================================================================
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_daily_logger(
    name: str, 
    log_dir: str = "logs", 
    level: int = logging.DEBUG
) -> logging.Logger:
    """
    Set up a logger with daily rotating file handlers.
    
    Creates a comprehensive logging setup with multiple output destinations:
    - Console: INFO and above (for immediate feedback)
    - All logs file: DEBUG and above (complete record)
    - Info logs file: INFO and above (operational events)
    - Warning logs file: WARNING and above (potential issues)
    - Error logs file: ERROR and above (failures only)
    
    This function is idempotent - calling it multiple times with the same
    name will return the existing logger without adding duplicate handlers.
    
    Args:
        name: Logger name (typically module name like "pipeline", "routes")
        log_dir: Directory path for log files (created if doesn't exist)
        level: Minimum logging level for the logger (default: DEBUG)
        
    Returns:
        logging.Logger: Configured logger instance ready for use
        
    Example:
        >>> logger = setup_daily_logger("my_module")
        >>> logger.info("Application started")
        >>> logger.error("Something went wrong", exc_info=True)
        
    Note:
        Log files are named with the current date (YYYY-MM-DD) so a new
        file is automatically created each day. This provides natural
        log rotation without additional configuration.
    """
    # Get or create logger with the specified name
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # ==========================================================================
    # IDEMPOTENCY CHECK
    # ==========================================================================
    # Prevent duplicate handlers if logger already configured
    # This happens when the module is imported multiple times
    if logger.handlers:
        logger.debug(f"Logger '{name}' already configured, returning existing instance")
        return logger
    
    # ==========================================================================
    # CREATE LOG DIRECTORY
    # ==========================================================================
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # ==========================================================================
    # DATE PREFIX FOR DAILY ROTATION
    # ==========================================================================
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # ==========================================================================
    # FORMATTER DEFINITIONS
    # ==========================================================================
    
    # Detailed formatter for file logs
    # Includes: timestamp, logger name, level, source file:line, message
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Simple formatter for console output
    # Includes: time, level, message (more readable for terminal)
    simple_formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # ==========================================================================
    # CONSOLE HANDLER
    # ==========================================================================
    # Outputs to stdout for immediate visibility during development
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)  # Only INFO and above to console
    console_handler.setFormatter(simple_formatter)
    console_handler.set_name(f"{name}_console")
    logger.addHandler(console_handler)
    
    # ==========================================================================
    # FILE HANDLER: ALL LOGS (DEBUG+)
    # ==========================================================================
    # Captures everything for complete debugging record
    all_logs_file = log_path / f"{current_date}_all.log"
    all_handler = logging.FileHandler(all_logs_file, encoding='utf-8')
    all_handler.setLevel(logging.DEBUG)
    all_handler.setFormatter(detailed_formatter)
    all_handler.set_name(f"{name}_all")
    logger.addHandler(all_handler)
    
    # ==========================================================================
    # FILE HANDLER: INFO LOGS (INFO+)
    # ==========================================================================
    # Captures operational events and above
    info_logs_file = log_path / f"{current_date}_info.log"
    info_handler = logging.FileHandler(info_logs_file, encoding='utf-8')
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(detailed_formatter)
    info_handler.set_name(f"{name}_info")
    logger.addHandler(info_handler)
    
    # ==========================================================================
    # FILE HANDLER: WARNING LOGS (WARNING+)
    # ==========================================================================
    # Captures potential issues that need attention
    warning_logs_file = log_path / f"{current_date}_warnings.log"
    warning_handler = logging.FileHandler(warning_logs_file, encoding='utf-8')
    warning_handler.setLevel(logging.WARNING)
    warning_handler.setFormatter(detailed_formatter)
    warning_handler.set_name(f"{name}_warnings")
    logger.addHandler(warning_handler)
    
    # ==========================================================================
    # FILE HANDLER: ERROR LOGS (ERROR+)
    # ==========================================================================
    # Captures only errors and critical issues
    error_logs_file = log_path / f"{current_date}_errors.log"
    error_handler = logging.FileHandler(error_logs_file, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    error_handler.set_name(f"{name}_errors")
    logger.addHandler(error_handler)
    
    # ==========================================================================
    # INITIALIZATION COMPLETE
    # ==========================================================================
    logger.info(f"Logger '{name}' initialized. Log files: {log_path}/{current_date}_*.log")
    logger.debug(f"Logger handlers: console(INFO), all(DEBUG), info(INFO), warnings(WARNING), errors(ERROR)")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get an existing logger or create a new one with default settings.
    
    This is a convenience function for getting a logger instance.
    If the logger doesn't exist or has no handlers, it will be
    configured with default settings using setup_daily_logger().
    
    Args:
        name: Logger name to retrieve or create
        
    Returns:
        logging.Logger: The requested logger instance
        
    Example:
        >>> logger = get_logger("pipeline")
        >>> logger.info("Processing started")
    """
    logger = logging.getLogger(name)
    
    # If logger has no handlers, set it up with defaults
    if not logger.handlers:
        return setup_daily_logger(name)
    
    return logger


def log_function_entry(logger: logging.Logger, func_name: str, **kwargs):
    """
    Log entry into a function with its arguments.
    
    Utility function for consistent function entry logging.
    Logs at DEBUG level to avoid cluttering info logs.
    
    Args:
        logger: Logger instance to use
        func_name: Name of the function being entered
        **kwargs: Function arguments to log
        
    Example:
        >>> log_function_entry(logger, "process_prompt", prompt="test", timeout=30)
        # Logs: "ENTER process_prompt | prompt=test, timeout=30"
    """
    args_str = ", ".join(f"{k}={v!r}" for k, v in kwargs.items())
    logger.debug(f"ENTER {func_name} | {args_str}" if args_str else f"ENTER {func_name}")


def log_function_exit(logger: logging.Logger, func_name: str, result=None, error=None):
    """
    Log exit from a function with its result or error.
    
    Utility function for consistent function exit logging.
    Logs at DEBUG level for success, ERROR level for failures.
    
    Args:
        logger: Logger instance to use
        func_name: Name of the function exiting
        result: Return value (logged at DEBUG level)
        error: Exception if function failed (logged at ERROR level)
        
    Example:
        >>> log_function_exit(logger, "process_prompt", result={"success": True})
        # Logs: "EXIT process_prompt | result={'success': True}"
    """
    if error:
        logger.error(f"EXIT {func_name} | ERROR: {type(error).__name__}: {error}")
    elif result is not None:
        # Truncate long results for readability
        result_str = str(result)
        if len(result_str) > 200:
            result_str = result_str[:200] + "..."
        logger.debug(f"EXIT {func_name} | result={result_str}")
    else:
        logger.debug(f"EXIT {func_name}")
