from __future__ import annotations

import re
from typing import Dict, List

from .models import FrameworkDetectionResult


class FrameworkDetector:
    def __init__(self) -> None:
        self.patterns: Dict[str, List[str]] = {
            "React": [r"__NEXT_DATA__", r"data-reactroot", r"_reactFiber", r"window\.__REACT_DEVTOOLS"],
            "Vue": [r"data-v-[a-zA-Z0-9_-]+", r"__vue__", r"window\.__VUE__", r"vue-router"],
            "Angular": [r"ng-version", r"_nghost-", r"_ngcontent-", r"ng-reflect"],
            "Svelte": [r"__svelte_", r'class\s*=\s*["\'][^"\']*\bs-[^"\']*["\']'],
            "Nuxt.js": [r"window\.__NUXT__", r"nuxt-link"],
            "SvelteKit": [r"__sveltekit_"],
        }

    def detect(self, html: str, headers: Dict[str, str]) -> FrameworkDetectionResult:
        matched: Dict[str, List[str]] = {k: [] for k in self.patterns}
        header_blob = " ".join(f"{k}:{v}" for k, v in headers.items())
        haystack = f"{html[:500000]}\n{header_blob}"

        for framework, rules in self.patterns.items():
            for rule in rules:
                if re.search(rule, haystack, flags=re.IGNORECASE):
                    matched[framework].append(rule)

        if matched["SvelteKit"]:
            mode = "SSR" if "<body" in html.lower() and "__sveltekit_" in haystack else "CSR"
            return FrameworkDetectionResult("SvelteKit", mode, 0.96, matched["SvelteKit"])

        if matched["Nuxt.js"]:
            mode = "SSR" if "__NUXT__" in haystack and self._has_meaningful_ssr_text(html) else "CSR"
            return FrameworkDetectionResult("Nuxt.js", mode, 0.95, matched["Nuxt.js"])

        if matched["React"]:
            if "__NEXT_DATA__" in haystack:
                mode = "SSR" if self._has_meaningful_ssr_text(html) else "CSR"
                return FrameworkDetectionResult("Next.js", mode, 0.97, matched["React"])
            mode = "SSR" if self._has_meaningful_ssr_text(html) and "data-reactroot" in haystack else "CSR"
            return FrameworkDetectionResult("React", mode, 0.92, matched["React"])

        if matched["Vue"]:
            mode = "SSR" if self._has_meaningful_ssr_text(html) and "data-server-rendered" in haystack else "CSR"
            return FrameworkDetectionResult("Vue", mode, 0.91, matched["Vue"])

        if matched["Angular"]:
            mode = "SSR" if self._has_meaningful_ssr_text(html) and "ng-version" in haystack and "<app-root" not in html[:25000].lower() else "CSR"
            return FrameworkDetectionResult("Angular", mode, 0.91, matched["Angular"])

        if matched["Svelte"]:
            mode = "SSR" if self._has_meaningful_ssr_text(html) else "CSR"
            return FrameworkDetectionResult("Svelte", mode, 0.9, matched["Svelte"])

        return FrameworkDetectionResult("Plain HTML", "SSR", 0.75, [])

    @staticmethod
    def _has_meaningful_ssr_text(html: str) -> bool:
        body = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", body)
        text = re.sub(r"\s+", " ", text).strip()
        return len(text) > 120
