#!/usr/bin/env python3
"""Hash the public OpenWorld document without retaining its contents."""
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


URL = "https://preceptoros.org/openworld/"
request = urllib.request.Request(URL, headers={"User-Agent": "PreceptorOS-Lab-B1/1"})
with urllib.request.urlopen(request, timeout=20) as response:
    body = response.read()
    record = {
        "observed_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "requested_url": URL,
        "final_url": response.geturl(),
        "http_status": response.status,
        "response_date": response.headers.get("Date"),
        "content_type": response.headers.get("Content-Type"),
        "body_bytes": len(body),
        "body_sha256": hashlib.sha256(body).hexdigest(),
        "served_source_commit": "NO_DATA (the public page response does not expose a source revision)",
        "body_storage": "not retained; only the digest is recorded",
    }
target = Path(__file__).with_name("evidence") / "live-surface.json"
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps({key: record[key] for key in ("observed_at_utc", "http_status", "body_bytes", "body_sha256")}, sort_keys=True))
