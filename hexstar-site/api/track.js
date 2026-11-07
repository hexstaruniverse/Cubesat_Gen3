// POST /api/track: counts a visit (once per browser session) by day and by country.
// Stores no IP addresses: unique visitors are counted with a one-way daily hash.
const { db, country, visitorHash, today, body } = require('./_lib');

module.exports = async (req, res) => {
  res.setHeader('Cache-Control', 'no-store');
  if (req.method !== 'POST') return res.status(405).end();
  const ua = String(req.headers['user-agent'] || '');
  if (/bot|crawl|spider|slurp|preview|headless/i.test(ua)) return res.status(204).end();
  const d = today(), cc = country(req), h = visitorHash(req, d), page = String(body(req).page || '/').slice(0, 40);
  try {
    await db(['INCR', 'v:total'], ['HINCRBY', 'v:day', d, '1'], ['HINCRBY', 'v:country', cc, '1'], ['HINCRBY', 'v:page', page, '1'],
      ['PFADD', 'v:uniq', h], ['PFADD', `v:uniq:${d}`, h], ['EXPIRE', `v:uniq:${d}`, String(60 * 60 * 24 * 120)]);
  } catch (e) { /* tracking must never break the site */ }
  return res.status(204).end();
};
