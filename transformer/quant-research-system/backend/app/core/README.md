# Core Module

Core utilities for configuration and logging.

## Files

- `__init__.py` - Package marker
- `config.py` - Configuration management
- `logger.py` - Logging system

## Configuration (config.py)

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REFINER_MODEL` | `qwen3.5` | Model for prompt refinement |
| `RESEARCHER_MODEL` | `qwen3.5` | Model for research generation |
| `MAX_REFINE_WORDS` | `250` | Skip refinement above this |
| `REFINER_TEMPERATURE` | `0.0` | Refiner sampling temp |
| `RESEARCHER_TEMPERATURE` | `0.2` | Researcher sampling temp |
| `BACKEND_HOST` | `0.0.0.0` | Server bind address |
| `BACKEND_PORT` | `8000` | Server port |

### Usage

```python
from app.core.config import get_pipeline_config, settings

# Pipeline configuration
config = get_pipeline_config()
print(config.refiner_model)  # "qwen3.5"

# Server settings
print(settings.host)  # "0.0.0.0"
print(settings.port)  # 8000
```

## Logging (logger.py)

### Log Files

Daily rotating logs in `backend/logs/`:

```
logs/
├── 2026-04-07_all.log       # DEBUG and above
├── 2026-04-07_info.log      # INFO and above
├── 2026-04-07_warnings.log  # WARNING and above
└── 2026-04-07_errors.log    # ERROR and above
```

### Log Format

**File logs:**
```
2026-04-07 16:28:03 - pipeline - INFO - [pipeline.py:42] - Processing prompt
```

**Console logs:**
```
16:28:03 - INFO - Processing prompt
```

### Usage

```python
from app.core.logger import setup_daily_logger, get_logger

# Create new logger
logger = setup_daily_logger("my_module", log_dir="logs")

# Get existing logger
logger = get_logger("my_module")

# Log at different levels
logger.debug("Detailed info")    # Only in _all.log
logger.info("General info")      # In _all.log and _info.log
logger.warning("Warning")        # In _all, _info, _warnings
logger.error("Error occurred")   # In all files
logger.critical("Critical!")     # In all files

# Log with traceback
try:
    risky_operation()
except Exception as e:
    logger.error(f"Failed: {e}", exc_info=True)
```

### Utility Functions

```python
from app.core.logger import log_function_entry, log_function_exit

def my_function(arg1, arg2):
    log_function_entry(logger, "my_function", arg1=arg1, arg2=arg2)
    # Logs: "ENTER my_function | arg1='value1', arg2='value2'"
    
    try:
        result = do_work()
        log_function_exit(logger, "my_function", result=result)
        return result
    except Exception as e:
        log_function_exit(logger, "my_function", error=e)
        raise
```

## Design Decisions

### Why daily rotation?
- Natural log organization by date
- Easy to find logs for specific incidents
- Simple cleanup (delete old date files)

### Why multiple severity files?
- Quick access to errors without grep
- Smaller files for specific concerns
- Different retention policies possible

### Why environment variables?
- No code changes for configuration
- Docker/Kubernetes friendly
- Secure for sensitive values
