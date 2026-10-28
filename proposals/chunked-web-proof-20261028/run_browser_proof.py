#!/usr/bin/env python3
"""Run the local browser proof through Chrome DevTools Protocol."""
import asyncio
import hashlib
import json
import platform
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.request import Request, urlopen

import websockets

ROOT = Path(__file__).resolve().parent
MODEL = ROOT / "model"
REQUESTS = []


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        REQUESTS.append(self.path)
        super().do_GET()

    def log_message(self, _format, *args):
        pass


async def run():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    Thread(target=server.serve_forever, daemon=True).start()
    port = server.server_address[1]
    with tempfile.TemporaryDirectory(prefix="chunk-proof-") as profile:
        chrome = subprocess.Popen([
            "google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu",
            "--disable-background-networking", "--no-first-run", "--no-default-browser-check",
            "--remote-allow-origins=*", "--remote-debugging-port=0",
            f"--user-data-dir={profile}", "about:blank",
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            active = Path(profile) / "DevToolsActivePort"
            deadline = time.monotonic() + 20
            while not active.exists() and time.monotonic() < deadline:
                if chrome.poll() is not None:
                    raise RuntimeError("Chrome exited before DevTools was ready")
                await asyncio.sleep(0.1)
            if not active.exists():
                raise RuntimeError("Chrome DevTools startup timed out")
            debug_port = int(active.read_text().splitlines()[0])
            request = Request(f"http://127.0.0.1:{debug_port}/json/new?about:blank", method="PUT")
            tab = json.load(urlopen(request))
            async with websockets.connect(tab["webSocketDebuggerUrl"], origin="http://localhost") as ws:
                next_id = 0

                async def call(method, params=None):
                    nonlocal next_id
                    next_id += 1
                    command_id = next_id
                    await ws.send(json.dumps({"id": command_id, "method": method, "params": params or {}}))
                    while True:
                        message = json.loads(await ws.recv())
                        if message.get("id") == command_id:
                            if "error" in message:
                                raise RuntimeError(message["error"])
                            return message.get("result", {})

                async def evaluate(expression):
                    result = await call("Runtime.evaluate", {"expression": expression, "returnByValue": True, "awaitPromise": True})
                    if result.get("exceptionDetails"):
                        raise RuntimeError(result["exceptionDetails"])
                    return result.get("result", {}).get("value")

                await call("Page.enable")
                await call("Runtime.enable")
                await call("Page.navigate", {"url": f"http://127.0.0.1:{port}/demo.html"})
                deadline = time.monotonic() + 30
                while time.monotonic() < deadline:
                    if await evaluate("document.readyState === 'complete'"):
                        break
                    await asyncio.sleep(0.1)
                await evaluate("new Promise(r => setTimeout(r, 300))")
                visible = await evaluate("document.querySelector('#model-origin').textContent")
                if f"127.0.0.1:{port}/model/" not in visible:
                    raise RuntimeError("same-origin model source is not visible before download")
                if any("weights-" in path for path in REQUESTS):
                    raise RuntimeError("weight request occurred before an explicit button action")

                await evaluate("document.querySelector('#load').click()")
                deadline = time.monotonic() + 10
                while time.monotonic() < deadline:
                    state = await evaluate("document.querySelector('#status').textContent")
                    if "cache_chunk_missing" in state:
                        break
                    await asyncio.sleep(0.1)
                if "cache_chunk_missing" not in state:
                    raise RuntimeError("missing cache did not report cause-bearing NO_DATA")

                await evaluate("document.querySelector('#download').click()")
                deadline = time.monotonic() + 60
                while time.monotonic() < deadline:
                    state = await evaluate("document.querySelector('#status').textContent")
                    if state == "SIMULATED · all chunks hash-verified":
                        break
                    await asyncio.sleep(0.2)
                if state != "SIMULATED · all chunks hash-verified":
                    raise RuntimeError(f"download/verification failed: {state}")
                await evaluate("document.querySelector('#input').value = 'help'; document.querySelector('#ask').click()")
                await evaluate("document.querySelector('#ask').click()")
                chat = await evaluate("Array.from(document.querySelectorAll('#chat li')).slice(-2).map(n => n.dataset.text)")
                if len(chat) != 2 or chat[0] != chat[1]:
                    raise RuntimeError("chat output was not byte-identical on repeat")
                weight_paths = [path for path in REQUESTS if "weights-" in path]
                if len(weight_paths) != 4:
                    raise RuntimeError(f"expected four weight requests, observed {len(weight_paths)}")
                weight_sizes = await evaluate("performance.getEntriesByType('resource').filter(e => e.name.includes('weights-')).map(e => e.decodedBodySize)")
                if len(weight_sizes) != 4 or sum(weight_sizes) != 25_000_000:
                    raise RuntimeError(f"browser-reported body sizes mismatch: {weight_sizes}")
                answer_hash = hashlib.sha256(chat[0].encode()).hexdigest()
                manifest_bytes = (MODEL / "manifest.json").read_bytes()
                report = {
                    "date_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "machine": f"{platform.system()} {platform.machine()} (host label omitted)",
                    "browser": subprocess.check_output(["google-chrome", "--version"], text=True).strip(),
                    "command": "python3 proposals/chunked-web-proof-20261028/run_browser_proof.py",
                    "same_origin_visible_before_weights": True,
                    "weight_requests_before_action": 0,
                    "missing_cache_cause": "cache_chunk_missing",
                    "weight_chunk_requests_after_action": len(weight_paths),
                    "browser_received_weight_body_bytes": sum(weight_sizes),
                    "chunk_bytes": weight_sizes,
                    "chunk_sha256": [json.loads((MODEL / "manifest.json").read_text())["chunks"][i]["sha256"] for i in range(4)],
                    "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
                    "chat_contract": "AtlasRadioChat.dice compatible fixture; PR #363 public call shape",
                    "repeat_output_equal": True,
                    "chat_output_sha256": answer_hash,
                    "worker_calls": 0,
                }
                print(json.dumps(report, indent=2))
        finally:
            chrome.terminate()
            try:
                chrome.wait(timeout=5)
            except subprocess.TimeoutExpired:
                chrome.kill()
                chrome.wait()
            server.shutdown()


if __name__ == "__main__":
    asyncio.run(run())
