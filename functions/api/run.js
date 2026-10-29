// POST /api/run  {type, pin}
// Checks the PIN, then starts a market run for the aircraft type (Claude scheduled task, fired by API).
// Secrets set in Cloudflare Pages settings: RUN_PIN, ROUTINE_TOKEN, ROUTINE_FIRE_URL. KV binding: AMF_KV.

const MAX_BAD_PIN = 5;          // wrong PINs allowed per address per hour
const SAME_TYPE_HOLD_MIN = 120; // the same type cannot be started twice inside this window

const json = (obj, status = 200) =>
  new Response(JSON.stringify(obj), { status, headers: { 'content-type': 'application/json', 'cache-control': 'no-store' } });

const slugOf = t => t.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 50);

export async function onRequestPost({ request, env }) {
  if (!env.RUN_PIN || !env.ROUTINE_TOKEN || !env.ROUTINE_FIRE_URL || !env.AMF_KV)
    return json({ ok: false, error: 'The Run button is not set up yet.' }, 503);

  let body;
  try { body = await request.json(); } catch { return json({ ok: false, error: 'Bad request.' }, 400); }
  const type = String(body.type || '').replace(/\s+/g, ' ').trim();
  const pin = String(body.pin || '').trim();
  if (!/^[A-Za-z0-9 .\/\-()]{2,60}$/.test(type))
    return json({ ok: false, error: 'Type a make and model, 2 to 60 letters or numbers.' }, 400);

  const ip = request.headers.get('cf-connecting-ip') || 'unknown';
  const badKey = 'bad:' + ip;
  const bad = parseInt(await env.AMF_KV.get(badKey) || '0', 10);
  if (bad >= MAX_BAD_PIN) return json({ ok: false, error: 'Too many wrong PINs. Try again in an hour.' }, 429);
  if (pin !== env.RUN_PIN) {
    await env.AMF_KV.put(badKey, String(bad + 1), { expirationTtl: 3600 });
    return json({ ok: false, error: 'Wrong PIN.' }, 401);
  }

  const slug = slugOf(type);
  const holdKey = 'hold:' + slug;
  const held = await env.AMF_KV.get(holdKey, 'json');
  if (held) return json({ ok: false, error: `A run for ${held.type} was started at ${held.at}. Wait for it to finish.`, request: held }, 409);

  const id = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15) + '-' + slug;
  const text = `Aircraft type requested from the web page: ${type}\nRequest id: ${id}\nType slug: ${slug}`;
  const r = await fetch(env.ROUTINE_FIRE_URL, {
    method: 'POST',
    headers: { 'Authorization': 'Bearer ' + env.ROUTINE_TOKEN, 'anthropic-version': '2023-06-01', 'content-type': 'application/json' },
    body: JSON.stringify({ text }),
  });
  if (!r.ok) {
    const detail = r.status === 429 ? 'Run limit reached for this hour.' : 'Could not start the run (' + r.status + ').';
    return json({ ok: false, error: detail }, 502);
  }
  const fired = await r.json().catch(() => ({}));
  const rec = { id, type, slug, at: new Date().toISOString(), session_url: fired.claude_code_session_url || null };
  await env.AMF_KV.put('req:' + id, JSON.stringify(rec), { expirationTtl: 60 * 60 * 24 * 30 });
  await env.AMF_KV.put(holdKey, JSON.stringify(rec), { expirationTtl: SAME_TYPE_HOLD_MIN * 60 });
  return json({ ok: true, request: rec });
}

export async function onRequest() {
  return json({ ok: false, error: 'Use POST.' }, 405);
}
