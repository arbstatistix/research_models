#!/usr/bin/env python3
"""
================================================================================
QUANT RESEARCH PIPELINE - APPLICATION ENTRY POINT
================================================================================

This module serves as the main entry point for the Quant Research Pipeline API.
It initializes the Uvicorn ASGI server and starts the FastAPI application.

EXECUTION FLOW:
---------------
1. Script is executed (python run.py or ./run.py)
2. Backend directory is added to Python path for module resolution
3. Configuration settings are loaded from environment variables
4. Daily rotating logger is initialized
5. Uvicorn server starts with the FastAPI app from app.main
6. Server listens on configured host:port (default 0.0.0.0:8000)
7. Hot-reload is enabled for development (watches for file changes)

RELATIONSHIPS:
--------------
- Loads: app.core.config (server settings)
- Loads: app.core.logger (logging setup)
- Starts: app.main:app (FastAPI application)

CONFIGURATION:
--------------
Environment variables (via .env or shell):
- BACKEND_HOST: Server bind address (default: 0.0.0.0)
- BACKEND_PORT: Server port (default: 8000)

USAGE:
------
    # Direct execution
    python run.py
    
    # Or make executable
    chmod +x run.py
    ./run.py

LOG OUTPUT:
-----------
- Console: INFO level and above
- Files: logs/YYYY-MM-DD_*.log (all levels)

================================================================================
"""

import uvicorn
import sys
from pathlib import Path
from datetime import datetime

# =============================================================================
# PATH SETUP
# =============================================================================
# Add the backend directory to Python path to ensure proper module resolution
# This is necessary when running the script directly (not via uvicorn command)
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# =============================================================================
# IMPORTS (after path setup)
# =============================================================================
from app.core.config import settings
from app.core.logger import setup_daily_logger

# =============================================================================
# LOGGER INITIALIZATION
# =============================================================================
# Setup main logger for this entry point module
# This creates daily rotating log files in the logs/ directory
logger = setup_daily_logger("run", log_dir="logs")


def main():
    """
    Main entry point function.
    
    Initializes and starts the Uvicorn ASGI server with the FastAPI application.
    
    Server Configuration:
    - Host: Configurable via BACKEND_HOST env var (default: 0.0.0.0)
    - Port: Configurable via BACKEND_PORT env var (default: 8000)
    - Reload: Enabled for development (auto-restart on code changes)
    - Log Level: INFO (uvicorn's internal logging)
    
    Error Handling:
    - Catches and logs any startup failures
    - Re-raises exceptions after logging for proper exit codes
    
    Returns:
        None
        
    Raises:
        Exception: Any error during server startup is logged and re-raised
    """
    # Log startup banner with configuration details
    logger.info("=" * 80)
    logger.info("QUANT RESEARCH PIPELINE - SERVER STARTING")
    logger.info("=" * 80)
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info(f"Host: {settings.host}")
    logger.info(f"Port: {settings.port}")
    logger.info(f"Reload: True (development mode)")
    logger.info(f"Log Directory: logs/")
    logger.info(f"Python Path: {sys.executable}")
    logger.info("=" * 80)
    
    try:
        # Log pre-startup event
        logger.debug("Initializing Uvicorn server instance...")
        
        # Start Uvicorn with the FastAPI app
        # The app is loaded from app.main:app (module:variable)
        uvicorn.run(
            "app.main:app",          # FastAPI app location
            host=settings.host,       # Bind address
            port=settings.port,       # Port number
            reload=True,              # Enable hot-reload for development
            log_level="info"          # Uvicorn's internal log level
        )
        
        # This line is reached when server shuts down gracefully
        logger.info("Server shutdown complete")
        
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        logger.info("Server stopped by user (KeyboardInterrupt)")
        
    except Exception as e:
        # Log critical errors with full traceback
        logger.critical(f"Failed to start server: {type(e).__name__}: {e}", exc_info=True)
        logger.critical("Server startup aborted due to critical error")
        raise  # Re-raise for proper exit code


# =============================================================================
# SCRIPT ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    main()
