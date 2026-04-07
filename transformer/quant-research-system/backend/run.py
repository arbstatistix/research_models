#!/usr/bin/env python3
"""
Entry point for the Quant Research Pipeline API.
"""
import uvicorn
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.core.logger import setup_daily_logger

# Setup main logger
logger = setup_daily_logger("run", log_dir="logs")

def main():
    """Run the FastAPI application."""
    logger.info("=" * 80)
    logger.info("Starting Uvicorn server...")
    logger.info(f"Host: {settings.host}")
    logger.info(f"Port: {settings.port}")
    logger.info(f"Reload: True")
    logger.info("=" * 80)
    
    try:
        uvicorn.run(
            "app.main:app",
            host=settings.host,
            port=settings.port,
            reload=True,
            log_level="info"
        )
    except Exception as e:
        logger.critical(f"Failed to start server: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
