// The drop: guests' photographs and films, received into a private R2 bucket.
// Runs on Cloudflare Workers (free plan). The page at coleswedding.com/your-photographs
// talks to this in four moves: open, part (one or more), close; abort on failure.
//
// Rules baked in:
//   - only coleswedding.com may call it (Origin check) and only until CLOSES
//   - the caller must present a fingerprint from the guest list (the same salted
//     SHA-256 the door uses); no fingerprint, no upload
//   - object keys carry the day, the guest's four-character mark and a random
//     id, never a name; the guest's name travels in the request BODY and is kept
//     only as object metadata, visible to the couple in the dashboard
//   - files must be image/* or video/*, up to MAX_BYTES each
//   - parts are PART_BYTES each (Workers bodies are capped at 100 MB, so whole
//     films are never posted in one go)

const DAY = '2026-08-14';
const PART_BYTES = 8 * 1024 * 1024;            // 8 MiB; all parts equal but the last (R2 rule)
const MAX_BYTES = 2 * 1024 * 1024 * 1024;      // 2 GiB per file
const KEY_RE = /^2026-08-14\/[0-9a-f]{4}\/[0-9a-f-]{36}\.[a-z0-9]{1,5}$/;

function json(body, status, headers) {
  return new Response(JSON.stringify(body), {
    status, headers: Object.assign({ 'Content-Type': 'application/json' }, headers),
  });
}
function clean(s, n) { return String(s || '').replace(/[\x00-\x1f\x7f]/g, '').slice(0, n); }

export default {
  async fetch(request, env) {
    const cors = {
      'Access-Control-Allow-Origin': env.ALLOWED_ORIGIN,
      'Access-Control-Allow-Methods': 'POST, PUT, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, X-CA-Key, X-CA-Upload, X-CA-Part',
      'Access-Control-Max-Age': '86400',
      'Vary': 'Origin',
    };
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors });
    if ((request.headers.get('Origin') || '') !== env.ALLOWED_ORIGIN) return json({ error: 'origin' }, 403, cors);
    if (env.CLOSES && Date.now() > Date.parse(env.CLOSES)) return json({ error: 'closed' }, 410, cors);

    const path = new URL(request.url).pathname;
    const hashes = new Set((env.HASHES || '').split(',').map(s => s.trim()).filter(Boolean));

    try {
      if (request.method === 'POST' && path === '/open') {
        const b = await request.json();
        const fp = clean(b.fp, 64);
        if (!hashes.has(fp)) return json({ error: 'unknown' }, 403, cors);
        const type = clean(b.type, 80);
        if (!/^(image|video)\//.test(type)) return json({ error: 'type' }, 415, cors);
        const size = Number(b.size) || 0;
        if (size <= 0 || size > MAX_BYTES) return json({ error: 'size' }, 413, cors);
        const ext = clean(b.ext, 8).toLowerCase().replace(/[^a-z0-9]/g, '').slice(0, 5)
          || (type.startsWith('video/') ? 'mov' : 'jpg');
        const key = `${DAY}/${fp.slice(0, 4)}/${crypto.randomUUID()}.${ext}`;
        const mpu = await env.PHOTOS.createMultipartUpload(key, {
          httpMetadata: { contentType: type },
          customMetadata: {
            guest: clean(b.guest, 80),
            mark: fp.slice(0, 4),
            original: clean(b.name, 120),
            taken: clean(b.taken, 40),
            bytes: String(size),
          },
        });
        return json({ key, uploadId: mpu.uploadId, part: PART_BYTES }, 200, cors);
      }

      if (request.method === 'PUT' && path === '/part') {
        const key = request.headers.get('X-CA-Key') || '';
        const uploadId = request.headers.get('X-CA-Upload') || '';
        const n = parseInt(request.headers.get('X-CA-Part') || '0', 10);
        if (!KEY_RE.test(key) || !uploadId || !(n >= 1 && n <= 10000)) return json({ error: 'part' }, 400, cors);
        const body = await request.arrayBuffer();
        if (body.byteLength === 0 || body.byteLength > PART_BYTES) return json({ error: 'partsize' }, 413, cors);
        const mpu = env.PHOTOS.resumeMultipartUpload(key, uploadId);
        const part = await mpu.uploadPart(n, body);
        return json({ partNumber: part.partNumber, etag: part.etag }, 200, cors);
      }

      if (request.method === 'POST' && path === '/close') {
        const b = await request.json();
        const key = clean(b.key, 80), uploadId = clean(b.uploadId, 400);
        if (!KEY_RE.test(key) || !uploadId || !Array.isArray(b.parts) || !b.parts.length) return json({ error: 'close' }, 400, cors);
        const mpu = env.PHOTOS.resumeMultipartUpload(key, uploadId);
        const obj = await mpu.complete(b.parts.map(p => ({ partNumber: Number(p.partNumber), etag: String(p.etag) })));
        return json({ received: true, bytes: obj.size }, 200, cors);
      }

      if (request.method === 'POST' && path === '/abort') {
        const b = await request.json();
        const key = clean(b.key, 80), uploadId = clean(b.uploadId, 400);
        if (KEY_RE.test(key) && uploadId) {
          try { await env.PHOTOS.resumeMultipartUpload(key, uploadId).abort(); } catch (e) {}
        }
        return json({ aborted: true }, 200, cors);
      }
    } catch (e) {
      return json({ error: 'failed' }, 500, cors);
    }
    return json({ error: 'not found' }, 404, cors);
  },
};
