from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from .models import FrameworkDetectionResult


class JSONAssembler:
    def assemble(
        self,
        url: str,
        status_code: int,
        framework_result: FrameworkDetectionResult,
        rendering_strategy: str,
        robots_txt_allowed: bool,
        response_time_ms: int,
        page_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "url": url,
            "scraped_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "status_code": status_code,
            "framework_detected": framework_result.display_name,
            "rendering_strategy_used": rendering_strategy,
            "robots_txt_allowed": robots_txt_allowed,
            "response_time_ms": response_time_ms,
            "page": {
                "title": page_payload.get("title", ""),
                "meta_description": page_payload.get("meta_description", ""),
                "lang": page_payload.get("lang", ""),
                "canonical_url": page_payload.get("canonical_url", ""),
                "framework_meta": {
                    "framework": framework_result.framework,
                    "rendering_mode": framework_result.rendering_mode,
                    "confidence": framework_result.confidence,
                    "matched_signals": framework_result.matched_signals,
                    "sections": page_payload.get("framework_meta", {}).get("sections", {}),
                    "components": page_payload.get("framework_meta", {}).get("components", []),
                },
                "sections": page_payload.get("sections", {}),
            },
        }
