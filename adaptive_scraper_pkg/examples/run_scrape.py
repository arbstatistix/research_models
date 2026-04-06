from pathlib import Path

from adaptive_scraper import AdaptiveScraper, ScraperConfig

config = ScraperConfig(output_dir=Path("outputs"))
scraper = AdaptiveScraper(config)
try:
    result = scraper.scrape("https://example.com")
    print(result.output_path)
finally:
    scraper.close()
