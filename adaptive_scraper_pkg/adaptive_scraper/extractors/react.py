from __future__ import annotations

from typing import Any, Dict, List

from bs4 import BeautifulSoup, Tag

from ..config import ScraperConfig
from .base import ComponentExtractorBase


class ReactExtractor(ComponentExtractorBase):
    component_type = "react_component"

    def __init__(self, config: ScraperConfig) -> None:
        super().__init__(config)

    def extract(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        components: List[Dict[str, Any]] = []
        seen = set()
        for element in self._iter_react_candidates(soup):
            identity = id(element)
            if identity in seen:
                continue
            seen.add(identity)
            component = self._base_component(element)
            component["component_type"] = self.component_type
            component["data_testid"] = element.get("data-testid")
            component["custom_data_attributes"] = {
                key: value for key, value in element.attrs.items() if key.startswith("data-") and key not in {"data-testid", "data-reactroot"}
            }
            component["text_strings"] = self._limit_items([
                element.get_text(separator=" ", strip=True),
                *component["attribute_strings"],
                *component["descendant_text_strings"],
            ])
            component["aria_labels"] = self._limit_items([element.get("aria-label", "")])
            components.append(component)
        return components

    def _iter_react_candidates(self, soup: BeautifulSoup):
        for element in soup.find_all(attrs={"data-reactroot": True}):
            yield element
        for element in soup.find_all(attrs={"data-testid": True}):
            yield element
        for element in soup.find_all(True):
            if any(key.startswith("data-") for key in element.attrs.keys()):
                yield element
