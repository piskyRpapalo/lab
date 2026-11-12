"""Bounded planner measurement using the existing APP proxy, never an authority."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import urllib.request

from .delegation import Failure, PROXY_CAUSES, sha
from .transports import run_worker, throughput

PUBLIC_PLAN = {'schema': 'public-delegation-choice-v1', 'actions': ['DELEGATE_LOCAL', 'NO_DATA'],
               'specialist': 'serion-sort', 'budget_tokens': 64, 'privacy': 'LOCAL_ONLY'}


def public_prompt():
    return ('Propose only: a human has authorized a local public integer-sorting test. '
            'Choose DELEGATE_LOCAL to measure the already-installed specialist, or NO_DATA '
            'if evidence is missing. You cannot grant permissions or train anything. '
            'Return only JSON with one key action. Public case: ' + json.dumps(PUBLIC_PLAN, sort_keys=True))


def _plan(connection, app_root, base, expected):
    try:
        root = Path(app_root)
        path = root / 'hexelion_proxy.py'
        proxy_sha = hashlib.sha256(path.read_bytes()).hexdigest()
        sys.path.insert(0, str(root))
        spec = importlib.util.spec_from_file_location('meta_existing_hexelion_proxy', path)
        proxy = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(proxy)
        actual = throughput.model_digest(throughput.request('/api/tags', base=base), proxy.MODEL)
        if actual != expected:
            raise Failure('MODEL_IDENTITY')
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), throughput.NoRedirect())
        refused = []
        def bounded_open(request, timeout=None):
            if request.full_url not in (base + '/api/tags', base + '/api/generate'):
                raise Failure('PERMISSION')
            if request.data is not None:
                body = throughput.strict_json(request.data)
                if body.get('model') != proxy.MODEL or body.get('prompt') != public_prompt():
                    raise Failure('PERMISSION')
                # Preserve the working planner's GPT-OSS think-low contract.
                body['options']['num_predict'] = 512
                # No keep_alive: preserve the proxy/server's current retention behavior.
                request = urllib.request.Request(request.full_url, data=json.dumps(body).encode(),
                    headers={'Content-Type': 'application/json'}, method='POST')
            with opener.open(request, timeout=min(timeout or 30, 30)) as response:
                raw = response.read(65537)
            if len(raw) > 65536:
                refused.append('PROTOCOL')
                raise Failure('PROTOCOL')
            value = throughput.strict_json(raw)
            try:
                if request.full_url.endswith('/api/tags'):
                    if throughput.model_digest(value, proxy.MODEL) != expected:
                        refused.append('MODEL_IDENTITY')
                        raise Failure('MODEL_IDENTITY')
                else:
                    throughput.reject_remote(value)
                    if value.get('done') is not True:
                        refused.append('PROTOCOL')
                        raise Failure('PROTOCOL')
            except ValueError:
                refused.append('PERMISSION')
                raise Failure('PERMISSION') from None
            return io.BytesIO(raw)
        answer = proxy.ask(public_prompt(), endpoint=base, opener=bounded_open,
            output_format={'type': 'object', 'properties': {'action': {'type': 'string',
                'enum': ['DELEGATE_LOCAL', 'NO_DATA']}}, 'required': ['action'], 'additionalProperties': False})
        if answer.get('estado') != 'MEASURED':
            code = answer.get('causa')
            raise Failure(refused[0] if refused else PROXY_CAUSES.get(code, 'EVIDENCE'), code)
        decision = throughput.strict_json(answer['texto'])
        if (type(decision) is not dict or set(decision) != {'action'}
                or decision['action'] not in ('DELEGATE_LOCAL', 'NO_DATA')):
            raise Failure('OUTPUT_SCHEMA')
        if throughput.model_digest(throughput.request('/api/tags', base=base), proxy.MODEL) != expected:
            raise Failure('MODEL_IDENTITY')
        tokens = answer.get('medida', {}).get('gen_tokens')
        if type(tokens) is not int or not 0 < tokens <= 512:
            raise Failure('BUDGET')
        connection.send({'decision': decision['action'], 'proxy_sha256': proxy_sha,
            'result': {'model_version': expected, 'output_sha256': sha(decision), 'tokens': tokens,
                       'grade': 'PASS', 'basis': 'public_deterministic_reference'}})
    except Failure as exc:
        connection.send({'failure': exc.category, 'cause': exc.cause})
    except OSError:
        connection.send({'failure': 'TRANSPORT'})
    except Exception:
        connection.send({'failure': 'PROTOCOL'})
    finally:
        connection.close()


class ExistingHexelion:
    def __init__(self, app_root, base):
        self.app_root, self.base = Path(app_root), throughput.local_url(base)
        if not (self.app_root / 'hexelion_proxy.py').is_file():
            raise Failure('TRANSPORT')
        self.decision, self.proxy_sha256 = None, None

    def __call__(self, task, cancelled):
        self.decision, self.proxy_sha256 = None, None
        if (task['input_sha256'] != hashlib.sha256(public_prompt().encode()).hexdigest()
                or task['max_tokens'] != 512 or task['transport'] != 'ollama_loopback'):
            raise Failure('PERMISSION')
        response = run_worker(_plan, (str(self.app_root), self.base, task['model_version']),
                              task['timeout_ms'], cancelled)
        self.decision, self.proxy_sha256 = response['decision'], response['proxy_sha256']
        return response['result']
