"""Optional local-only Ollama explanation adapter; it cannot rank or authorize."""

from __future__ import annotations

import json
from pathlib import Path
import re
import urllib.error
import urllib.request


class LocalModelCaller:
    def __init__(self, host: str, port: int, model: str, *, seed: int = 0, timeout: float = 60):
        if host not in {"127.0.0.1", "::1"}:
            raise ValueError("model host must be numeric loopback")
        if not 1 <= port <= 65535 or not model:
            raise ValueError("local endpoint configuration is incomplete")
        self.base = f"http://[{host}]:{port}" if ":" in host else f"http://{host}:{port}"
        self.model = model
        self.seed = seed
        self.timeout = timeout

    def explain(self, equation: str, cause: str) -> str:
        show = self._request("/api/show", {"model": self.model}, method="POST")
        modelfile = show.get("modelfile") if isinstance(show, dict) else None
        match = re.search(r"(?m)^FROM\s+(.+?)\s*$", modelfile or "")
        blob = Path(match.group(1)) if match else None
        if not isinstance(show, dict) or "details" not in show or blob is None or not blob.is_absolute() or not blob.is_file() or blob.is_symlink():
            raise RuntimeError("model blob is not a readable local file; no inference attempted")
        prompt = ("Explain this deterministic selector equation and its cause. Do not select, "
                  "authorize, rewrite, or add facts. Equation: " + equation + " Cause: " + cause)
        response = self._request("/api/generate", {"model": self.model, "prompt": prompt, "stream": False,
                                 "options": {"temperature": 0, "seed": self.seed}})
        value = response.get("response") if isinstance(response, dict) else None
        if not isinstance(value, str) or not value.strip():
            raise RuntimeError("local model returned no explanation")
        return value

    def _request(self, path: str, body: dict, *, method: str = "POST") -> dict:
        request = urllib.request.Request(self.base + path, data=json.dumps(body).encode("utf-8"),
                                         headers={"Content-Type": "application/json"}, method=method)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"local model service returned HTTP {exc.code}") from None
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"local model call unavailable: {type(exc).__name__}") from None
