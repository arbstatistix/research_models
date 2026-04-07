# Services Module

External service integrations and utilities.

## Files

- `__init__.py` - Package marker
- `ollama_client.py` - Ollama API wrapper (optional)
- `pid_manager.py` - Process tracking and management

## PID Manager

### Purpose

When running large language models, inference can:
- Take a very long time (30-120+ seconds)
- Hang indefinitely due to bugs or resource issues
- Consume excessive CPU/memory

The PID Manager allows:
- Tracking which processes are running inference
- Monitoring their resource usage
- Killing stuck processes without server restart

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      PID Manager                             │
│                                                             │
│  ┌─────────────┐    ┌─────────────────────────────────┐    │
│  │ JSON File   │◄───│ /tmp/quant_research_pids.json   │    │
│  └─────────────┘    └─────────────────────────────────┘    │
│         ▲                                                   │
│         │                                                   │
│  ┌──────┴──────┐                                           │
│  │  Methods    │                                           │
│  │             │                                           │
│  │ register_pid()     ← Called when inference starts       │
│  │ unregister_pid()   ← Called when inference ends         │
│  │ get_active_pids()  ← Returns running processes          │
│  │ kill_pid()         ← Terminates specific process        │
│  │ kill_all()         ← Terminates all processes           │
│  └─────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
```

### JSON File Structure

```json
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
```

### Process Lifecycle

```
1. Pipeline starts inference
   │
   ▼
2. Get Ollama runner PID (pgrep -f "ollama runner")
   │
   ▼
3. Register PID with manager
   │
   ▼
4. Inference runs (30-120+ seconds)
   │
   ├─────────────────────────────┐
   │                             │
   ▼                             ▼
5a. Success                   5b. Error/Timeout
   │                             │
   ▼                             ▼
6. Unregister PID             6. Unregister PID (finally block)
```

### Usage

```python
from app.services.pid_manager import get_pid_manager

pm = get_pid_manager()

# Register a process
pm.register_pid(
    pid=12345,
    process_type="ollama_runner",
    model="qwen3.5",
    prompt="What is arbitrage?"
)

# Check active processes
active = pm.get_active_pids()
for p in active:
    print(f"PID {p['pid']}: {p['model']} ({p['cpu_percent']:.1f}% CPU)")

# Kill a stuck process
result = pm.kill_pid(12345)
print(result['message'])  # "Process killed successfully"

# Kill all tracked processes
results = pm.kill_all()
```

### Kill Strategy

```
1. Try SIGTERM (graceful)
   │
   │ wait up to 5 seconds
   ▼
2. Process stopped? → Done
   │
   │ no
   ▼
3. Send SIGKILL (force)
   │
   ▼
4. Remove from tracking
```

### API Endpoints

The PID manager is exposed via these API endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/pids` | GET | List active processes |
| `/api/pids/{pid}/kill` | POST | Kill specific process |
| `/api/pids/kill-all` | POST | Kill all processes |

### Frontend Integration

The frontend includes a PID Manager widget:
- Floating button showing active process count
- Click to see details (CPU, memory, prompt)
- Kill button for each process
- Auto-refresh every 3 seconds

## Ollama Client (ollama_client.py)

Optional wrapper around the Ollama Python library.

Currently the pipeline uses `ollama.chat()` directly, but this
module could be extended to add:
- Connection pooling
- Retry logic
- Response caching
- Model preloading

### Potential Usage

```python
from app.services.ollama_client import OllamaClient

client = OllamaClient(model="qwen3.5", temperature=0.2)

# Check availability
if client.is_available():
    response = client.chat(messages=[...])
```
