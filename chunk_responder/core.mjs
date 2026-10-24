export const REQUEST_SCHEMA = 'preceptoros.chunk-request/1';
export const RESPONSE_SCHEMA = 'preceptoros.chunk-response/1';
export const MAX_REQUEST_BYTES = 1024;
export const MAX_CHUNK_BYTES = 150;
export const POLICY_ID = 'demo-allowlist/1';
export const ALLOWED_VIEWS = new Set(['map', 'battle', 'profile', 'info']);

export const CANON = Object.freeze({
  'guide-v1': Object.freeze({
    greeting: Object.freeze({ id: 'guide.greeting/1', text: 'Hola. Este chat explica la vista activa.' }),
    screen_help: Object.freeze({ id: 'guide.screen-help/1', text: 'La vista activa se lee en el orden de títulos indicado.' }),
    controls: Object.freeze({ id: 'guide.controls/1', text: 'Usa los controles visibles; este chat no ejecuta acciones.' }),
    privacy: Object.freeze({ id: 'guide.privacy/1', text: 'El texto queda local; el Worker recibe solo una categoría pública.' }),
  }),
});

const ALLOWLIST = new Map([
  ['hello', 'greeting'], ['hi', 'greeting'], ['hola', 'greeting'],
  ['what is on this screen', 'screen_help'], ['what is this screen', 'screen_help'],
  ['que hay en esta pantalla', 'screen_help'], ['qué hay en esta pantalla', 'screen_help'],
  ['how do i use the controls', 'controls'], ['como uso los controles', 'controls'],
  ['cómo uso los controles', 'controls'], ['controls', 'controls'],
  ['privacy', 'privacy'], ['privacidad', 'privacy'],
]);

const ATTACK = /(?:ignore\s+(?:all\s+)?previous\s+instructions|reveal\s+(?:the\s+)?system\s+prompt|override\s+(?:the\s+)?policy|ignora\s+(?:todas\s+)?las\s+instrucciones|revela\s+(?:el\s+)?prompt\s+del\s+sistema)/iu;
const ID = /^[a-z0-9][a-z0-9._-]{0,63}$/u;

function noData(cause) {
  return { schema: RESPONSE_SCHEMA, status: 'NO_DATA', cause };
}

export function moderateLocally(visitorText) {
  if (typeof visitorText !== 'string' || !visitorText.trim()) {
    return { state: 'NO_DATA', cause: 'moderator_empty_input' };
  }
  const normalized = visitorText.normalize('NFKC').trim().replace(/\s+/gu, ' ').toLocaleLowerCase('en');
  if (ATTACK.test(normalized)) return { state: 'ABORT', cause: 'moderator_attack_or_injection' };
  const category = ALLOWLIST.get(normalized);
  if (!category) return { state: 'NO_DATA', cause: 'moderator_demo_unmatched' };
  return { state: 'ALLOW', policy: POLICY_ID, category };
}

export function makeRequest(visitorText, screen) {
  const gate = moderateLocally(visitorText);
  if (gate.state !== 'ALLOW') return noData(gate.cause);
  if (!validScreen(screen)) return noData('screen_context_invalid');
  const request = {
    schema: REQUEST_SCHEMA,
    gate: 'ALLOW',
    policy: gate.policy,
    screen: {
      id: screen.id,
      active_view: screen.active_view,
      reading_plan: screen.reading_plan,
      title_order: [...screen.title_order],
    },
    category: gate.category,
  };
  if (new TextEncoder().encode(JSON.stringify(request)).byteLength > MAX_REQUEST_BYTES) {
    return noData('request_over_1024_bytes');
  }
  return request;
}

function validScreen(screen) {
  if (!screen || typeof screen !== 'object' || Array.isArray(screen)) return false;
  if (!ID.test(screen.id || '') || !ALLOWED_VIEWS.has(screen.active_view)) return false;
  if (screen.reading_plan !== 'plan-del-guion') return false;
  if (!Array.isArray(screen.title_order) || screen.title_order.length < 1 || screen.title_order.length > 16) return false;
  return screen.title_order.every((id) => typeof id === 'string' && ID.test(id));
}

export function resolveSignal(request) {
  if (!request || typeof request !== 'object' || Array.isArray(request)) return noData('request_schema_invalid');
  if (request.schema !== REQUEST_SCHEMA || request.gate !== 'ALLOW' || request.policy !== POLICY_ID) {
    return noData('moderator_gate_missing_or_invalid');
  }
  const keys = Object.keys(request).sort().join(',');
  if (keys !== 'category,gate,policy,schema,screen') return noData('request_fields_not_allowed');
  if (!validScreen(request.screen)) return noData('screen_context_invalid');
  if (typeof request.category !== 'string' || !Object.hasOwn(CANON[request.screen.id] || {}, request.category)) {
    return noData('canon_chunk_absent');
  }
  const entry = CANON[request.screen.id][request.category];
  if (new TextEncoder().encode(entry.text).byteLength >= MAX_CHUNK_BYTES) return noData('canon_chunk_over_150_bytes');
  return {
    schema: RESPONSE_SCHEMA,
    status: 'CHUNK',
    screen: { id: request.screen.id, active_view: request.screen.active_view },
    reading_plan: request.screen.reading_plan,
    title_order: [...request.screen.title_order],
    category: request.category,
    chunk_id: entry.id,
    chunk: entry.text,
    source: 'embedded-canon/1',
  };
}

export async function routeOnline(visitorText, screen, send) {
  const request = makeRequest(visitorText, screen);
  if (request.status === 'NO_DATA') return request;
  if (typeof send !== 'function') return noData('worker_transport_unavailable');
  return send(request);
}
