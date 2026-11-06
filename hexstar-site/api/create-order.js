// POST /api/create-order: validates the checkout form and creates a Razorpay order.
// Needs RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET set as Vercel environment variables.
const { KITS, bookingAmount, validate, line } = require('./_shop');

module.exports = async (req, res) => {
  if (req.method !== 'POST') { res.setHeader('Allow', 'POST'); return res.status(405).json({ error: 'Method not allowed' }); }
  const keyId = process.env.RAZORPAY_KEY_ID, secret = process.env.RAZORPAY_KEY_SECRET;
  if (!keyId || !secret) return res.status(503).json({ error: 'Payments are not configured yet. Please try again soon.' });

  let body = req.body;
  if (typeof body === 'string') { try { body = JSON.parse(body); } catch { body = {}; } }
  const v = validate(body || {});
  if (v.errors.length) return res.status(400).json({ error: v.errors.join(' ') });

  const amount = bookingAmount(v.currency, v.qty);
  const notes = {
    kit: `${KITS[v.kit].name} x ${v.qty}`,
    type: 'Pre-order booking',
    name: v.contact.name,
    email: v.contact.email,
    phone: v.contact.phone,
    shipping: line(v.shipping),
    billing: v.billingSame ? 'Same as shipping' : line(v.billing),
  };
  if (v.business) { notes.company = v.business.company; if (v.business.gstin) notes.gstin = v.business.gstin; }

  try {
    const r = await fetch('https://api.razorpay.com/v1/orders', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: 'Basic ' + Buffer.from(`${keyId}:${secret}`).toString('base64') },
      body: JSON.stringify({ amount, currency: v.currency, receipt: `hx_${Date.now()}`, notes }),
    });
    const data = await r.json();
    if (!r.ok) return res.status(502).json({ error: data?.error?.description || 'Could not start the payment.' });
    return res.status(200).json({ order_id: data.id, amount: data.amount, currency: data.currency, key_id: keyId, kit: KITS[v.kit].name, qty: v.qty });
  } catch (e) {
    return res.status(502).json({ error: 'Payment service unreachable. Please try again.' });
  }
};
