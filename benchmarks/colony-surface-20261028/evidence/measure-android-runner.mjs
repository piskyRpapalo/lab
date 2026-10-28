#!/usr/bin/env node
// Repeatable visible-browser frame-cadence and memory sampler for B1.
// No application data, URL list, profile content, or device serial is emitted.
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { spawn, spawnSync } from 'node:child_process';
import { setTimeout as delay } from 'node:timers/promises';
import { createHash } from 'node:crypto';

const args = Object.fromEntries(process.argv.slice(2).map((item) => {
  const [key, ...rest] = item.replace(/^--/, '').split('=');
  return [key, rest.join('=') || true];
}));
const device = args.device || 'android';
const durationMs = Number(args['duration-ms'] || 60000);
const repetitions = Number(args.repeat || 2);
const outDir = path.resolve(args.output || 'benchmarks/colony-surface-20261028/evidence');
const webUrl = 'https://preceptoros.org/openworld/';
const appUrl = 'http://127.0.0.1:49188/walking_render.html';
const port = device === 'android' ? 9222 : 9333;
const cdn = `http://127.0.0.1:${port}`;
const adb = (...argv) => {
  const result = spawnSync('adb', argv, { encoding: 'utf8', timeout: 15000 });
  if (result.status !== 0) throw new Error(`adb operation failed (${result.status ?? 'timeout'})`);
  return result.stdout;
};
const getJson = async (url) => {
  const response = await fetch(url, { signal: AbortSignal.timeout(5000) });
  if (!response.ok) throw new Error(`CDP endpoint returned ${response.status}`);
  return response.json();
};

class Cdp {
  constructor(url) {
    this.socket = new WebSocket(url);
    this.nextId = 0;
    this.pending = new Map();
    this.ready = new Promise((resolve) => {
      this.socket.addEventListener('open', resolve, { once: true });
      this.socket.addEventListener('error', reject, { once: true });
    });
    this.socket.addEventListener('message', (event) => {
      const message = JSON.parse(event.data);
      if (!message.id) return;
      const entry = this.pending.get(message.id);
      if (!entry) return;
      this.pending.delete(message.id);
      if (message.error) entry.reject(new Error(message.error.message));
      else entry.resolve(message.result);
    });
  }
  async send(method, params = {}, sessionId) {
    await this.ready;
    const id = ++this.nextId;
    const message = { id, method, params };
    if (sessionId) message.sessionId = sessionId;
    const result = new Promise((resolve, reject) => this.pending.set(id, { resolve, reject }));
    this.socket.send(JSON.stringify(message));
    return result;
  }
  close() { this.socket.close(); }
}

async function waitForTarget(url) {
  for (let attempt = 0; attempt < 80; attempt += 1) {
    const targets = await getJson(`${cdn}/json/list`);
    const target = targets.find((entry) => entry.type === 'page' && entry.url === url);
    if (target) return target;
    await delay(250);
  }
  throw new Error('benchmark page target did not appear');
}

function runCommand(command, argv, options = {}) {
  const child = spawn(command, argv, { stdio: 'ignore', ...options });
  child.unref();
  return child;
}

async function startBrowser() {
  if (device === 'android') {
    adb('forward', `tcp:${port}`, 'localabstract:chrome_devtools_remote');
    adb('reverse', 'tcp:49188', 'tcp:49188');
    adb('shell', 'am', 'start', '-a', 'android.intent.action.VIEW', '-d', webUrl);
  } else if (device === 'rack') {
    const profile = path.join(os.tmpdir(), 'b1-colony-benchmark-chrome-profile');
    fs.mkdirSync(profile, { recursive: true, mode: 0o700 });
    runCommand('google-chrome', [
      '--no-first-run', '--no-default-browser-check', '--new-window',
      '--remote-debugging-port=9333', '--remote-allow-origins=*',
      '--enable-precise-memory-info', '--force-device-scale-factor=1',
      '--window-size=1920,1080', `--user-data-dir=${profile}`, webUrl,
    ], { detached: true });
  } else {
    throw new Error('device must be android or rack');
  }
  for (let attempt = 0; attempt < 120; attempt += 1) {
    try { await getJson(`${cdn}/json/version`); return; }
    catch { await delay(250); }
  }
  throw new Error('Chrome DevTools endpoint unavailable');
}

async function selectPage() {
  const targets = await getJson(`${cdn}/json/list`);
  let target = targets.find((entry) => entry.type === 'page' && entry.url === webUrl);
  if (!target && device === 'rack') target = targets.find((entry) => entry.type === 'page');
  if (!target) throw new Error('public benchmark tab unavailable');
  const cdp = new Cdp(target.webSocketDebuggerUrl);
  await cdp.send('Page.enable');
  await cdp.send('Runtime.enable');
  await cdp.send('Performance.enable');
  return cdp;
}

async function evaluate(cdp, expression, timeoutMs = 10000) {
  const response = await cdp.send('Runtime.evaluate', {
    expression, awaitPromise: true, returnByValue: true, userGesture: true,
  });
  if (response.exceptionDetails) throw new Error('page evaluation failed');
  return response.result?.value;
}

function quantile(values, percentile) {
  if (!values.length) return null;
  const sorted = [...values].sort((a, b) => a - b);
  return sorted[Math.max(0, Math.ceil(percentile * sorted.length) - 1)];
}

function chromeProcessRssKb() {
  if (device === 'android') {
    const output = adb('shell', 'dumpsys', 'meminfo', 'com.android.chrome');
    const matches = [...output.matchAll(/^\s*TOTAL PSS:\s*([\d,]+)/gm)];
    return matches.length ? Number(matches.at(-1)[1].replaceAll(',', '')) : null;
  }
  const result = spawnSync('ps', ['-eo', 'rss,args'], { encoding: 'utf8' });
  if (result.status !== 0) return null;
  let total = 0;
  let count = 0;
  for (const line of result.stdout.split('\n')) {
    const match = line.match(/^\s*(\d+)\s+.*--user-data-dir=([^\s]+b1-colony-benchmark-chrome-profile)/);
    if (match) { total += Number(match[1]); count += 1; }
  }
  return count ? total : null;
}

async function runSample(cdp, surface, reduced, runNumber) {
  const url = surface === 'openworld' ? webUrl : appUrl;
  await cdp.send('Emulation.setEmulatedMedia', {
    features: [{ name: 'prefers-reduced-motion', value: reduced ? 'reduce' : 'no-preference' }],
  });
  await cdp.send('Page.navigate', { url });
  for (let attempt = 0; attempt < 120; attempt += 1) {
    const ready = await evaluate(cdp, 'document.readyState').catch(() => null);
    if (ready === 'complete' || ready === 'interactive') break;
    await delay(250);
  }
  await delay(8000);
  const state = await evaluate(cdp, `({
    title: document.title,
    visibility: document.visibilityState,
    reducedMotion: matchMedia('(prefers-reduced-motion: reduce)').matches,
    viewport: [innerWidth, innerHeight, devicePixelRatio],
    responseStatus: performance.getEntriesByType('navigation')[0]?.responseStatus ?? null,
    motionTargets: document.querySelectorAll('.unit').length,
    transitionDuration: getComputedStyle(document.querySelector('.unit') || document.body).transitionDuration,
    jsHeapStart: performance.memory?.usedJSHeapSize ?? null
  })`);
  if (state.reducedMotion !== reduced) throw new Error('reduced-motion emulation did not match the requested setting');
  if (state.visibility !== 'visible') throw new Error('benchmark tab is not visible');
  if (surface === 'app' && state.motionTargets < 1) throw new Error('app walker fixture did not load its inhabitants');
  const screenshot = await cdp.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false });
  const screenshotPath = path.join(outDir, `${device}-${surface}-reduce-${reduced ? 'on' : 'off'}.png`);
  if (runNumber === 1) fs.writeFileSync(screenshotPath, Buffer.from(screenshot.data, 'base64'), { mode: 0o600 });

  const memoryStart = chromeProcessRssKb();
  const sampleExpression = `new Promise((resolve, reject) => {
    const elapsed = [];
    const heap = [];
    let previous = null;
    let clicks = 0;
    let transitions = 0;
    const started = performance.now();
    const onTransition = () => { transitions += 1; };
    document.addEventListener('transitionrun', onTransition, true);
    const driver = ${surface === 'app' ? "setInterval(() => { document.querySelector('#step')?.click(); clicks += 1; }, 250)" : 'null'};
    function frame(now) {
      if (previous !== null) elapsed.push(now - previous);
      previous = now;
      if (elapsed.length % 300 === 0 && performance.memory) heap.push(performance.memory.usedJSHeapSize);
      if (now - started >= ${durationMs}) {
        if (driver !== null) clearInterval(driver);
        document.removeEventListener('transitionrun', onTransition, true);
        resolve({elapsed, heap, clicks, transitions, elapsedMs: now - started,
          jsHeapEnd: performance.memory?.usedJSHeapSize ?? null,
          activeAnimations: document.getAnimations().length,
          reducedMotion: matchMedia('(prefers-reduced-motion: reduce)').matches});
      } else requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  })`;
  const memorySamples = [];
  const task = evaluate(cdp, sampleExpression, durationMs + 15000);
  const memoryInterval = setInterval(() => memorySamples.push(chromeProcessRssKb()), 10000);
  let sample;
  try { sample = await task; } finally { clearInterval(memoryInterval); }
  const memoryEnd = chromeProcessRssKb();
  if (!sample || sample.reducedMotion !== reduced) throw new Error('frame sample failed its media preference check');
  const fps = sample.elapsed.map((delta) => 1000 / delta);
  return {
    surface, reduced_motion: reduced ? 'on' : 'off', run: runNumber,
    duration_ms: Math.round(sample.elapsedMs), sample_count: fps.length,
    fps_median: quantile(fps, 0.50), fps_p05: quantile(fps, 0.05),
    frame_interval_ms_median: quantile(sample.elapsed, 0.50),
    frame_interval_ms_p95: quantile(sample.elapsed, 0.95),
    clicks: sample.clicks, transition_runs: sample.transitions,
    active_animations_at_end: sample.activeAnimations,
    reduced_motion_confirmed: sample.reducedMotion,
    js_heap_start_bytes: state.jsHeapStart, js_heap_end_bytes: sample.jsHeapEnd,
    process_memory_scope: device === 'android' ? 'Chrome package aggregate PSS; tabs/processes are not attributable separately' : 'benchmark Chrome profile aggregate RSS',
    process_memory_kb_start: memoryStart, process_memory_kb_samples: memorySamples,
    process_memory_kb_end: memoryEnd, screenshot: path.basename(screenshotPath),
    response_status: state.responseStatus, viewport_css_px: state.viewport,
    _frame_interval_ms: sample.elapsed,
    _js_heap_bytes_samples: sample.heap,
  };
}

await fs.promises.mkdir(outDir, { recursive: true, mode: 0o700 });
await startBrowser();
const cdp = await selectPage();
const results = [];
try {
  for (const surface of ['openworld', 'app']) {
    for (const reduced of [false, true]) {
      for (let run = 1; run <= repetitions; run += 1) {
        const result = await runSample(cdp, surface, reduced, run);
        results.push(result);
        const fps = result._frame_interval_ms.map((delta) => 1000 / delta);
        console.log(JSON.stringify({device, surface, reduced_motion: result.reduced_motion,
          run, fps_median: quantile(fps, 0.5), fps_p05: quantile(fps, 0.05),
          frames: fps.length, memory_kb_end: result.process_memory_kb_end}));
      }
    }
  }
} finally {
  cdp.close();
  if (device === 'rack') {
    const profile = path.join(os.tmpdir(), 'b1-colony-benchmark-chrome-profile');
    const result = spawnSync('pkill', ['-f', `--user-data-dir=${profile}`], { encoding: 'utf8' });
    void result;
  }
}

const outputPath = path.join(outDir, `${device}-samples.json`);
const payload = {
  schema: 'preceptoros.lab.colony-surface-benchmark/1',
  generated_at: new Date().toISOString(), device,
  method: {
    browser_frame_cadence: 'requestAnimationFrame callback intervals; reciprocal per interval; nearest-rank median and p05; two 60-second runs per surface and reduced-motion setting',
    warmup_ms: 8000,
    motion_input: 'app fixture receives a deterministic Next cycle click every 250 ms; live OpenWorld is passive',
    caveat: 'browser callback cadence is not a compositor or physical display-present measurement',
    sample_order: 'openworld then app; reduced motion off then on; repetitions in order',
  },
  results: results.map(({ _frame_interval_ms, _js_heap_bytes_samples, ...publicResult }) => ({
    ...publicResult,
    frame_interval_ms: _frame_interval_ms,
    js_heap_bytes_samples: _js_heap_bytes_samples,
  })),
};
fs.writeFileSync(outputPath, `${JSON.stringify(payload)}\n`, { mode: 0o600 });
console.log(JSON.stringify({receipt: outputPath, sha256: createHash('sha256').update(fs.readFileSync(outputPath)).digest('hex'), runs: results.length}));
