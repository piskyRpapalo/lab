import { MAX_REQUEST_BYTES, resolveSignal } from './core.mjs';

const HEADERS = {
  'content-type': 'application/json; charset=utf-8',
  'cache-control': 'no-store',
  'x-content-type-options': 'nosniff',
};

function reply(body, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: HEADERS });
}

export async function fetch(request) {
  if (request.method !== 'POST') return reply({ status: 'NO_DATA', cause: 'method_not_allowed' }, 405);
  if ((request.headers.get('content-type') || '').split(';', 1)[0].trim().toLowerCase() !== 'application/json') {
    return reply({ status: 'NO_DATA', cause: 'content_type_invalid' }, 415);
  }
  const declaredLength = Number(request.headers.get('content-length'));
  if (Number.isFinite(declaredLength) && declaredLength > MAX_REQUEST_BYTES) {
    return reply({ status: 'NO_DATA', cause: 'request_over_1024_bytes' }, 413);
  }
  const reader = request.body?.getReader();
  if (!reader) return reply({ status: 'NO_DATA', cause: 'request_body_missing' }, 400);
  const parts = [];
  let length = 0;
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    length += value.byteLength;
    if (length > MAX_REQUEST_BYTES) {
      await reader.cancel();
      return reply({ status: 'NO_DATA', cause: 'request_over_1024_bytes' }, 413);
    }
    parts.push(value);
  }
  const bytes = new Uint8Array(length);
  let offset = 0;
  for (const part of parts) {
    bytes.set(part, offset);
    offset += part.byteLength;
  }
  let payload;
  try {
    payload = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(bytes));
  } catch {
    return reply({ status: 'NO_DATA', cause: 'request_json_invalid' }, 400);
  }
  const result = resolveSignal(payload);
  return reply(result, result.status === 'CHUNK' ? 200 : 400);
}

export default { fetch };
