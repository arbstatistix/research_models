"""
================================================================================
QUANT RESEARCH PIPELINE - FASTAPI APPLICATION
================================================================================

This module defines the main FastAPI application instance and its configuration.
It serves as the central hub that ties together all API routes, middleware,
and application lifecycle events.

EXECUTION FLOW:
---------------
1. Logger is initialized for this module
2. FastAPI app instance is created with metadata
3. CORS middleware is configured for frontend access
4. API router is mounted at /api prefix
5. Lifecycle events (startup/shutdown) are registered
6. Global exception handler catches unhandled errors
7. Root and health endpoints are defined

RELATIONSHIPS:
--------------
- Imports: app.api.routes (API endpoints)
- Imports: app.core.logger (logging utilities)
- Called by: run.py via Uvicorn
- Serves: Frontend at localhost:5173

REQUEST FLOW:
-------------
    Client Request
         │
         ▼
    ┌─────────────┐
    │ CORS Check  │  ← Middleware validates origin
    └─────────────┘
         │
         ▼
    ┌─────────────┐
    │   Router    │  ← Routes to /api/* endpoints
    └─────────────┘
         │
         ▼
    ┌─────────────┐
    │  Handler    │  ← Specific endpoint function
    └─────────────┘
         │
         ▼
    ┌─────────────┐
    │  Response   │  ← JSON response to client
    └─────────────┘

ENDPOINTS:
----------
- GET /           : Root endpoint (API info)
- GET /health     : Health check endpoint
- /api/*          : Research pipeline endpoints (see routes.py)

MIDDLEWARE:
-----------
- CORS: Allows requests from frontend origins

ERROR HANDLING:
---------------
- Global exception handler catches all unhandled errors
- Returns structured JSON error response
- Logs full traceback for debugging

================================================================================
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.logger import setup_daily_logger

# =============================================================================
# LOGGER INITIALIZATION
# =============================================================================
# Setup daily logging before creating the app
# This ensures all startup events are captured
logger = setup_daily_logger("main", log_dir="logs")

logger.debug("Initializing FastAPI application...")

# =============================================================================
# FASTAPI APPLICATION INSTANCE
# =============================================================================
# Create the main FastAPI application with metadata for documentation
app = FastAPI(
    title="Quant Research Pipeline API",
    description="""
    API for quantitative research prompt processing.
    
    Features:
    - Two-stage pipeline: prompt refinement + expert research
    - Local LLM inference via Ollama
    - Process management for model instances
    - Comprehensive logging and error handling
    
    See /api/research for the main endpoint.
    """,
    version="1.0.0",
    docs_url="/docs",           # Swagger UI
    redoc_url="/redoc",         # ReDoc documentation
    openapi_url="/openapi.json" # OpenAPI schema
)

logger.debug("FastAPI app instance created")

# =============================================================================
# CORS MIDDLEWARE CONFIGURATION
# =============================================================================
# Configure Cross-Origin Resource Sharing to allow frontend requests
# This is required because frontend (port 5173) and backend (port 8000)
# are on different origins

ALLOWED_ORIGINS = [
    "http://localhost:5173",    # Vite dev server
    "http://127.0.0.1:5173",    # Vite dev server (alt)
    "http://localhost:3000",    # Alternative React port
    "http://127.0.0.1:3000",    # Alternative React port (alt)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Origins that can make requests
    allow_credentials=True,          # Allow cookies/auth headers
    allow_methods=["*"],             # Allow all HTTP methods
    allow_headers=["*"],             # Allow all headers
)

logger.info(f"CORS middleware configured for origins: {ALLOWED_ORIGINS}")

# =============================================================================
# API ROUTER MOUNTING
# =============================================================================
# Mount the main API router at /api prefix
# All research pipeline endpoints are under this prefix
app.include_router(router, prefix="/api", tags=["research"])

logger.info("API router mounted at /api prefix")

# =============================================================================
# LIFECYCLE EVENT HANDLERS
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """
    Application startup event handler.
    
    Called once when the application starts, before accepting requests.
    Used for initialization tasks and logging.
    
    Actions:
    - Logs startup timestamp
    - Logs configuration summary
    - Could initialize database connections, caches, etc.
    """
    logger.info("=" * 80)
    logger.info("QUANT RESEARCH PIPELINE API - STARTUP")
    logger.info("=" * 80)
    logger.info(f"Startup time: {datetime.now().isoformat()}")
    logger.info(f"Environment: development (reload enabled)")
    logger.info(f"Documentation: http://localhost:8000/docs")
    logger.info(f"Health check: http://localhost:8000/health")
    logger.info("=" * 80)
    logger.debug("Startup event handler completed")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown event handler.
    
    Called once when the application is shutting down.
    Used for cleanup tasks and logging.
    
    Actions:
    - Logs shutdown timestamp
    - Could close database connections, flush caches, etc.
    """
    logger.info("=" * 80)
    logger.info("QUANT RESEARCH PIPELINE API - SHUTDOWN")
    logger.info("=" * 80)
    logger.info(f"Shutdown time: {datetime.now().isoformat()}")
    logger.info("Cleaning up resources...")
    logger.debug("Shutdown event handler completed")
    logger.info("=" * 80)


# =============================================================================
# GLOBAL EXCEPTION HANDLER
# =============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors.
    
    Catches any exception that isn't handled by specific endpoint handlers.
    Returns a structured JSON error response and logs the full traceback.
    
    Args:
        request: The FastAPI Request object
        exc: The exception that was raised
        
    Returns:
        JSONResponse with error details and 500 status code
        
    Note:
        This handler should rarely be triggered if endpoints handle
        their own errors properly. It serves as a safety net.
    """
    # Log comprehensive error information
    logger.error("=" * 80)
    logger.error("UNHANDLED EXCEPTION CAUGHT BY GLOBAL HANDLER")
    logger.error("=" * 80)
    logger.error(f"Exception type: {type(exc).__name__}")
    logger.error(f"Exception message: {str(exc)}")
    logger.error(f"Request path: {request.url.path}")
    logger.error(f"Request method: {request.method}")
    logger.error(f"Client host: {request.client.host if request.client else 'unknown'}")
    logger.error(f"Full traceback:", exc_info=True)
    logger.error("=" * 80)
    
    # Return structured error response
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "detail": "An unexpected error occurred. Check server logs for details.",
            "path": request.url.path,
            "timestamp": datetime.now().isoformat()
        }
    )


# =============================================================================
# ROOT ENDPOINTS
# =============================================================================

@app.get("/", tags=["info"])
async def root():
    """
    Root endpoint - API information.
    
    Returns basic information about the API for discovery purposes.
    Useful for confirming the server is running.
    
    Returns:
        dict: API name, status, and version
    """
    logger.debug("Root endpoint accessed")
    logger.info("GET / - Root endpoint request")
    
    return {
        "message": "Quant Research Pipeline API",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["info"])
async def health():
    """
    Health check endpoint.
    
    Returns the current health status of the API.
    Used by load balancers, monitoring systems, and the frontend
    to verify the backend is responsive.
    
    Returns:
        dict: Health status and current timestamp
    """
    logger.debug("Health check endpoint accessed")
    
    # Could add more comprehensive checks here:
    # - Database connectivity
    # - Ollama service availability
    # - Memory/CPU usage
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "quant-research-api"
    }
