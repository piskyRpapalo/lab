# Receipt · ideas18oct validation and live routes · 2026-10-19

Machine/runtime for local Python checks: Linux 7.0.0-38-generic x86_64;
Python 3.14.4. No hostname, model label, credential or prompt is retained.

## Yardsticks

- LAB contracts branch, command `python3 -m unittest discover -s tests -p 'test_*.py'`:
  11 tests, 0 failures in each of two consecutive runs.
- Selector branch after main sync, same command: 25 tests, 0 failures in each
  of two consecutive runs.
- `python3 bin/verify_llms_tree.py`: `LIVE · 5 indexed paths resolve inside
  the physical tree`.
- `./bin/pruebas` belongs to APP, not this LAB count; its separate receipt is
  in the APP validation document.
- Remote CI: `NO_DATA`, cause: not configured in this repository.

## Rack observation

Observation time: `2026-10-19T12:02:38Z`.

- Exact command: `python3 -c 'from pathlib import Path; root=Path("/sys/class/hwmon"); paths=list(root.glob("hwmon*/temp*_input")); readable=sum(1 for p in paths if p.read_text().strip().lstrip("-+").isdigit()); print("channels="+str(len(paths))+" readable="+str(readable))'`
- Result: 10 thermal channels found, 10 readable.
- Exact command:

  ```sh
  python3 - <<'PY'
  from pathlib import Path
  p = Path("/sys/class/powercap/intel-rapl:0/energy_uj")
  print("path_exists=" + str(p.exists()))
  try:
      print("counter_readable=" + str(p.read_text().strip().isdigit()))
  except PermissionError:
      print("NO_DATA cause=PermissionError")
  PY
  ```
- Result: counter path exists; read is `NO_DATA`, cause: `PermissionError`.
- Endpoint command: `python3 -c 'import datetime as dt,json,urllib.request; print("observed_at="+dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00","Z")); p="/api/tags"; r=urllib.request.urlopen("http://127.0.0.1:11434"+p,timeout=3); print(p+" HTTP "+str(r.status)+" models="+str(len(json.load(r).get("models",[])))); r=urllib.request.urlopen("http://127.0.0.1:11434/api/version",timeout=3); print("/api/version HTTP "+str(r.status)); r=urllib.request.urlopen("http://127.0.0.1:8740/",timeout=3); print("PWA / HTTP "+str(r.status))'`
- Result: `/api/tags` HTTP 200, 45 entries; `/api/version` HTTP 200; PWA `/` HTTP 200.
- Exact metrics probe: `curl --noproxy '*' --max-time 3 -sS -o /dev/null -w '/metrics HTTP %{http_code}\n' http://127.0.0.1:11434/metrics`
- Result: `/metrics` HTTP 404; token counters are unavailable. Net joules/token is
  `NO_DATA`, cause: RAPL read permission denied and no token counter is exposed.

## Cloudflare observation

Exact command:

```sh
python3 - <<'PY'
import datetime as dt
import urllib.request
import urllib.error

print("observed_at=" + dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"))
for path in ("/", "/cerebros.json", "/public/cerebros.json"):
    request = urllib.request.Request("https://preceptoros.org" + path, method="HEAD")
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            code = response.status
            headers = response.headers
    except urllib.error.HTTPError as exc:
        code = exc.code
        headers = exc.headers
    edge = headers.get("server", "").lower() == "cloudflare" or "cf-ray" in headers
    print(path + " HTTP " + str(code) + " edge=" + str(edge))
PY
```

Result: all three requests reached the Cloudflare edge and returned HTTP 403.
The source-tree file `public/cerebros.json` exists, but its live origin route
and bytes are `NO_DATA`, cause: edge denial. Asset-size compliance is declared
by the strict `< 25 MiB` guard in `test_web.py`; no live asset size was measured.
