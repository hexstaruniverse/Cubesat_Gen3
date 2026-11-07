// POST /api/verify: checks the Razorpay payment signature, marks the order paid, and sends the confirmation emails.
const crypto = require('crypto');
const { body } = require('./_lib');
const { markPaid } = require('./_orders');

module.exports = async (req, res) => {
  if (req.method !== 'POST') { res.setHeader('Allow', 'POST'); return res.status(405).json({ error: 'Method not allowed' }); }
  const secret = process.env.RAZORPAY_KEY_SECRET;
  if (!secret) return res.status(503).json({ error: 'Payments are not configured.' });
  const { razorpay_order_id: o, razorpay_payment_id: p, razorpay_signature: sig } = body(req);
  if (!o || !p || !sig) return res.status(400).json({ ok: false, error: 'Missing payment details.' });
  const expected = crypto.createHmac('sha256', secret).update(`${o}|${p}`).digest('hex');
  const ok = expected.length === String(sig).length && crypto.timingSafeEqual(Buffer.from(expected), Buffer.from(String(sig)));
  if (!ok) return res.status(400).json({ ok: false });
  try { await markPaid(req, o, p, 'checkout'); } catch (e) { console.error('markPaid', e); }
  return res.status(200).json({ ok: true, payment_id: p, order_id: o });
};
