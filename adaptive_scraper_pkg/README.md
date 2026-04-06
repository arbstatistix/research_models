# Adaptive Scraper

Production-oriented, single-page, polite scraper for public business research.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```

## Run

```bash
python -m adaptive_scraper.cli https://example.com --print
```
