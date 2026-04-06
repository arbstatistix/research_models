from __future__ import annotations

from .models import FrameworkDetectionResult


class RenderingStrategySelector:
    def select(self, detection: FrameworkDetectionResult) -> str:
        if detection.framework == "Plain HTML":
            return "requests+BeautifulSoup"
        if detection.rendering_mode == "SSR":
            return "requests+BeautifulSoup"
        return "playwright"
