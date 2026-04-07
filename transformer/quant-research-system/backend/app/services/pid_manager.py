"""
================================================================================
QUANT RESEARCH PIPELINE - PROCESS ID MANAGER
================================================================================

This module provides process tracking and management for Ollama model inference.
It tracks running processes, monitors their resource usage, and provides
kill functionality for stuck or long-running processes.

PURPOSE:
--------
When running large language models locally, inference can sometimes hang or
take excessively long. This module allows:
- Tracking which processes are running model inference
- Monitoring CPU/memory usage of those processes
- Killing stuck processes without restarting the entire server
- Frontend visibility into active background processes

STORAGE:
--------
PIDs are stored in a JSON file at /tmp/quant_research_pids.json for
persistence across requests. The file structure:

    [
        {
            "pid": 12345,
            "type": "ollama_runner",
            "model": "qwen3.5",
            "prompt": "What is arbitrage?...",
            "created_at": "2026-04-07T16:28:28.301931",
            "status": "running"
        }
    ]

PROCESS LIFECYCLE:
------------------
    ┌──────────────────────────────────────────────────────────────┐
    │                    Pipeline.run_researcher()                  │
    └──────────────────────────────────────────────────────────────┘
                              │
                              ▼
    ┌──────────────────────────────────────────────────────────────┐
    │  1. Get current Ollama runner PID (pgrep -f "ollama runner") │
    └──────────────────────────────────────────────────────────────┘
                              │
                              ▼
    ┌──────────────────────────────────────────────────────────────┐
    │  2. Register PID with PIDManager (writes to JSON file)       │
    └──────────────────────────────────────────────────────────────┘
                              │
                              ▼
    ┌──────────────────────────────────────────────────────────────┐
    │  3. Model inference runs (can take 30-120+ seconds)          │
    └──────────────────────────────────────────────────────────────┘
                              │
                              ▼
    ┌──────────────────────────────────────────────────────────────┐
    │  4. Unregister PID on completion/error (removes from file)   │
    └──────────────────────────────────────────────────────────────┘

USAGE:
------
    from app.services.pid_manager import get_pid_manager
    
    pid_manager = get_pid_manager()
    
    # Register a new process
    pid_manager.register_pid(12345, "ollama_runner", model="qwen3.5")
    
    # Check active processes
    active = pid_manager.get_active_pids()
    
    # Kill a stuck process
    result = pid_manager.kill_pid(12345)
    
    # Kill all tracked processes
    results = pid_manager.kill_all()

RELATIONSHIPS:
--------------
- Used by: app.pipeline.pipeline (registers/unregisters PIDs)
- Used by: app.api.routes (exposes PID management endpoints)
- Depends on: psutil (process information and killing)

================================================================================
"""

import os
import json
import signal
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

import psutil

from app.core.logger import setup_daily_logger, log_function_entry, log_function_exit

# =============================================================================
# LOGGER INITIALIZATION
# =============================================================================
logger = setup_daily_logger("pid_manager", log_dir="logs")

# =============================================================================
# CONFIGURATION
# =============================================================================
# Default location for PID storage file
# Using /tmp for easy cleanup on reboot
DEFAULT_PID_FILE = Path("/tmp/quant_research_pids.json")


class PIDManager:
    """
    Manages process IDs for model inference sessions.
    
    This class provides a simple file-based tracking system for Ollama
    runner processes. It allows the application to:
    - Know which model processes are currently running
    - Monitor their resource usage (CPU, memory)
    - Kill stuck or misbehaving processes
    - Clean up terminated processes automatically
    
    The PID data is persisted to a JSON file so it survives server
    restarts (within the same system session).
    
    Attributes:
        pid_file: Path to the JSON file storing PID data
        
    Thread Safety:
        This class performs file I/O and should be used with care in
        multi-threaded scenarios. Currently, the API routes are async
        and shouldn't have concurrency issues.
    """
    
    def __init__(self, pid_file: Optional[Path] = None):
        """
        Initialize the PID manager.
        
        Args:
            pid_file: Path to JSON file for PID storage.
                     Defaults to /tmp/quant_research_pids.json
        """
        log_function_entry(logger, "__init__", pid_file=pid_file)
        
        self.pid_file = pid_file or DEFAULT_PID_FILE
        logger.info(f"PIDManager initializing with file: {self.pid_file}")
        
        self._ensure_file_exists()
        
        logger.debug("PIDManager initialized successfully")
        log_function_exit(logger, "__init__")
    
    def _ensure_file_exists(self):
        """
        Create PID file if it doesn't exist.
        
        Initializes the file with an empty JSON array.
        """
        logger.debug(f"Checking if PID file exists: {self.pid_file}")
        
        if not self.pid_file.exists():
            logger.info(f"PID file not found, creating: {self.pid_file}")
            self._write_pids([])
            logger.debug("Empty PID file created")
        else:
            logger.debug("PID file already exists")
    
    def _read_pids(self) -> List[Dict[str, Any]]:
        """
        Read PIDs from the JSON file.
        
        Returns:
            List of PID dictionaries, or empty list on error
        """
        logger.debug(f"Reading PIDs from {self.pid_file}")
        
        try:
            with open(self.pid_file, 'r') as f:
                data = json.load(f)
                logger.debug(f"Read {len(data)} PID entries")
                return data
                
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode error reading PIDs: {e}")
            logger.warning("Returning empty list and file will be rewritten")
            return []
            
        except FileNotFoundError:
            logger.warning(f"PID file not found: {self.pid_file}")
            return []
            
        except Exception as e:
            logger.error(f"Unexpected error reading PIDs: {type(e).__name__}: {e}", exc_info=True)
            return []
    
    def _write_pids(self, pids: List[Dict[str, Any]]):
        """
        Write PIDs to the JSON file.
        
        Args:
            pids: List of PID dictionaries to write
        """
        logger.debug(f"Writing {len(pids)} PIDs to {self.pid_file}")
        
        try:
            with open(self.pid_file, 'w') as f:
                json.dump(pids, f, indent=2)
            logger.debug("PIDs written successfully")
            
        except Exception as e:
            logger.error(f"Failed to write PIDs: {type(e).__name__}: {e}", exc_info=True)
            raise
    
    def register_pid(
        self, 
        pid: int, 
        process_type: str = "ollama", 
        model: Optional[str] = None, 
        prompt: Optional[str] = None
    ) -> bool:
        """
        Register a new process ID for tracking.
        
        If the PID already exists, updates its timestamp instead
        of creating a duplicate entry.
        
        Args:
            pid: The process ID to register
            process_type: Type of process (e.g., "ollama_runner")
            model: Name of the model being run
            prompt: The prompt being processed (truncated to 100 chars)
            
        Returns:
            True if registration succeeded, False otherwise
        """
        log_function_entry(logger, "register_pid", pid=pid, process_type=process_type, model=model)
        
        try:
            pids = self._read_pids()
            
            # Check if PID already exists (update timestamp if so)
            for p in pids:
                if p['pid'] == pid:
                    logger.debug(f"PID {pid} already registered, updating timestamp")
                    p['updated_at'] = datetime.now().isoformat()
                    self._write_pids(pids)
                    log_function_exit(logger, "register_pid", result=True)
                    return True
            
            # Create new PID entry
            # Truncate prompt to avoid huge JSON entries
            truncated_prompt = None
            if prompt:
                truncated_prompt = (prompt[:100] + '...') if len(prompt) > 100 else prompt
            
            entry = {
                'pid': pid,
                'type': process_type,
                'model': model or 'unknown',
                'prompt': truncated_prompt,
                'created_at': datetime.now().isoformat(),
                'status': 'running'
            }
            
            pids.append(entry)
            self._write_pids(pids)
            
            logger.info(f"Registered PID {pid} (type={process_type}, model={model})")
            log_function_exit(logger, "register_pid", result=True)
            return True
            
        except Exception as e:
            logger.error(f"Failed to register PID {pid}: {type(e).__name__}: {e}", exc_info=True)
            log_function_exit(logger, "register_pid", error=e)
            return False
    
    def unregister_pid(self, pid: int) -> bool:
        """
        Remove a PID from tracking.
        
        Called when inference completes (successfully or with error).
        
        Args:
            pid: The process ID to unregister
            
        Returns:
            True if unregistration succeeded, False otherwise
        """
        log_function_entry(logger, "unregister_pid", pid=pid)
        
        try:
            pids = self._read_pids()
            original_count = len(pids)
            
            pids = [p for p in pids if p['pid'] != pid]
            
            if len(pids) < original_count:
                logger.info(f"Unregistered PID {pid}")
            else:
                logger.debug(f"PID {pid} was not registered (nothing to remove)")
            
            self._write_pids(pids)
            log_function_exit(logger, "unregister_pid", result=True)
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister PID {pid}: {type(e).__name__}: {e}", exc_info=True)
            log_function_exit(logger, "unregister_pid", error=e)
            return False
    
    def get_active_pids(self) -> List[Dict[str, Any]]:
        """
        Get list of active (running) PIDs with current status.
        
        Checks each registered PID to see if it's still running,
        and enriches the data with CPU/memory usage.
        Automatically cleans up entries for terminated processes.
        
        Returns:
            List of dictionaries with PID details:
            - pid: Process ID
            - type: Process type
            - model: Model name
            - prompt: Truncated prompt
            - created_at: When registered
            - status: "running" or "terminated"
            - cpu_percent: Current CPU usage (if running)
            - memory_mb: Current memory usage in MB (if running)
        """
        log_function_entry(logger, "get_active_pids")
        
        pids = self._read_pids()
        active = []
        
        logger.debug(f"Checking {len(pids)} registered PIDs")
        
        for entry in pids:
            pid = entry['pid']
            
            try:
                # Check if process is still running
                process = psutil.Process(pid)
                
                if process.is_running():
                    entry['status'] = 'running'
                    
                    # Get resource usage (cpu_percent needs a small interval)
                    try:
                        entry['cpu_percent'] = process.cpu_percent(interval=0.1)
                        entry['memory_mb'] = process.memory_info().rss / 1024 / 1024
                    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                        logger.debug(f"Could not get stats for PID {pid}: {e}")
                        entry['cpu_percent'] = 0
                        entry['memory_mb'] = 0
                    
                    active.append(entry)
                    logger.debug(f"PID {pid} is running (CPU: {entry['cpu_percent']:.1f}%, MEM: {entry['memory_mb']:.0f}MB)")
                else:
                    entry['status'] = 'terminated'
                    logger.debug(f"PID {pid} is no longer running")
                    
            except psutil.NoSuchProcess:
                entry['status'] = 'terminated'
                logger.debug(f"PID {pid} no longer exists")
                
            except psutil.AccessDenied:
                # Process exists but we can't access it (permissions)
                entry['status'] = 'access_denied'
                logger.warning(f"Access denied for PID {pid}")
                
            except Exception as e:
                logger.error(f"Error checking PID {pid}: {type(e).__name__}: {e}")
                entry['status'] = 'error'
        
        # Clean up terminated processes from file
        if len(active) < len(pids):
            logger.info(f"Cleaning up {len(pids) - len(active)} terminated processes")
            self._write_pids([p for p in pids if p.get('status') == 'running'])
        
        logger.info(f"Found {len(active)} active processes")
        log_function_exit(logger, "get_active_pids", result=f"count={len(active)}")
        
        return active
    
    def kill_pid(self, pid: int) -> Dict[str, Any]:
        """
        Kill a specific process by PID.
        
        Attempts graceful termination (SIGTERM) first, then forces
        kill (SIGKILL) if the process doesn't stop within 5 seconds.
        
        Args:
            pid: The process ID to kill
            
        Returns:
            Dictionary with kill result:
            - pid: The targeted PID
            - success: Whether kill succeeded
            - message: Human-readable result message
        """
        log_function_entry(logger, "kill_pid", pid=pid)
        
        result = {
            'pid': pid,
            'success': False,
            'message': ''
        }
        
        try:
            # Get process info before killing
            process = psutil.Process(pid)
            name = process.name()
            
            logger.info(f"Attempting to kill process: {name} (PID {pid})")
            
            # Try graceful termination first (SIGTERM)
            logger.debug(f"Sending SIGTERM to PID {pid}")
            process.terminate()
            
            try:
                # Wait up to 5 seconds for graceful shutdown
                process.wait(timeout=5)
                result['success'] = True
                result['message'] = f"Process {name} (PID {pid}) terminated gracefully"
                logger.info(result['message'])
                
            except psutil.TimeoutExpired:
                # Process didn't stop, force kill (SIGKILL)
                logger.warning(f"PID {pid} didn't respond to SIGTERM, sending SIGKILL")
                process.kill()
                result['success'] = True
                result['message'] = f"Process {name} (PID {pid}) killed forcefully"
                logger.info(result['message'])
            
            # Remove from tracking
            self.unregister_pid(pid)
            
        except psutil.NoSuchProcess:
            result['message'] = f"Process {pid} not found (already terminated)"
            result['success'] = True  # Consider it a success since it's gone
            logger.info(result['message'])
            self.unregister_pid(pid)
            
        except psutil.AccessDenied:
            result['message'] = f"Access denied: Cannot kill PID {pid} (may need elevated permissions)"
            logger.error(result['message'])
            
        except Exception as e:
            result['message'] = f"Failed to kill PID {pid}: {type(e).__name__}: {str(e)}"
            logger.error(result['message'], exc_info=True)
        
        log_function_exit(logger, "kill_pid", result=result)
        return result
    
    def kill_all(self, process_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Kill all tracked processes, optionally filtered by type.
        
        Args:
            process_type: If provided, only kill processes of this type
            
        Returns:
            List of kill results for each process
        """
        log_function_entry(logger, "kill_all", process_type=process_type)
        
        pids = self._read_pids()
        results = []
        
        logger.info(f"Killing all processes (filter: {process_type or 'none'})")
        
        for entry in pids:
            # Apply type filter if specified
            if process_type and entry.get('type') != process_type:
                logger.debug(f"Skipping PID {entry['pid']} (type {entry.get('type')} != {process_type})")
                continue
            
            result = self.kill_pid(entry['pid'])
            results.append(result)
        
        success_count = sum(1 for r in results if r['success'])
        logger.info(f"Kill all complete: {success_count}/{len(results)} succeeded")
        
        log_function_exit(logger, "kill_all", result=f"{success_count}/{len(results)} killed")
        return results


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================
# Create a singleton instance for use throughout the application
# This ensures all modules use the same PID tracking file

logger.debug("Creating global PIDManager instance...")
pid_manager = PIDManager()
logger.debug("Global PIDManager instance created")


def get_pid_manager() -> PIDManager:
    """
    Get the global PID manager instance.
    
    Returns:
        PIDManager: The singleton PID manager instance
        
    Usage:
        from app.services.pid_manager import get_pid_manager
        pm = get_pid_manager()
    """
    return pid_manager
