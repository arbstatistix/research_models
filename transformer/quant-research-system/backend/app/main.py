import logging
import sys
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.routes import router
from app.core.logger import setup_daily_logger

# Setup daily logging before creating app
logger = setup_daily_logger("main", log_dir="logs")

app = FastAPI(
    title="Quant Research Pipeline API",
    description="API for quantitative research prompt processing with refinement and researcher models",
    version="1.0.0"
)

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router - FIXED: use include_router not add_router
app.include_router(router, prefix="/api", tags=["research"])

@app.on_event("startup")
async def startup_event():
    """Log application startup."""
    logger.info("=" * 80)
    logger.info("Quant Research Pipeline API starting up")
    logger.info(f"Startup time: {datetime.now().isoformat()}")
    logger.info("=" * 80)

@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown."""
    logger.info("=" * 80)
    logger.info("Quant Research Pipeline API shutting down")
    logger.info(f"Shutdown time: {datetime.now().isoformat()}")
    logger.info("=" * 80)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {type(exc).__name__}: {exc}", exc_info=True)
    logger.error(f"Request path: {request.url.path}")
    logger.error(f"Request method: {request.method}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "detail": "An unexpected error occurred. Check logs for details."
        }
    )

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Quant Research Pipeline API", "status": "running"}

@app.get("/health")
async def health():
    logger.debug("Health check endpoint accessed")
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}