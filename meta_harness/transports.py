"""Explicit local transports; no discovery by port, fallback, pulls or service changes."""
import hashlib
import fcntl
import json
import multiprocessing
import os
from pathlib import Path
import select
import subprocess
import sys
import time

from .delegation import Failure, sha
from .reuse import instrument

throughput = instrument('throughput')
PROFILES = {'csv': ('public-sort', 64), 'json-array': ('public-sort-json', 64),
            'json-array-128': ('public-sort-json128', 128)}


class StdioMCP:
    """One operator-selected existing Python MCP server; bounded NDJSON protocol.

    Arbitrary server paths/arguments are not accepted from model/task JSON. The
    operator owns this local executable choice; its imports are not attested here.
    """
    def __init__(self, script, *, expected_version=None, timeout=5, cancelled=lambda: False):
        self.script = Path(script)
        if self.script.is_symlink() or not self.script.is_file() or self.script.suffix != '.py':
            raise Failure('TRANSPORT')
        # A sealed in-memory snapshot binds launched top-level bytes to this hash.
        # Imported modules/configuration remain host-owned and are not attested.
        self.code = self.script.read_bytes()
        if len(self.code) > 1048576:
            raise Failure('PROTOCOL')
        self.version = hashlib.sha256(self.code).hexdigest()
        if expected_version is not None and self.version != expected_version:
            raise Failure('MODEL_IDENTITY')
        self.timeout, self.cancelled, self.seq, self.buffer = timeout, cancelled, 0, b''
        self.process = None

    def __enter__(self):
        if self.cancelled():
            raise Failure('CANCELLED')
        snapshot = os.memfd_create('meta-mcp', os.MFD_CLOEXEC | os.MFD_ALLOW_SEALING)
        try:
            with os.fdopen(os.dup(snapshot), 'wb') as output:
                output.write(self.code)
            os.lseek(snapshot, 0, os.SEEK_SET)
            fcntl.fcntl(snapshot, fcntl.F_ADD_SEALS, fcntl.F_SEAL_WRITE | fcntl.F_SEAL_GROW |
                        fcntl.F_SEAL_SHRINK | fcntl.F_SEAL_SEAL)
            launcher = ('import os,sys,pathlib; fd=int(sys.argv[1]); path=sys.argv[2]; '
                'source=os.fdopen(fd,"rb").read(1048577); sys.argv=[path]; '
                'sys.path.insert(0,str(pathlib.Path(path).resolve().parent)); '
                'namespace=sys.modules["__main__"].__dict__; '
                'namespace.update(__file__=path,__package__=None,__spec__=None); '
                'exec(compile(source,path,"exec"),namespace)')
            if self.cancelled():
                raise Failure('CANCELLED')
            self.process = subprocess.Popen([sys.executable, '-B', '-c', launcher, str(snapshot), str(self.script)],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, pass_fds=(snapshot,),
                env={'PATH': os.defpath, 'LANG': 'C.UTF-8', 'PYTHONDONTWRITEBYTECODE': '1'})
        finally:
            os.close(snapshot)
        try:
            initialized = self.rpc('initialize', {'protocolVersion': '2025-11-25',
                'capabilities': {}, 'clientInfo': {'name': 'meta-harness', 'version': '1'}})
            if (not isinstance(initialized, dict) or initialized.get('protocolVersion') not in
                    ('2025-11-25', '2026-07-28') or not isinstance(initialized.get('serverInfo'), dict)
                    or not isinstance(initialized.get('capabilities', {}).get('tools'), dict)):
                raise Failure('PROTOCOL')
            self.notify('notifications/initialized')
            declared = self.rpc('tools/list')
            tools = declared.get('tools') if isinstance(declared, dict) else None
            if not isinstance(tools, list) or len(tools) > 64 or any(
                    not isinstance(t, dict) or not isinstance(t.get('name'), str) for t in tools):
                raise Failure('PROTOCOL')
            if len({t['name'] for t in tools}) != len(tools):
                raise Failure('PROTOCOL')
            self.tools = {t['name'] for t in tools}
            self.manifest_sha256 = sha(tools)
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def notify(self, method):
        self._write({'jsonrpc': '2.0', 'method': method})

    def _write(self, value):
        if self.cancelled():
            raise Failure('CANCELLED')
        try:
            self.process.stdin.write(json.dumps(value).encode() + b'\n')
            self.process.stdin.flush()
        except (OSError, ValueError):
            raise Failure('TRANSPORT') from None

    def rpc(self, method, params=None):
        self.seq += 1
        expected = self.seq
        self._write({'jsonrpc': '2.0', 'id': expected, 'method': method, 'params': params or {}})
        deadline = time.monotonic() + self.timeout
        while b'\n' not in self.buffer:
            if self.cancelled():
                raise Failure('CANCELLED')
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise Failure('TRANSPORT')
            ready, _, _ = select.select([self.process.stdout], [], [], min(.05, remaining))
            if not ready:
                continue
            block = os.read(self.process.stdout.fileno(), 4096)
            if not block:
                raise Failure('TRANSPORT')
            self.buffer += block
            if len(self.buffer) > 1048576:
                raise Failure('PROTOCOL')
        raw, self.buffer = self.buffer.split(b'\n', 1)
        try:
            message = throughput.strict_json(raw)
        except (ValueError, TypeError, UnicodeError):
            raise Failure('PROTOCOL') from None
        if (not isinstance(message, dict) or message.get('jsonrpc') != '2.0'
                or type(message.get('id')) is not int or message['id'] != expected
                or 'error' in message or 'result' not in message):
            raise Failure('PROTOCOL')
        return message['result']

    def call(self, tool):
        if tool not in self.tools:
            raise Failure('PERMISSION')
        result = self.rpc('tools/call', {'name': tool, 'arguments': {}})
        if not isinstance(result, dict) or result.get('isError', False) is not False:
            raise Failure('EVIDENCE')
        content = result.get('content')
        if (not isinstance(content, list) or len(content) != 1 or not isinstance(content[0], dict)
                or content[0].get('type') != 'text' or not isinstance(content[0].get('text'), str)):
            raise Failure('PROTOCOL')
        try:
            value = throughput.strict_json(content[0]['text'])
        except (ValueError, TypeError):
            raise Failure('PROTOCOL') from None
        if not isinstance(value, dict) or value.get('ok') is False or value.get('estado') == 'NO_DATA':
            raise Failure('EVIDENCE')
        return value

    def __exit__(self, *args):
        if self.process is not None:
            if self.process.stdin:
                self.process.stdin.close()
            try:
                self.process.wait(timeout=.3)
            except subprocess.TimeoutExpired:
                self.process.terminate()
                try:
                    self.process.wait(timeout=.3)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait()
            self.process.stdout.close()


class NativeHealth:
    """Fixed health tool only. Native server retains its own dispatcher/allowlist.

    Never exposes exec/audit/data tools to task/model JSON. Ping writes no audit.
    """
    def __init__(self, script):
        self.script = script
        self.version = hashlib.sha256(Path(script).read_bytes()).hexdigest()
        self.inventory = None

    def __call__(self, task, cancelled):
        if task['transport'] != 'mcp_stdio' or task['input_sha256'] != sha({'tool': 'ping'}):
            raise Failure('PERMISSION')
        with StdioMCP(self.script, expected_version=task['model_version'],
                      timeout=task['timeout_ms'] / 3000, cancelled=cancelled) as client:
            if client.version != task['model_version']:
                raise Failure('MODEL_IDENTITY')
            value = client.call('ping')
            if value.get('pong') is not True or value.get('ok') is not True:
                raise Failure('PROTOCOL')
            self.inventory = {'transport': 'stdio', 'state': 'VERIFIED',
                'basis': 'initialize_tools_list_ping_roundtrip', 'tools_declared': len(client.tools),
                'tools_verified': ['ping'], 'manifest_sha256': client.manifest_sha256,
                'model_execution': throughput.no_data('no_model_invoked')}
            return {'model_version': client.version, 'output_sha256': sha(value),
                    'tokens': 0, 'grade': 'NOT_EVALUATED', 'basis': 'protocol_roundtrip'}


def sort_prompt(raw, profile='csv'):
    if profile not in PROFILES:
        raise Failure('PERMISSION')
    prompt = throughput.public_input(raw)
    return prompt if profile == 'csv' else prompt + ' Return only a JSON array of these 16 integers.'


def grade_public(answer, raw, profile='csv'):
    import re
    normalized = answer.strip()
    if profile.startswith('json-array'):
        try:
            values = throughput.strict_json(normalized)
        except (TypeError, ValueError):
            return 'OUTPUT_SCHEMA'
        if type(values) is not list or len(values) != 16 or any(type(v) is not int for v in values):
            return 'OUTPUT_SCHEMA'
    else:
        if not re.fullmatch(r'\d{1,2}(?:\s*,\s*\d{1,2}){15}', normalized):
            return 'OUTPUT_SCHEMA'
        values = [int(v) for v in normalized.split(',')]
    expected = sorted(throughput.strict_json(raw)['values'])
    return 'PASS' if values == expected else 'TASK_SKILL'


def _generate(connection, base, model, expected, raw, profile):
    """Worker sends only hashes/counters to the parent, never prompt/answer text."""
    try:
        call = lambda path, body=None: throughput.request(path, body, base)
        if throughput.model_digest(call('/api/tags'), model) != expected:
            raise Failure('MODEL_IDENTITY')
        settings = throughput.SETTINGS
        started = time.monotonic_ns()
        body = {'model': model, 'prompt': sort_prompt(raw, profile),
            'stream': False, 'think': False, 'keep_alive': 0, 'options': {k: settings[k]
                for k in ('temperature', 'seed', 'num_ctx', 'num_predict')}}
        body['options']['num_predict'] = PROFILES[profile][1]
        if profile.startswith('json-array'):
            body['format'] = {'type': 'array', 'items': {'type': 'integer'}, 'minItems': 16, 'maxItems': 16}
        result = call('/api/generate', body)
        metrics = throughput.sample(result, model, time.monotonic_ns() - started)
        if throughput.model_digest(call('/api/tags'), model) != expected:
            raise Failure('MODEL_IDENTITY')
        connection.send({'model_version': expected, 'output_sha256': metrics['response_sha256'],
            'tokens': metrics['eval_count'], 'grade': grade_public(result['response'], raw, profile),
            'basis': 'public_deterministic_reference'})
    except Failure as exc:
        connection.send({'failure': exc.category})
    except OSError:
        connection.send({'failure': 'TRANSPORT'})
    except Exception:
        connection.send({'failure': 'PROTOCOL'})
    finally:
        connection.close()


class LocalModel:
    def __init__(self, base, model, profile='csv'):
        self.base = throughput.local_url(base)
        if model.endswith(':cloud'):
            raise Failure('PERMISSION')
        self.model = model
        self.raw = throughput.FIXTURE.read_bytes()
        self.profile = profile
        self.input_sha256 = hashlib.sha256(sort_prompt(self.raw, profile).encode()).hexdigest()
        self.case_sha256 = hashlib.sha256(self.raw).hexdigest()

    def __call__(self, task, cancelled):
        if (task['transport'] != 'ollama_loopback' or task['input_sha256'] != self.input_sha256
                or hashlib.sha256(sort_prompt(self.raw, self.profile).encode()).hexdigest() != self.input_sha256
                or task['max_tokens'] != PROFILES[self.profile][1]):
            raise Failure('PERMISSION')
        # Enforce a bounded client wait without reconfiguring/stopping the model service.
        return run_worker(_generate, (self.base, self.model, task['model_version'], self.raw, self.profile),
                          task['timeout_ms'], cancelled)


def run_worker(target, args, timeout_ms, cancelled):
        """Stop only our client child; the service's in-flight outcome may be unknown."""
        if cancelled():
            raise Failure('CANCELLED')
        context = multiprocessing.get_context('spawn')
        reader, writer = context.Pipe(duplex=False)
        process = context.Process(target=target, args=(writer, *args))
        if cancelled():
            reader.close()
            writer.close()
            raise Failure('CANCELLED')
        process.start()
        writer.close()
        deadline = time.monotonic() + timeout_ms / 1000
        try:
            while True:
                if cancelled():
                    raise Failure('CANCELLED')
                if time.monotonic() >= deadline:
                    raise Failure('TRANSPORT')
                if reader.poll(.02):
                    try:
                        result = reader.recv()
                    except EOFError:
                        raise Failure('TRANSPORT') from None
                    if isinstance(result, dict) and 'failure' in result:
                        raise Failure(result['failure'], result.get('cause'))
                    return result
                if not process.is_alive():
                    raise Failure('TRANSPORT')
        finally:
            reader.close()
            if process.is_alive():
                process.terminate()
            process.join(timeout=1)
            if process.is_alive():
                process.kill()
                process.join()
