import logging
import traceback
import os
import signal
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from app.schemas.request import PromptRequest
from app.schemas.response import PipelineResponse
from app.pipeline.pipeline import QuantResearchPipeline
from app.core.config import get_pipeline_config
from app.core.logger import setup_daily_logger
from app.services.pid_manager import get_pid_manager, PIDManager
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Thread pool for running blocking pipeline calls
pipeline_executor = ThreadPoolExecutor(max_workers=2)

router = APIRouter()

# Initialize daily logger for routes
logger = setup_daily_logger("routes", log_dir="logs")

# Initialize pipeline singleton with logging
logger.info("Initializing QuantResearchPipeline...")
try:
    pipeline_config = get_pipeline_config()
    pipeline = QuantResearchPipeline(pipeline_config, log_dir="logs")
    logger.info("QuantResearchPipeline initialized successfully")
except Exception as e:
    logger.critical(f"Failed to initialize pipeline: {e}", exc_info=True)
    raise


@router.post("/research", response_model=PipelineResponse)
async def process_research_prompt(request: PromptRequest, req: Request) -> PipelineResponse:
    """
    Process a research prompt through the quantitative research pipeline.
    The pipeline may refine the prompt and then run it through a researcher model.
    """
    client_host = req.client.host if req.client else "unknown"
    logger.info("=" * 80)
    logger.info(f"RESEARCH REQUEST from {client_host}")
    logger.info(f"Prompt: {request.prompt[:100]}...")
    logger.info("=" * 80)
    
    try:
        # Validate input
        if not request.prompt or not request.prompt.strip():
            logger.warning("Empty prompt received")
            raise HTTPException(status_code=400, detail="Prompt cannot be empty")
        
        # Process the prompt through the pipeline (in thread pool to avoid blocking)
        logger.info("Starting pipeline processing...")
        start_time = datetime.now()
        
        # Run blocking pipeline in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            pipeline_executor,
            pipeline.process_prompt,
            request.prompt
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Convert dict result to Pydantic model
        response = PipelineResponse(**result)
        
        # Log results
        if response.success:
            logger.info(f"✓ Request completed successfully in {duration:.2f}s")
            logger.info(f"  - Refinement used: {response.used_refinement}")
            logger.info(f"  - Answer length: {len(response.final_answer)} chars")
        else:
            logger.error(f"✗ Request failed after {duration:.2f}s")
            logger.error(f"  - Error type: {response.error_type}")
            logger.error(f"  - Error: {response.error}")
        
        logger.info("=" * 80)
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in research endpoint: {e}", exc_info=True)
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/models")
async def list_available_models():
    """List configuration of current pipeline models."""
    logger.info("Models endpoint accessed")
    try:
        config = get_pipeline_config()
        return {
            "refiner_model": config.refiner_model,
            "researcher_model": config.researcher_model,
            "max_refine_words": config.max_refine_words,
            "refiner_temperature": config.refiner_temperature,
            "researcher_temperature": config.researcher_temperature,
        }
    except Exception as e:
        logger.error(f"Error listing models: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve model configuration")


# ============================================================================
# PID MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/pids")
async def list_active_pids():
    """List all active (running) process IDs being tracked."""
    try:
        pid_manager = get_pid_manager()
        active_pids = pid_manager.get_active_pids()
        return {
            "success": True,
            "count": len(active_pids),
            "pids": active_pids
        }
    except Exception as e:
        logger.error(f"Error listing PIDs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list PIDs: {str(e)}")


@router.post("/pids/{pid}/kill")
async def kill_process(pid: int):
    """Kill a specific process by PID."""
    try:
        pid_manager = get_pid_manager()
        result = pid_manager.kill_pid(pid)
        return result
    except Exception as e:
        logger.error(f"Error killing PID {pid}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to kill process: {str(e)}")


@router.post("/pids/kill-all")
async def kill_all_processes(process_type: str = None):
    """Kill all tracked processes, optionally filtered by type."""
    try:
        pid_manager = get_pid_manager()
        results = pid_manager.kill_all(process_type=process_type)
        success_count = sum(1 for r in results if r['success'])
        return {
            "success": True,
            "total": len(results),
            "killed": success_count,
            "results": results
        }
    except Exception as e:
        logger.error(f"Error killing all PIDs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to kill processes: {str(e)}")


@router.get("/server/kill")
async def kill_server():
    """Kill the backend server itself (for emergency restart)."""
    try:
        import threading
        def shutdown():
            import time
            time.sleep(1)
            os.kill(os.getpid(), signal.SIGTERM)
        
        threading.Thread(target=shutdown, daemon=True).start()
        return {
            "success": True,
            "message": "Server shutting down in 1 second...",
            "pid": os.getpid()
        }
    except Exception as e:
        logger.error(f"Error killing server: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to kill server: {str(e)}")
