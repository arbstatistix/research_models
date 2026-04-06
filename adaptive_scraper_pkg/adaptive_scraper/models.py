from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(slots=True)
class HTTPResponseData:
    url: str
    status_code: int
    headers: Dict[str, str]
    text: str
    elapsed_ms: int


@dataclass(slots=True)
class FrameworkDetectionResult:
    framework: str
    rendering_mode: str
    confidence: float
    matched_signals: List[str] = field(default_factory=list)

    @property
    def display_name(self) -> str:
        if self.framework == "Plain HTML":
            return "Plain HTML / SSR"
        if self.framework in {"Next.js", "Nuxt.js"}:
            return f"{self.framework} {self.rendering_mode}"
        if self.framework == "SvelteKit":
            return f"SvelteKit {self.rendering_mode}"
        if self.framework in {"React", "Vue", "Angular", "Svelte"}:
            return f"{self.framework} {self.rendering_mode}"
        return f"{self.framework} ({self.rendering_mode})"


@dataclass(slots=True)
class RenderedPage:
    url: str
    status_code: int
    html: str
    elapsed_ms: int
    final_url: Optional[str] = None


@dataclass(slots=True)
class ScrapeResult:
    data: Dict[str, Any]
    output_path: Optional[str] = None
