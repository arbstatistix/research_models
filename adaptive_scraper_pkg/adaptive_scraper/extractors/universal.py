from __future__ import annotations

from typing import Any, Dict, List

from bs4 import BeautifulSoup, Tag

from ..config import ScraperConfig
from .base import ComponentExtractorBase


class UniversalExtractor(ComponentExtractorBase):
    component_type = "universal_component"
    SECTION_TAGS = ("header", "main", "section", "article", "footer", "nav", "aside")

    def __init__(self, config: ScraperConfig) -> None:
        super().__init__(config)

    def extract(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        components: List[Dict[str, Any]] = []
        seen = set()
        for tag_name in self.SECTION_TAGS:
            for element in soup.find_all(tag_name):
                identity = id(element)
                if identity in seen:
                    continue
                seen.add(identity)
                payload = self._base_component(element)
                payload["component_type"] = self.component_type
                payload["text_strings"] = self._limit_items(payload["descendant_text_strings"] + payload["attribute_strings"])
                components.append(payload)
        return components

    def extract_semantic_sections(self, soup: BeautifulSoup) -> Dict[str, Dict[str, Any]]:
        section_names = ["header", "main", "section", "article", "footer", "nav", "aside"]
        results: Dict[str, Dict[str, Any]] = {name: {"components": []} for name in section_names}

        for name in section_names:
            for element in soup.find_all(name):
                component = self._component_from_section_element(element)
                results[name]["components"].append(component)

        return results

    def _component_from_section_element(self, element: Tag) -> Dict[str, Any]:
        payload = self._base_component(element)
        payload["component_type"] = self.component_type
        payload["text_strings"] = self._limit_items(payload["descendant_text_strings"] + payload["attribute_strings"])
        return payload
