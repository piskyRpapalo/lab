const CLASSES = ['greeting', 'screen_help', 'controls', 'privacy'];
const RESPONSES = Object.freeze({
  greeting: 'Hello. This chat only selects prewritten help.',
  screen_help: 'This screen help is a fixed, local demonstration.',
  controls: 'Use visible controls; this demonstration performs no action.',
  privacy: 'Input stays in this page and is not transmitted.',
});
const ATTACK = /(?:ignore\s+(?:all\s+)?previous\s+instructions|reveal\s+(?:the\s+)?system\s+prompt|override\s+(?:the\s+)?policy)/iu;
const encoder = new TextEncoder();

function noData(cause) {
  return { status: 'NO_DATA', cause };
}

async function digest(bytes) {
  const hash = await crypto.subtle.digest('SHA-256', bytes);
  return [...new Uint8Array(hash)].map((byte) => byte.toString(16).padStart(2, '0')).join('');
}

function feature(term) {
  let value = 2166136261;
  for (const byte of encoder.encode(term)) value = Math.imul(value ^ byte, 16777619) >>> 0;
  return value % 6_250_000;
}

function validateManifest(manifest) {
  if (!manifest || manifest.schema !== 'preceptoros.synthetic-choice-model/1') return 'manifest_invalid';
  if (manifest.total_bytes !== 25_000_000 || manifest.chunks?.length !== 4) return 'manifest_shape_invalid';
  let offset = 0;
  for (const chunk of manifest.chunks) {
    if (chunk.byte_offset !== offset || chunk.byte_length !== 6_250_000 || !/^[a-f0-9]{64}$/u.test(chunk.sha256)) return 'chunk_boundary_invalid';
    offset += chunk.byte_length;
  }
  return offset === manifest.total_bytes ? null : 'chunk_total_invalid';
}

export class IndexedChunkCache {
  constructor(name = 'chunked-choice-proof-v1') { this.name = name; this.db = null; }
  async open() {
    if (this.db) return this.db;
    this.db = await new Promise((resolve, reject) => {
      const request = indexedDB.open(this.name, 1);
      request.onupgradeneeded = () => request.result.createObjectStore('chunks');
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
    return this.db;
  }
  async get(key) {
    const db = await this.open();
    return new Promise((resolve, reject) => {
      const request = db.transaction('chunks').objectStore('chunks').get(key);
      request.onsuccess = () => resolve(request.result || null);
      request.onerror = () => reject(request.error);
    });
  }
  async put(key, value) {
    const db = await this.open();
    return new Promise((resolve, reject) => {
      const request = db.transaction('chunks', 'readwrite').objectStore('chunks').put(value, key);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }
}

async function assemble(manifest, cache) {
  const invalid = validateManifest(manifest);
  if (invalid) return noData(invalid);
  const result = new Uint8Array(manifest.total_bytes);
  for (const chunk of manifest.chunks) {
    let bytes;
    try { bytes = await cache.get(chunk.sha256); } catch { return noData('cache_read_failed'); }
    if (!bytes) return noData('cache_chunk_missing');
    if (!(bytes instanceof Uint8Array)) bytes = new Uint8Array(bytes);
    if (bytes.byteLength !== chunk.byte_length) return noData('cache_chunk_size_mismatch');
    if (await digest(bytes) !== chunk.sha256) return noData('cache_chunk_hash_mismatch');
    result.set(bytes, chunk.byte_offset);
  }
  return { status: 'READY', weights: result };
}

export async function downloadAndVerify(manifest, cache, fetchImpl = fetch, baseUrl = './model/') {
  const invalid = validateManifest(manifest);
  if (invalid) return noData(invalid);
  for (const chunk of manifest.chunks) {
    let response;
    try { response = await fetchImpl(new URL(chunk.file, new URL(baseUrl, location.href))); }
    catch { return noData('chunk_fetch_failed'); }
    if (!response.ok) return noData('chunk_http_missing');
    let bytes;
    try { bytes = new Uint8Array(await response.arrayBuffer()); }
    catch { return noData('chunk_body_unreadable'); }
    if (bytes.byteLength !== chunk.byte_length) return noData('chunk_size_mismatch');
    if (await digest(bytes) !== chunk.sha256) return noData('chunk_hash_mismatch');
    try { await cache.put(chunk.sha256, bytes); }
    catch { return noData('cache_write_failed'); }
  }
  return assemble(manifest, cache);
}

export async function loadCached(manifest, cache) {
  return assemble(manifest, cache);
}

export function decide(visitorText, weights) {
  if (typeof visitorText !== 'string' || !visitorText.trim()) return noData('moderator_empty_input');
  const normalized = visitorText.normalize('NFKC').trim().toLowerCase();
  if (normalized.length > 256) return noData('moderator_input_too_long');
  if (ATTACK.test(normalized)) return noData('moderator_attack_abort');
  if (!(weights instanceof Uint8Array) || weights.byteLength !== 25_000_000) return noData('model_not_loaded');
  const terms = normalized.match(/[a-z]+/gu) || [];
  const scores = [0, 0, 0, 0];
  for (const term of new Set(terms)) {
    const at = feature(term) * CLASSES.length;
    for (let i = 0; i < CLASSES.length; i += 1) scores[i] += weights[at + i] > 127 ? weights[at + i] - 256 : weights[at + i];
  }
  const best = Math.max(...scores);
  if (best <= 0 || scores.filter((score) => score === best).length !== 1) return noData('classifier_unmatched_or_tied');
  const category = CLASSES[scores.indexOf(best)];
  return { status: 'SIMULATED', category, text: RESPONSES[category] };
}
