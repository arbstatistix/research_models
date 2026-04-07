import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_daily_logger(name: str, log_dir: str = "logs", level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with daily rotating file handlers.
    
    Creates separate log files per date:
    - logs/YYYY-MM-DD_all.log (all messages)
    - logs/YYYY-MM-DD_info.log (info and above)
    - logs/YYYY-MM-DD_warnings.log (warnings and above)
    - logs/YYYY-MM-DD_errors.log (errors only)
    
    Args:
        name: Logger name
        log_dir: Directory for log files
        level: Minimum logging level
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create logs directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Get current date for log file naming
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # Formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Console handler (INFO and above)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # File handler for ALL logs (DEBUG and above)
    all_logs_file = log_path / f"{current_date}_all.log"
    all_handler = logging.FileHandler(all_logs_file, encoding='utf-8')
    all_handler.setLevel(logging.DEBUG)
    all_handler.setFormatter(detailed_formatter)
    logger.addHandler(all_handler)
    
    # File handler for INFO logs (INFO and above)
    info_logs_file = log_path / f"{current_date}_info.log"
    info_handler = logging.FileHandler(info_logs_file, encoding='utf-8')
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(detailed_formatter)
    logger.addHandler(info_handler)
    
    # File handler for WARNING logs (WARNING and above)
    warning_logs_file = log_path / f"{current_date}_warnings.log"
    warning_handler = logging.FileHandler(warning_logs_file, encoding='utf-8')
    warning_handler.setLevel(logging.WARNING)
    warning_handler.setFormatter(detailed_formatter)
    logger.addHandler(warning_handler)
    
    # File handler for ERROR logs (ERROR only)
    error_logs_file = log_path / f"{current_date}_errors.log"
    error_handler = logging.FileHandler(error_logs_file, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    logger.addHandler(error_handler)
    
    logger.info(f"Logger initialized. Log files: {log_path}/{current_date}_*.log")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get existing logger or create new one with default settings."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_daily_logger(name)
    return logger
