"""
PID Manager for tracking and killing Ollama/model processes.
Stores PIDs in a JSON file for persistence across requests.
"""
import os
import json
import signal
import psutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Default location for PID storage
DEFAULT_PID_FILE = Path("/tmp/quant_research_pids.json")


class PIDManager:
    """Manages process IDs for model inference sessions."""
    
    def __init__(self, pid_file: Optional[Path] = None):
        self.pid_file = pid_file or DEFAULT_PID_FILE
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Create PID file if it doesn't exist."""
        if not self.pid_file.exists():
            self._write_pids([])
    
    def _read_pids(self) -> List[Dict[str, Any]]:
        """Read PIDs from file."""
        try:
            with open(self.pid_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _write_pids(self, pids: List[Dict[str, Any]]):
        """Write PIDs to file."""
        with open(self.pid_file, 'w') as f:
            json.dump(pids, f, indent=2)
    
    def register_pid(self, pid: int, process_type: str = "ollama", 
                     model: Optional[str] = None, prompt: Optional[str] = None) -> bool:
        """Register a new process ID."""
        try:
            pids = self._read_pids()
            
            # Check if PID already exists
            for p in pids:
                if p['pid'] == pid:
                    p['updated_at'] = datetime.now().isoformat()
                    self._write_pids(pids)
                    return True
            
            # Add new PID entry
            entry = {
                'pid': pid,
                'type': process_type,
                'model': model or 'unknown',
                'prompt': (prompt[:100] + '...') if prompt and len(prompt) > 100 else prompt,
                'created_at': datetime.now().isoformat(),
                'status': 'running'
            }
            pids.append(entry)
            self._write_pids(pids)
            logger.info(f"Registered PID {pid} ({process_type})")
            return True
        except Exception as e:
            logger.error(f"Failed to register PID {pid}: {e}")
            return False
    
    def unregister_pid(self, pid: int) -> bool:
        """Remove a PID from tracking."""
        try:
            pids = self._read_pids()
            pids = [p for p in pids if p['pid'] != pid]
            self._write_pids(pids)
            return True
        except Exception as e:
            logger.error(f"Failed to unregister PID {pid}: {e}")
            return False
    
    def get_active_pids(self) -> List[Dict[str, Any]]:
        """Get list of active (running) PIDs with current status."""
        pids = self._read_pids()
        active = []
        
        for entry in pids:
            pid = entry['pid']
            try:
                process = psutil.Process(pid)
                if process.is_running():
                    entry['status'] = 'running'
                    entry['cpu_percent'] = process.cpu_percent(interval=0.1)
                    entry['memory_mb'] = process.memory_info().rss / 1024 / 1024
                    active.append(entry)
                else:
                    entry['status'] = 'terminated'
            except psutil.NoSuchProcess:
                entry['status'] = 'terminated'
        
        # Clean up terminated processes
        self._write_pids([p for p in pids if p['status'] == 'running'])
        
        return active
    
    def kill_pid(self, pid: int) -> Dict[str, Any]:
        """Kill a specific process by PID."""
        result = {
            'pid': pid,
            'success': False,
            'message': ''
        }
        
        try:
            process = psutil.Process(pid)
            name = process.name()
            
            # Try graceful termination first
            process.terminate()
            try:
                process.wait(timeout=5)
                result['success'] = True
                result['message'] = f"Process {name} (PID {pid}) terminated gracefully"
            except psutil.TimeoutExpired:
                # Force kill
                process.kill()
                result['success'] = True
                result['message'] = f"Process {name} (PID {pid}) killed forcefully"
            
            self.unregister_pid(pid)
            logger.info(result['message'])
            
        except psutil.NoSuchProcess:
            result['message'] = f"Process {pid} not found (already terminated)"
            self.unregister_pid(pid)
        except Exception as e:
            result['message'] = f"Failed to kill PID {pid}: {str(e)}"
            logger.error(result['message'])
        
        return result
    
    def kill_all(self, process_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Kill all tracked processes, optionally filtered by type."""
        pids = self._read_pids()
        results = []
        
        for entry in pids:
            if process_type and entry.get('type') != process_type:
                continue
            result = self.kill_pid(entry['pid'])
            results.append(result)
        
        return results


# Global instance
pid_manager = PIDManager()


def get_pid_manager() -> PIDManager:
    """Get the global PID manager instance."""
    return pid_manager
