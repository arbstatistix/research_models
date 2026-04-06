from __future__ import annotations

from typing import Any, Dict, List

from bs4 import BeautifulSoup

from ..config import ScraperConfig
from .base import ComponentExtractorBase


class AngularExtractor(ComponentExtractorBase):
    component_type = "angular_component"

    def __init__(self, config: ScraperConfig) -> None:
        super().__init__(config)

    def extract(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        components: List[Dict[str, Any]] = []
        seen = set()
        for element in soup.find_all(True):
            keys = list(element.attrs.keys())
            if not any(key.startswith("_nghost-") or key.startswith("_ngcontent-") or key.startswith("ng-reflect-") for key in keys):
                continue
            identity = id(element)
            if identity in seen:
                continue
            seen.add(identity)
            component = self._base_component(element)
            component["component_type"] = self.component_type
            component["ng_scope_attributes"] = [key for key in keys if key.startswith("_nghost-") or key.startswith("_ngcontent-")]
            component["ng_reflect_props"] = {key: value for key, value in element.attrs.items() if key.startswith("ng-reflect-")}
            component["text_strings"] = self._limit_items(component["descendant_text_strings"] + component["attribute_strings"] + list(component["ng_reflect_props"].values()))
            components.append(component)
        return components
