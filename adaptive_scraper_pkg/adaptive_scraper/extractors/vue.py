from __future__ import annotations

from typing import Any, Dict, List

from bs4 import BeautifulSoup

from ..config import ScraperConfig
from .base import ComponentExtractorBase


class VueExtractor(ComponentExtractorBase):
    component_type = "vue_component"

    def __init__(self, config: ScraperConfig) -> None:
        super().__init__(config)

    def extract(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        components: List[Dict[str, Any]] = []
        seen = set()
        for element in soup.find_all(True):
            scoped_attrs = [key for key in element.attrs.keys() if key.startswith("data-v-")]
            if not scoped_attrs:
                continue
            identity = id(element)
            if identity in seen:
                continue
            seen.add(identity)
            component = self._base_component(element)
            component["component_type"] = self.component_type
            component["scoped_attributes"] = scoped_attrs
            component["rendered_bound_attributes"] = {key: value for key, value in element.attrs.items() if key.startswith(":") or key.startswith("v-bind:")}
            component["text_strings"] = self._limit_items(component["descendant_text_strings"] + component["attribute_strings"])
            components.append(component)
        return components
