from __future__ import annotations

from typing import Any, Dict

from bs4 import BeautifulSoup

from ..config import ScraperConfig
from .angular import AngularExtractor
from .react import ReactExtractor
from .svelte import SvelteExtractor
from .universal import UniversalExtractor
from .vue import VueExtractor


class StaticExtractor:
    def __init__(self, config: ScraperConfig) -> None:
        self.config = config
        self.universal = UniversalExtractor(config)
        self.react = ReactExtractor(config)
        self.vue = VueExtractor(config)
        self.angular = AngularExtractor(config)
        self.svelte = SvelteExtractor(config)

    def parse(self, html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "lxml")

    def extract_page(self, soup: BeautifulSoup, framework_name: str) -> Dict[str, Any]:
        title = soup.title.get_text(strip=True) if soup.title else ""
        meta_description = ""
        meta = soup.find("meta", attrs={"name": "description"})
        if meta:
            meta_description = meta.get("content", "")
        canonical = soup.find("link", attrs={"rel": lambda v: v and "canonical" in v})
        html_tag = soup.find("html")
        lang = html_tag.get("lang", "") if html_tag else ""

        sections = self.universal.extract_semantic_sections(soup)
        framework_components = self._extract_framework_components(soup, framework_name)
        self._merge_framework_components_into_sections(soup, sections, framework_components)

        return {
            "title": title,
            "meta_description": meta_description,
            "lang": lang,
            "canonical_url": canonical.get("href", "") if canonical else "",
            "framework_meta": {
                "sections": sections,
                "components": framework_components,
            },
            "sections": sections,
        }

    def _extract_framework_components(self, soup: BeautifulSoup, framework_name: str):
        if framework_name.startswith("Next.js") or framework_name.startswith("React"):
            return self.react.extract(soup)
        if framework_name.startswith("Vue") or framework_name.startswith("Nuxt.js"):
            return self.vue.extract(soup)
        if framework_name.startswith("Angular"):
            return self.angular.extract(soup)
        if framework_name.startswith("Svelte"):
            return self.svelte.extract(soup)
        return self.universal.extract(soup)

    def _merge_framework_components_into_sections(self, soup: BeautifulSoup, sections: Dict[str, Dict[str, Any]], framework_components):
        for component in framework_components:
            tag_name = component.get("tag")
            if tag_name in sections:
                sections[tag_name]["components"].append(component)
                continue
            parent_section = self._nearest_section_name(soup, component)
            if parent_section:
                sections[parent_section]["components"].append(component)

    def _nearest_section_name(self, soup: BeautifulSoup, component: Dict[str, Any]) -> str | None:
        component_id = component.get("id")
        component_tag = component.get("tag")
        element = None
        if component_id:
            element = soup.find(id=component_id)
        if element is None and component_tag:
            element = soup.find(component_tag)
        while element is not None:
            if getattr(element, "name", None) in sections_names():
                return element.name
            element = element.parent
        return "main" if "main" in sections_names() else None


def sections_names():
    return {"header", "main", "section", "article", "footer", "nav", "aside"}
