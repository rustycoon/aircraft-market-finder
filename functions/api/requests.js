// GET /api/requests — the last 30 days of Run requests (type and time only, newest first).
export async function onRequestGet({ env }) {
  const out = [];
  if (env.AMF_KV) {
    const list = await env.AMF_KV.list({ prefix: 'req:', limit: 100 });
    for (const k of list.keys) {
      const r = await env.AMF_KV.get(k.name, 'json');
      if (r) out.push({ id: r.id, type: r.type, slug: r.slug, at: r.at });
    }
  }
  out.sort((a, b) => b.at.localeCompare(a.at));
  return new Response(JSON.stringify({ ok: true, ready: !!(env.AMF_KV && env.RUN_PIN && env.ROUTINE_TOKEN), requests: out.slice(0, 20) }),
    { headers: { 'content-type': 'application/json', 'cache-control': 'no-store' } });
}
