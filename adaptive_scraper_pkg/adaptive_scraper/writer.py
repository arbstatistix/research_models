from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


class JSONWriter:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write(self, url: str, data: dict) -> Path:
        parsed = urlparse(url)
        host = (parsed.netloc or "site").replace(":", "_")
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = self.output_dir / f"{host}_{ts}.json"
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return path
