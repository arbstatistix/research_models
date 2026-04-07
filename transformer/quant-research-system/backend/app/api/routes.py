"""
================================================================================
QUANT RESEARCH PIPELINE - API ROUTES
================================================================================

This module defines all API endpoints for the quant research pipeline.
It handles HTTP requests, validates input, calls the pipeline, and returns
structured responses.

ENDPOINT OVERVIEW:
------------------
Research:
    POST /api/research      Process a prompt through the research pipeline
    GET  /api/models        Get current model configuration

Process Management:
    GET  /api/pids          List active model processes
    POST /api/pids/{pid}/kill   Kill a specific process
    POST /api/pids/kill-all     Kill all tracked processes
    GET  /api/server/kill       Emergency server shutdown

REQUEST FLOW (POST /api/research):
----------------------------------
    1. Request received with JSON body {"prompt": "..."}
    2. Validate prompt is not empty
    3. Submit to pipeline via thread pool executor
    4. Pipeline refines prompt (if needed)
    5. Pipeline sends to researcher model
    6. Return structured response with answer

    Client                    Routes                    Pipeline
      │                         │                          │
      │  POST /api/research     │                          │
      │────────────────────────>│                          │
      │                         │  validate request        │
      │                         │──────────────────────────│
      │                         │                          │
      │                         │  run_in_executor()       │
      │                         │─────────────────────────>│
      │                         │                          │ refine_prompt()
      │                         │                          │───────────────
      │                         │                          │ run_researcher()
      │                         │                          │───────────────
      │                         │      result dict         │
      │                         │<─────────────────────────│
      │                         │                          │
      │   PipelineResponse      │                          │
      │<────────────────────────│                          │
      │                         │                          │

THREAD POOL:
------------
The pipeline runs in a separate thread pool to prevent blocking the
FastAPI event loop. This ensures:
- Health checks remain responsive during inference
- PID management endpoints are accessible
- Multiple requests can queue

ERROR HANDLING:
---------------
- 400: Empty prompt or validation errors
- 500: Pipeline errors, Ollama errors, unexpected exceptions
- All errors are logged with full tracebacks

RELATIONSHIPS:
--------------
- Imports: app.pipeline.pipeline (research logic)
- Imports: app.services.pid_manager (process tracking)
- Imports: app.schemas.* (request/response models)
- Mounted by: app.main at /api prefix

================================================================================
"""

import logging
import traceback
import os
import signal
import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from app.schemas.request import PromptRequest
from app.schemas.response import PipelineResponse
from app.pipeline.pipeline import QuantResearchPipeline
from app.core.config import get_pipeline_config
from app.core.logger import setup_daily_logger, log_function_entry, log_function_exit
from app.services.pid_manager import get_pid_manager, PIDManager

# =============================================================================
# LOGGER INITIALIZATION
# =============================================================================
logger = setup_daily_logger("routes", log_dir="logs")

# =============================================================================
# THREAD POOL FOR NON-BLOCKING INFERENCE
# =============================================================================
# Create a thread pool executor for running blocking pipeline calls
# This prevents the FastAPI event loop from being blocked during inference
# max_workers=2 allows for one active request and one queued
pipeline_executor = ThreadPoolExecutor(max_workers=2)
logger.info("Thread pool executor created with max_workers=2")

# =============================================================================
# API ROUTER
# =============================================================================
router = APIRouter()
logger.debug("APIRouter instance created")

# =============================================================================
# PIPELINE INITIALIZATION
# =============================================================================
# Initialize the pipeline singleton at module load time
# This is done once and reused for all requests
logger.info("=" * 80)
logger.info("INITIALIZING QUANT RESEARCH PIPELINE")
logger.info("=" * 80)

try:
    # Load configuration from environment
    pipeline_config = get_pipeline_config()
    logger.debug(f"Pipeline config loaded: {pipeline_config}")
    
    # Create pipeline instance
    pipeline = QuantResearchPipeline(pipeline_config, log_dir="logs")
    logger.info("QuantResearchPipeline initialized successfully")
    
except Exception as e:
    logger.critical(f"FATAL: Failed to initialize pipeline: {type(e).__name__}: {e}", exc_info=True)
    logger.critical("Application cannot start without a working pipeline")
    raise

logger.info("=" * 80)


# =============================================================================
# RESEARCH ENDPOINT
# =============================================================================

@router.post("/research", response_model=PipelineResponse)
async def process_research_prompt(request: PromptRequest, req: Request) -> PipelineResponse:
    """
    Process a research prompt through the quantitative research pipeline.
    
    This is the main endpoint for the application. It takes a user prompt,
    optionally refines it for clarity, and sends it to the researcher model
    for a detailed, expert-level response.
    
    Request Flow:
        1. Validate prompt is not empty
        2. Log request details (client IP, prompt preview)
        3. Submit to pipeline via thread pool (non-blocking)
        4. Wait for pipeline to complete
        5. Convert result to Pydantic model
        6. Log outcome (success/failure, timing)
        7. Return structured response
    
    Args:
        request: PromptRequest with the user's prompt
        req: FastAPI Request object for client info
        
    Returns:
        PipelineResponse: Structured response with:
            - success: Whether processing succeeded
            - used_refinement: Whether prompt was refined
            - original_prompt: The original user input
            - prompt_sent_to_researcher: What was actually sent to model
            - final_answer: The generated research response
            - error fields if failed
            
    Raises:
        HTTPException(400): If prompt is empty
        HTTPException(500): If pipeline fails unexpectedly
        
    Example:
        POST /api/research
        {"prompt": "What is the Black-Scholes model?"}
        
        Response:
        {
            "success": true,
            "used_refinement": true,
            "original_prompt": "What is the Black-Scholes model?",
            "prompt_sent_to_researcher": "Derive the Black-Scholes PDE...",
            "final_answer": "## Black-Scholes Model\\n\\nThe Black-Scholes..."
        }
    """
    # ==========================================================================
    # REQUEST LOGGING
    # ==========================================================================
    client_host = req.client.host if req.client else "unknown"
    request_id = datetime.now().strftime("%H%M%S%f")  # Simple request ID for tracing
    
    logger.info("=" * 80)
    logger.info(f"[{request_id}] NEW RESEARCH REQUEST")
    logger.info("=" * 80)
    logger.info(f"[{request_id}] Client IP: {client_host}")
    logger.info(f"[{request_id}] Timestamp: {datetime.now().isoformat()}")
    logger.info(f"[{request_id}] Prompt length: {len(request.prompt)} chars")
    logger.info(f"[{request_id}] Prompt preview: {request.prompt[:100]}{'...' if len(request.prompt) > 100 else ''}")
    logger.debug(f"[{request_id}] Full prompt: {request.prompt}")
    
    try:
        # ======================================================================
        # INPUT VALIDATION
        # ======================================================================
        if not request.prompt or not request.prompt.strip():
            logger.warning(f"[{request_id}] REJECTED: Empty prompt received")
            raise HTTPException(status_code=400, detail="Prompt cannot be empty")
        
        logger.debug(f"[{request_id}] Prompt validation passed")
        
        # ======================================================================
        # PIPELINE EXECUTION
        # ======================================================================
        logger.info(f"[{request_id}] Submitting to pipeline executor...")
        start_time = datetime.now()
        
        # Run the blocking pipeline in a thread pool
        # This prevents blocking the FastAPI event loop
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            pipeline_executor,
            pipeline.process_prompt,
            request.prompt
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"[{request_id}] Pipeline execution completed in {duration:.2f}s")
        logger.debug(f"[{request_id}] Raw result keys: {result.keys()}")
        
        # ======================================================================
        # RESPONSE CONSTRUCTION
        # ======================================================================
        response = PipelineResponse(**result)
        
        # ======================================================================
        # OUTCOME LOGGING
        # ======================================================================
        if response.success:
            logger.info(f"[{request_id}] ✓ SUCCESS")
            logger.info(f"[{request_id}]   Duration: {duration:.2f}s")
            logger.info(f"[{request_id}]   Refinement used: {response.used_refinement}")
            logger.info(f"[{request_id}]   Answer length: {len(response.final_answer)} chars")
            logger.debug(f"[{request_id}]   Answer preview: {response.final_answer[:200]}...")
        else:
            logger.error(f"[{request_id}] ✗ FAILED")
            logger.error(f"[{request_id}]   Duration: {duration:.2f}s")
            logger.error(f"[{request_id}]   Error type: {response.error_type}")
            logger.error(f"[{request_id}]   Error: {response.error}")
        
        logger.info("=" * 80)
        return response

    except HTTPException:
        # Re-raise HTTP exceptions without wrapping
        raise
        
    except Exception as e:
        # Log unexpected errors with full traceback
        logger.error(f"[{request_id}] UNEXPECTED ERROR: {type(e).__name__}: {e}")
        logger.error(f"[{request_id}] Traceback:\n{traceback.format_exc()}")
        logger.error("=" * 80)
        raise HTTPException(status_code=500, detail="Internal server error")


# =============================================================================
# MODELS ENDPOINT
# =============================================================================

@router.get("/models")
async def list_available_models():
    """
    List the current pipeline model configuration.
    
    Returns the models being used for refinement and research,
    along with their temperature settings. Useful for debugging
    and monitoring.
    
    Returns:
        dict: Current model configuration
            - refiner_model: Model for prompt refinement
            - researcher_model: Model for research generation
            - max_refine_words: Word limit for refinement
            - refiner_temperature: Refiner sampling temperature
            - researcher_temperature: Researcher sampling temperature
    """
    logger.info("GET /api/models - Models configuration requested")
    log_function_entry(logger, "list_available_models")
    
    try:
        config = get_pipeline_config()
        
        result = {
            "refiner_model": config.refiner_model,
            "researcher_model": config.researcher_model,
            "max_refine_words": config.max_refine_words,
            "refiner_temperature": config.refiner_temperature,
            "researcher_temperature": config.researcher_temperature,
        }
        
        logger.debug(f"Returning config: {result}")
        log_function_exit(logger, "list_available_models", result=result)
        return result
        
    except Exception as e:
        logger.error(f"Error listing models: {type(e).__name__}: {e}", exc_info=True)
        log_function_exit(logger, "list_available_models", error=e)
        raise HTTPException(status_code=500, detail="Failed to retrieve model configuration")


# =============================================================================
# PID MANAGEMENT ENDPOINTS
# =============================================================================

@router.get("/pids")
async def list_active_pids():
    """
    List all active (running) process IDs being tracked.
    
    Returns information about Ollama runner processes that are currently
    executing model inference. Useful for monitoring and debugging stuck
    processes.
    
    Returns:
        dict: Active process information
            - success: Always true if endpoint succeeds
            - count: Number of active processes
            - pids: List of process details (pid, model, cpu%, memory)
    """
    logger.info("GET /api/pids - Active PIDs requested")
    log_function_entry(logger, "list_active_pids")
    
    try:
        pid_manager = get_pid_manager()
        active_pids = pid_manager.get_active_pids()
        
        logger.info(f"Found {len(active_pids)} active processes")
        logger.debug(f"Active PIDs: {[p['pid'] for p in active_pids]}")
        
        result = {
            "success": True,
            "count": len(active_pids),
            "pids": active_pids
        }
        
        log_function_exit(logger, "list_active_pids", result=f"count={len(active_pids)}")
        return result
        
    except Exception as e:
        logger.error(f"Error listing PIDs: {type(e).__name__}: {e}", exc_info=True)
        log_function_exit(logger, "list_active_pids", error=e)
        raise HTTPException(status_code=500, detail=f"Failed to list PIDs: {str(e)}")


@router.post("/pids/{pid}/kill")
async def kill_process(pid: int):
    """
    Kill a specific process by PID.
    
    Attempts graceful termination first (SIGTERM), then forces kill
    (SIGKILL) if the process doesn't stop within 5 seconds.
    
    Args:
        pid: Process ID to kill
        
    Returns:
        dict: Kill result
            - pid: The targeted PID
            - success: Whether kill succeeded
            - message: Human-readable result message
    """
    logger.info(f"POST /api/pids/{pid}/kill - Kill request for PID {pid}")
    log_function_entry(logger, "kill_process", pid=pid)
    
    try:
        pid_manager = get_pid_manager()
        result = pid_manager.kill_pid(pid)
        
        if result['success']:
            logger.info(f"Successfully killed PID {pid}: {result['message']}")
        else:
            logger.warning(f"Failed to kill PID {pid}: {result['message']}")
        
        log_function_exit(logger, "kill_process", result=result)
        return result
        
    except Exception as e:
        logger.error(f"Error killing PID {pid}: {type(e).__name__}: {e}", exc_info=True)
        log_function_exit(logger, "kill_process", error=e)
        raise HTTPException(status_code=500, detail=f"Failed to kill process: {str(e)}")


@router.post("/pids/kill-all")
async def kill_all_processes(process_type: Optional[str] = None):
    """
    Kill all tracked processes, optionally filtered by type.
    
    Args:
        process_type: Optional filter (e.g., "ollama_runner")
        
    Returns:
        dict: Bulk kill results
            - success: Always true if endpoint succeeds
            - total: Number of processes targeted
            - killed: Number successfully killed
            - results: Individual kill results
    """
    logger.info(f"POST /api/pids/kill-all - Kill all request (type={process_type})")
    log_function_entry(logger, "kill_all_processes", process_type=process_type)
    
    try:
        pid_manager = get_pid_manager()
        results = pid_manager.kill_all(process_type=process_type)
        success_count = sum(1 for r in results if r['success'])
        
        logger.info(f"Kill all complete: {success_count}/{len(results)} killed")
        
        result = {
            "success": True,
            "total": len(results),
            "killed": success_count,
            "results": results
        }
        
        log_function_exit(logger, "kill_all_processes", result=f"killed={success_count}/{len(results)}")
        return result
        
    except Exception as e:
        logger.error(f"Error killing all PIDs: {type(e).__name__}: {e}", exc_info=True)
        log_function_exit(logger, "kill_all_processes", error=e)
        raise HTTPException(status_code=500, detail=f"Failed to kill processes: {str(e)}")


@router.get("/server/kill")
async def kill_server():
    """
    Emergency server shutdown endpoint.
    
    Initiates a graceful server shutdown after a 1-second delay.
    This allows the response to be sent before the server stops.
    
    USE WITH CAUTION: This will stop the entire backend server.
    
    Returns:
        dict: Shutdown confirmation
            - success: Always true if shutdown initiated
            - message: Shutdown message
            - pid: The server's process ID
    """
    logger.warning("GET /api/server/kill - EMERGENCY SERVER SHUTDOWN REQUESTED")
    log_function_entry(logger, "kill_server")
    
    try:
        import threading
        
        server_pid = os.getpid()
        logger.warning(f"Initiating shutdown of server PID {server_pid} in 1 second...")
        
        def shutdown():
            """Delayed shutdown to allow response to be sent."""
            import time
            time.sleep(1)
            logger.critical("EXECUTING SERVER SHUTDOWN")
            os.kill(server_pid, signal.SIGTERM)
        
        # Start shutdown in background thread
        threading.Thread(target=shutdown, daemon=True).start()
        
        result = {
            "success": True,
            "message": "Server shutting down in 1 second...",
            "pid": server_pid
        }
        
        log_function_exit(logger, "kill_server", result=result)
        return result
        
    except Exception as e:
        logger.error(f"Error killing server: {type(e).__name__}: {e}", exc_info=True)
        log_function_exit(logger, "kill_server", error=e)
        raise HTTPException(status_code=500, detail=f"Failed to kill server: {str(e)}")
