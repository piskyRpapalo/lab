import { decide, downloadAndVerify, IndexedChunkCache, loadCached } from './chunk-model.mjs';

const cache = new IndexedChunkCache();
const status = document.querySelector('#status');
const manifest = await (await fetch('./model/manifest.json')).json();
const size = manifest.total_bytes.toLocaleString('en-US');
document.querySelector('#model-size').textContent = `Exact payload: ${size} bytes (25 MB decimal; 23.84 MiB).`;
document.querySelector('#model-origin').textContent = `Origin shown before weight download: ${new URL('./model/', location.href).href}`;
for (const chunk of manifest.chunks) {
  const row = document.createElement('li');
  row.textContent = `${chunk.file}: ${chunk.byte_length.toLocaleString('en-US')} bytes; offset ${chunk.byte_offset.toLocaleString('en-US')}; SHA-256 ${chunk.sha256}`;
  document.querySelector('#chunk-list').append(row);
}
let weights = null;

function report(result) {
  if (result.status === 'NO_DATA') {
    status.textContent = `NO_DATA · ${result.cause}`;
    window.AtlasRadioChat.dice({ quien: 'Preceptor', fuente: 'chunked-web-demo', sello: 'NO_DATA', texto: `NO_DATA · ${result.cause}` });
    return;
  }
  status.textContent = result.status === 'READY' ? 'SIMULATED · all chunks hash-verified' : `SIMULATED · ${result.category}`;
  if (result.status !== 'READY') {
    window.AtlasRadioChat.dice({ quien: 'Preceptor', fuente: 'chunked-web-demo', sello: 'SIMULATED', texto: result.text });
  }
}

document.querySelector('#download').addEventListener('click', async () => {
  status.textContent = 'Downloading only after explicit action; verifying each chunk…';
  const result = await downloadAndVerify(manifest, cache);
  weights = result.status === 'READY' ? result.weights : null;
  report(result);
});
document.querySelector('#load').addEventListener('click', async () => {
  const result = await loadCached(manifest, cache);
  weights = result.status === 'READY' ? result.weights : null;
  report(result);
});
document.querySelector('#ask').addEventListener('click', () => {
  report(decide(document.querySelector('#input').value, weights));
});
