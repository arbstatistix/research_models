from __future__ import annotations

import asyncio
import random
import time
from typing import Sequence

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

from .config import ScraperConfig
from .http_client import RateLimiter
from .models import RenderedPage


class PlaywrightRenderer:
    def __init__(self, config: ScraperConfig, rate_limiter: RateLimiter) -> None:
        self.config = config
        self.rate_limiter = rate_limiter

    def render(self, url: str) -> RenderedPage:
        return asyncio.run(self._render(url))

    async def _render(self, url: str) -> RenderedPage:
        self.rate_limiter.wait()
        started = time.perf_counter()
        width = random.randint(self.config.viewport_width_min, self.config.viewport_width_max)
        height = random.randint(self.config.viewport_height_min, self.config.viewport_height_max)
        meaningful_selectors: Sequence[str] = ("main", "body", "#__next", "#app", "header", "article")

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=self.config.headless, slow_mo=self.config.browser_slow_mo_ms)
            context = await browser.new_context(
                user_agent=self.config.user_agent,
                viewport={"width": width, "height": height},
                locale="en-US",
            )
            page = await context.new_page()
            try:
                response = await page.goto(url, wait_until="networkidle", timeout=self.config.browser_wait_timeout_ms)
                await self._wait_meaningful(page, meaningful_selectors)
                await self._random_mouse(page, width, height)
                content = await page.content()
                elapsed_ms = int((time.perf_counter() - started) * 1000)
                return RenderedPage(
                    url=url,
                    status_code=response.status if response else 200,
                    html=content,
                    elapsed_ms=elapsed_ms,
                    final_url=page.url,
                )
            finally:
                await page.close()
                await context.close()
                await browser.close()

    async def _wait_meaningful(self, page, selectors: Sequence[str]) -> None:
        for selector in selectors:
            try:
                await page.wait_for_selector(selector, timeout=4000, state="attached")
                return
            except PlaywrightTimeoutError:
                continue

    async def _random_mouse(self, page, width: int, height: int) -> None:
        steps = random.randint(2, 4)
        for _ in range(steps):
            x = random.randint(50, max(60, width - 50))
            y = random.randint(50, max(60, height - 50))
            await page.mouse.move(x, y, steps=random.randint(8, 20))
            await asyncio.sleep(random.uniform(0.2, 0.7))
