from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

from .http_client import HTTPClient


@dataclass(slots=True)
class RobotsPolicyResult:
    allowed: bool
    robots_url: str
    crawl_delay: float | None = None


class RobotsPolicyChecker:
    def __init__(self, http_client: HTTPClient, user_agent: str) -> None:
        self.http_client = http_client
        self.user_agent = user_agent

    def check(self, url: str) -> RobotsPolicyResult:
        parsed = urlparse(url)
        robots_url = urljoin(f"{parsed.scheme}://{parsed.netloc}", "/robots.txt")
        parser = RobotFileParser()
        parser.set_url(robots_url)

        try:
            response = self.http_client.get(robots_url, allow_redirects=True)
            lines = response.text.splitlines() if response.status_code < 400 else []
            parser.parse(lines)
        except Exception:
            parser.parse([])

        allowed = parser.can_fetch(self.user_agent, url)
        crawl_delay = parser.crawl_delay(self.user_agent)
        return RobotsPolicyResult(allowed=allowed, robots_url=robots_url, crawl_delay=crawl_delay)
