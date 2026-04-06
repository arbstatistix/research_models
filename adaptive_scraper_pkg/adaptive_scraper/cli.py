from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import ScraperConfig
from .scraper import AdaptiveScraper


def main() -> None:
    parser = argparse.ArgumentParser(description="Adaptive, polite, single-page web scraper")
    parser.add_argument("url", help="Public URL to scrape")
    parser.add_argument("--output-dir", default="outputs", help="Directory for JSON output")
    parser.add_argument("--no-browser", action="store_true", help="Disable Playwright even if CSR is detected")
    parser.add_argument("--print", dest="print_result", action="store_true", help="Print JSON to stdout")
    args = parser.parse_args()

    config = ScraperConfig(output_dir=Path(args.output_dir), allow_browser=not args.no_browser)
    scraper = AdaptiveScraper(config)
    try:
        result = scraper.scrape(args.url, write_json=True)
        if args.print_result:
            print(json.dumps(result.data, indent=2, ensure_ascii=False))
        if result.output_path:
            print(result.output_path)
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
