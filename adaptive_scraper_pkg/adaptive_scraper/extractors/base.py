from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List

from bs4 import BeautifulSoup, NavigableString, Tag

from ..config import ScraperConfig


class ComponentExtractorBase(ABC):
    component_type = "component"

    def __init__(self, config: ScraperConfig) -> None:
        self.config = config

    @abstractmethod
    def extract(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def _base_component(self, element: Tag) -> Dict[str, Any]:
        return {
            "tag": element.name,
            "id": element.get("id"),
            "class_list": self._class_list(element),
            "aria_label": element.get("aria-label"),
            "direct_text_strings": self._limit_items(self._direct_text_strings(element)),
            "descendant_text_strings": self._limit_items(self._descendant_text_strings(element)),
            "attribute_strings": self._limit_items(self._attribute_strings(element)),
            "children_count": len([child for child in element.children if isinstance(child, Tag)]),
            "element": self._element_min(element),
        }

    def _element_min(self, element: Tag) -> Dict[str, Any]:
        return {
            "tag": element.name,
            "id": element.get("id"),
            "class_list": self._class_list(element),
            "aria_label": element.get("aria-label"),
        }

    def _class_list(self, element: Tag) -> List[str]:
        classes = element.get("class")
        return [c for c in classes if c] if isinstance(classes, list) else []

    def _normalize_text(self, text: str) -> str:
        text = " ".join(text.split())
        if not text:
            return ""
        return text[: self.config.max_text_item_length]

    def _dedupe_preserve_order(self, values: Iterable[str]) -> List[str]:
        seen = set()
        result: List[str] = []
        for value in values:
            normalized = self._normalize_text(value)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            result.append(normalized)
        return result

    def _limit_items(self, values: Iterable[str]) -> List[str]:
        deduped = self._dedupe_preserve_order(values)
        return deduped[: self.config.max_text_items_per_component]

    def _direct_text_strings(self, element: Tag) -> List[str]:
        return [str(child).strip() for child in element.children if isinstance(child, NavigableString) and str(child).strip()]

    def _descendant_text_strings(self, element: Tag) -> List[str]:
        texts: List[str] = []
        for node in element.descendants:
            if isinstance(node, NavigableString):
                value = str(node).strip()
                if value:
                    texts.append(value)
        return texts

    def _attribute_strings(self, element: Tag) -> List[str]:
        values: List[str] = []
        for attr_name, attr_value in element.attrs.items():
            if attr_name == "alt" and isinstance(attr_value, str):
                values.append(attr_value)
            elif attr_name == "title" and isinstance(attr_value, str):
                values.append(attr_value)
            elif attr_name == "placeholder" and isinstance(attr_value, str):
                values.append(attr_value)
            elif attr_name == "data-label" and isinstance(attr_value, str):
                values.append(attr_value)
            elif attr_name.startswith("aria-"):
                if isinstance(attr_value, str):
                    values.append(attr_value)
                elif isinstance(attr_value, list):
                    values.extend(v for v in attr_value if isinstance(v, str))
        return values
