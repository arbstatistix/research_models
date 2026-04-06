from __future__ import annotations

from urllib.parse import urlparse

from .assembler import JSONAssembler
from .config import ScraperConfig
from .detector import FrameworkDetector
from .http_client import HTTPClient, RateLimiter
from .models import ScrapeResult
from .policy import RobotsPolicyChecker
from .renderer import PlaywrightRenderer
from .strategy import RenderingStrategySelector
from .writer import JSONWriter
from .extractors.static import StaticExtractor


class AdaptiveScraper:
    def __init__(self, config: ScraperConfig | None = None) -> None:
        self.config = config or ScraperConfig()
        self.rate_limiter = RateLimiter(
            min_interval_seconds=self.config.min_request_interval_seconds,
            random_delay_min_seconds=self.config.random_delay_min_seconds,
            random_delay_max_seconds=self.config.random_delay_max_seconds,
        )
        self.http_client = HTTPClient(self.config, self.rate_limiter)
        self.robots = RobotsPolicyChecker(self.http_client, self.config.user_agent)
        self.detector = FrameworkDetector()
        self.selector = RenderingStrategySelector()
        self.extractor = StaticExtractor(self.config)
        self.renderer = PlaywrightRenderer(self.config, self.rate_limiter)
        self.assembler = JSONAssembler()
        self.writer = JSONWriter(self.config.output_dir)

    def close(self) -> None:
        self.http_client.close()

    def scrape(self, url: str, write_json: bool = True) -> ScrapeResult:
        self._validate_public_url(url)
        robots_result = self.robots.check(url)
        if not robots_result.allowed:
            result = self.assembler.assemble(
                url=url,
                status_code=0,
                framework_result=self.detector.detect("", {}),
                rendering_strategy="blocked_by_robots",
                robots_txt_allowed=False,
                response_time_ms=0,
                page_payload={"title": "", "meta_description": "", "lang": "", "canonical_url": "", "sections": {}},
            )
            output_path = str(self.writer.write(url, result)) if write_json else None
            return ScrapeResult(data=result, output_path=output_path)

        initial = self.http_client.get(url)
        detection = self.detector.detect(initial.text, initial.headers)
        strategy = self.selector.select(detection)

        if strategy == "requests+BeautifulSoup":
            html = initial.text
            status_code = initial.status_code
            response_time_ms = initial.elapsed_ms
            final_url = initial.url
        else:
            if not self.config.allow_browser:
                raise RuntimeError("Playwright rendering required but browser use is disabled in config.")
            rendered = self.renderer.render(url)
            html = rendered.html
            status_code = rendered.status_code
            response_time_ms = rendered.elapsed_ms
            final_url = rendered.final_url or url

        soup = self.extractor.parse(html)
        page_payload = self.extractor.extract_page(soup, detection.display_name)
        result = self.assembler.assemble(
            url=final_url,
            status_code=status_code,
            framework_result=detection,
            rendering_strategy=strategy,
            robots_txt_allowed=True,
            response_time_ms=response_time_ms,
            page_payload=page_payload,
        )
        output_path = str(self.writer.write(final_url, result)) if write_json else None
        return ScrapeResult(data=result, output_path=output_path)

    @staticmethod
    def _validate_public_url(url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("Only public http/https URLs are allowed.")
        if not parsed.netloc:
            raise ValueError("A valid public URL is required.")
        host = parsed.hostname or ""
        blocked_hosts = {"localhost", "127.0.0.1", "0.0.0.0"}
        if host in blocked_hosts or host.endswith(".local"):
            raise ValueError("Private or local targets are not allowed.")
