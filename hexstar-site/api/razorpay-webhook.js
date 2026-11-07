// POST /api/razorpay-webhook: Razorpay calls this when a payment is captured, so an order is confirmed
// (and emailed) even if the customer closed the tab before the success screen.
// Set the same secret in Razorpay (Settings -> Webhooks) and in Vercel as RAZORPAY_WEBHOOK_SECRET.
const crypto = require('crypto');
const { rawBody } = require('./_lib');
const { markPaid } = require('./_orders');

module.exports = async (req, res) => {
  if (req.method !== 'POST') return res.status(405).end();
  const secret = process.env.RAZORPAY_WEBHOOK_SECRET;
  if (!secret) return res.status(503).json({ error: 'Webhook secret not set' });
  // read the exact bytes Razorpay signed (before anything parses the body)
  let raw = await rawBody(req).catch(() => '');
  if (!raw) raw = typeof req.body === 'string' ? req.body : JSON.stringify(req.body || {});
  const sig = String(req.headers['x-razorpay-signature'] || '');
  const expected = crypto.createHmac('sha256', secret).update(raw).digest('hex');
  if (!(sig.length === expected.length && crypto.timingSafeEqual(Buffer.from(sig), Buffer.from(expected)))) return res.status(400).json({ error: 'Bad signature' });
  let ev = {}; try { ev = JSON.parse(raw); } catch {}
  const pay = ev?.payload?.payment?.entity, ord = ev?.payload?.order?.entity;
  if ((ev.event === 'payment.captured' || ev.event === 'order.paid') && (pay?.order_id || ord?.id)) {
    try { await markPaid(req, pay?.order_id || ord.id, pay?.id || '', 'webhook'); } catch (e) { console.error(e); }
  }
  return res.status(200).json({ ok: true });
};
