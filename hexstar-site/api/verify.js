// POST /api/verify: checks the Razorpay payment signature so a success screen is only shown for a real payment.
const crypto = require('crypto');

module.exports = async (req, res) => {
  if (req.method !== 'POST') { res.setHeader('Allow', 'POST'); return res.status(405).json({ error: 'Method not allowed' }); }
  const secret = process.env.RAZORPAY_KEY_SECRET;
  if (!secret) return res.status(503).json({ error: 'Payments are not configured.' });
  let b = req.body;
  if (typeof b === 'string') { try { b = JSON.parse(b); } catch { b = {}; } }
  const { razorpay_order_id: o, razorpay_payment_id: p, razorpay_signature: sig } = b || {};
  if (!o || !p || !sig) return res.status(400).json({ ok: false, error: 'Missing payment details.' });
  const expected = crypto.createHmac('sha256', secret).update(`${o}|${p}`).digest('hex');
  const ok = expected.length === String(sig).length && crypto.timingSafeEqual(Buffer.from(expected), Buffer.from(String(sig)));
  return res.status(ok ? 200 : 400).json({ ok, payment_id: ok ? p : undefined, order_id: ok ? o : undefined });
};
