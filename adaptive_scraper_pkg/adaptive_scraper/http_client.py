from __future__ import annotations

import random
import time
from threading import Lock
from typing import Optional

import requests
from requests import Response, Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import ScraperConfig
from .models import HTTPResponseData


class RateLimiter:
    def __init__(self, min_interval_seconds: float, random_delay_min_seconds: float, random_delay_max_seconds: float) -> None:
        self.min_interval_seconds = min_interval_seconds
        self.random_delay_min_seconds = random_delay_min_seconds
        self.random_delay_max_seconds = random_delay_max_seconds
        self._last_request_monotonic = 0.0
        self._lock = Lock()

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_request_monotonic
            if elapsed < self.min_interval_seconds:
                time.sleep(self.min_interval_seconds - elapsed)
            time.sleep(random.uniform(self.random_delay_min_seconds, self.random_delay_max_seconds))
            self._last_request_monotonic = time.monotonic()


class HTTPClient:
    def __init__(self, config: ScraperConfig, rate_limiter: RateLimiter) -> None:
        self.config = config
        self.rate_limiter = rate_limiter
        self._session = self._build_session()

    def _build_session(self) -> Session:
        session = requests.Session()
        retry = Retry(
            total=0,
            connect=0,
            read=0,
            backoff_factor=0,
            allowed_methods=frozenset(["GET", "HEAD"]),
            status_forcelist=[],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=1, pool_maxsize=1)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update({"User-Agent": self.config.user_agent, "Accept-Language": "en-US,en;q=0.9"})
        if self.config.proxies:
            session.proxies.update(self.config.proxies)
        return session

    def close(self) -> None:
        self._session.close()

    def reset_session(self) -> None:
        try:
            self._session.close()
        finally:
            self._session = self._build_session()

    def _request_with_backoff(self, url: str, allow_redirects: bool = True) -> Response:
        last_error: Optional[Exception] = None
        for attempt in range(self.config.max_retries + 1):
            self.rate_limiter.wait()
            try:
                response = self._session.get(
                    url,
                    timeout=self.config.timeout_seconds,
                    allow_redirects=allow_redirects,
                    verify=self.config.verify_ssl,
                    stream=False,
                )
                if response.status_code in {429, 503}:
                    backoff = min(self.config.max_backoff_seconds, self.config.backoff_base_seconds * (2 ** attempt))
                    response.close()
                    time.sleep(backoff)
                    self.reset_session()
                    continue
                return response
            except (requests.ConnectionError, requests.Timeout, requests.ChunkedEncodingError) as exc:
                last_error = exc
                backoff = min(self.config.max_backoff_seconds, self.config.backoff_base_seconds * (2 ** attempt))
                time.sleep(backoff)
                self.reset_session()
        if last_error:
            raise last_error
        raise RuntimeError(f"Failed to fetch URL: {url}")

    def get(self, url: str, allow_redirects: bool = True) -> HTTPResponseData:
        started = time.perf_counter()
        response = self._request_with_backoff(url, allow_redirects=allow_redirects)
        try:
            text = response.text
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            return HTTPResponseData(
                url=response.url,
                status_code=response.status_code,
                headers={k.lower(): v for k, v in response.headers.items()},
                text=text,
                elapsed_ms=elapsed_ms,
            )
        finally:
            response.close()
