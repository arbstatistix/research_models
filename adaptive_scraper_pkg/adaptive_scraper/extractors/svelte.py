from __future__ import annotations

from typing import Any, Dict, List

from bs4 import BeautifulSoup

from ..config import ScraperConfig
from .base import ComponentExtractorBase


class SvelteExtractor(ComponentExtractorBase):
    component_type = "svelte_component"

    def __init__(self, config: ScraperConfig) -> None:
        super().__init__(config)

    def extract(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        components: List[Dict[str, Any]] = []
        seen = set()
        for element in soup.find_all(True):
            class_list = self._class_list(element)
            if not any(cls.startswith("s-") for cls in class_list):
                continue
            identity = id(element)
            if identity in seen:
                continue
            seen.add(identity)
            component = self._base_component(element)
            component["component_type"] = self.component_type
            component["scope_classes"] = [cls for cls in class_list if cls.startswith("s-")]
            component["text_strings"] = self._limit_items(component["descendant_text_strings"] + component["attribute_strings"])
            components.append(component)
        return components
