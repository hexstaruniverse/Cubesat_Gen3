// /api/admin: password login, then orders, enquiries and visitor stats for admin.html.
//   POST {action:'login', password}            -> {token}
//   GET  (Authorization: Bearer <token>)       -> dashboard data
//   POST {action:'inquiry-status', id, status} -> mark an enquiry new / replied / closed
const { db, dbReady, body, makeToken, checkToken, passwordOk, mailReady } = require('./_lib');

const list = async (zkey, prefix, n) => {
  const ids = (await db(['ZRANGE', zkey, '0', String(n - 1), 'REV']))?.[0] || [];
  if (!ids.length) return [];
  const rows = await db(...ids.map((id) => ['GET', `${prefix}:${id}`]));
  return rows.map((r) => { try { return JSON.parse(r); } catch { return null; } }).filter(Boolean);
};
const hashToObj = (a) => { const o = {}; for (let i = 0; a && i < a.length; i += 2) o[a[i]] = Number(a[i + 1]); return o; };

module.exports = async (req, res) => {
  res.setHeader('Cache-Control', 'no-store');
  if (!process.env.ADMIN_PASSWORD) return res.status(503).json({ error: 'Set ADMIN_PASSWORD in Vercel to enable the admin panel.' });
  const b = req.method === 'POST' ? body(req) : {};
  if (req.method === 'POST' && b.action === 'login') {
    await new Promise((r) => setTimeout(r, 400)); // slow down guessing
    return passwordOk(b.password) ? res.status(200).json({ token: makeToken() }) : res.status(401).json({ error: 'Wrong password.' });
  }
  if (!checkToken(req)) return res.status(401).json({ error: 'Please sign in.' });
  if (!dbReady()) return res.status(200).json({ setup: { db: false, mail: mailReady() }, orders: [], inquiries: [], visitors: null });
  if (req.method === 'POST' && b.action === 'inquiry-status') {
    const cur = (await db(['GET', `inq:${b.id}`]))?.[0];
    if (cur) { const q = JSON.parse(cur); q.status = ['new', 'replied', 'closed'].includes(b.status) ? b.status : q.status; await db(['SET', `inq:${q.id}`, JSON.stringify(q)]); }
    return res.status(200).json({ ok: true });
  }
  const [total, days, countries, pages, uniq] = await db(['GET', 'v:total'], ['HGETALL', 'v:day'], ['HGETALL', 'v:country'], ['HGETALL', 'v:page'], ['PFCOUNT', 'v:uniq']);
  const d0 = new Date();const last = [];for (let i = 29; i >= 0; i--) { const d = new Date(d0 - i * 864e5).toISOString().slice(0, 10); last.push(d); }
  const uq = await db(...last.map((d) => ['PFCOUNT', `v:uniq:${d}`]));
  const dayMap = hashToObj(days);
  const [orders, inquiries] = await Promise.all([list('orders', 'order', 500), list('inquiries', 'inq', 500)]);
  return res.status(200).json({
    setup: { db: true, mail: mailReady() },
    visitors: { total: Number(total || 0), unique: Number(uniq || 0), countries: hashToObj(countries), pages: hashToObj(pages), days: last.map((d, i) => ({ d, visits: dayMap[d] || 0, unique: uq[i] || 0 })) },
    orders, inquiries,
  });
};
