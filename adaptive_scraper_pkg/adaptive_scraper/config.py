from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass(slots=True)
class ScraperConfig:
    user_agent: str = "ResearchBot/1.0 (+https://yoursite.com/about)"
    min_request_interval_seconds: float = 5.0
    random_delay_min_seconds: float = 3.0
    random_delay_max_seconds: float = 8.0
    timeout_seconds: float = 30.0
    max_retries: int = 4
    backoff_base_seconds: float = 5.0
    max_backoff_seconds: float = 60.0
    max_text_item_length: int = 500
    max_text_items_per_component: int = 200
    headless: bool = True
    browser_slow_mo_ms: int = 0
    viewport_width_min: int = 1200
    viewport_width_max: int = 1600
    viewport_height_min: int = 700
    viewport_height_max: int = 1000
    output_dir: Path = field(default_factory=lambda: Path("outputs"))
    allow_browser: bool = True
    browser_wait_timeout_ms: int = 20000
    retain_browser_artifacts: bool = False
    verify_ssl: bool = True
    proxies: Optional[dict] = None
