// Order storage and the "you're booked" emails. Used by create-order, verify and the Razorpay webhook.
const { db, sendMail, adminEmails, siteUrl, esc, money } = require('./_lib');
const { KITS, BOOKING_INR, USD_RATE } = require('./_shop');

async function saveOrder(o) {
  await db(['SET', `order:${o.id}`, JSON.stringify(o)], ['ZADD', 'orders', String(o.created), o.id]);
}
async function getOrder(id) {
  const r = await db(['GET', `order:${id}`]);
  return r && r[0] ? JSON.parse(r[0]) : null;
}

// Rebuild an order record from Razorpay when it is not in our database (e.g. only the webhook arrived).
async function fetchRazorpayOrder(id) {
  const k = process.env.RAZORPAY_KEY_ID, s = process.env.RAZORPAY_KEY_SECRET;
  if (!k || !s) return null;
  const r = await fetch(`https://api.razorpay.com/v1/orders/${encodeURIComponent(id)}`, { headers: { Authorization: 'Basic ' + Buffer.from(`${k}:${s}`).toString('base64') } });
  if (!r.ok) return null;
  const d = await r.json(), n = d.notes || {};
  return { id: d.id, created: (d.created_at || 0) * 1000 || Date.now(), status: 'created', amount: d.amount, currency: d.currency,
    kit: n.kit || '', qty: null, contact: { name: n.name || '', email: n.email || '', phone: n.phone || '' },
    shippingText: n.shipping || '', billingText: n.billing || '', business: n.company ? { company: n.company, gstin: n.gstin || '' } : null };
}

// Mark paid once (idempotent) and send both emails exactly once.
async function markPaid(req, orderId, paymentId, source) {
  let o = (await getOrder(orderId).catch(() => null)) || (await fetchRazorpayOrder(orderId).catch(() => null));
  if (!o) return { ok: false };
  if (o.status !== 'paid') { o.status = 'paid'; o.paidAt = Date.now(); o.paymentId = paymentId; o.confirmedBy = source; await saveOrder(o).catch(() => {}); }
  // send emails only once per order
  const first = await db(['SET', `mailed:${orderId}`, '1', 'NX', 'EX', String(60 * 60 * 24 * 90)]).catch(() => null);
  const shouldMail = first === null ? !o.mailed : first[0] === 'OK';
  if (shouldMail) {
    o.mailed = true;
    await Promise.allSettled([sendCustomerMail(req, o), sendAdminMail(req, o)]);
    await saveOrder(o).catch(() => {});
  }
  return { ok: true, order: o };
}

const addr = (a) => a ? [a.line1, a.line2, a.city, a.state, a.postal, a.country].filter(Boolean).map(esc).join(', ') : '';

function shell(req, inner, preheader) {
  const img = `${siteUrl(req)}/assets/email-cubesat.jpg`, logo = `${siteUrl(req)}/assets/logo.png`;
  return `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="dark light"></head>
<body style="margin:0;background:#000;font-family:Helvetica,Arial,sans-serif;color:#f2f2f0">
<span style="display:none;max-height:0;overflow:hidden">${esc(preheader)}</span>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#000"><tr><td align="center" style="padding:28px 12px">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#0b0b0c;border:1px solid #222;border-radius:18px;overflow:hidden">
<tr><td style="padding:22px 28px"><img src="${logo}" alt="Hexstar Universe" height="30" style="display:block;height:30px"></td></tr>
<tr><td><img src="${img}" alt="Hexstar 1U CubeSat" width="600" style="display:block;width:100%;height:auto"></td></tr>
<tr><td style="padding:30px 28px 10px">${inner}</td></tr>
<tr><td style="padding:22px 28px 30px;color:#77777a;font-size:12px;line-height:1.6;border-top:1px solid #1d1d1f">Hexstar Universe · Designed for the next generation of space engineers.<br>Questions? Just reply to this email.</td></tr>
</table></td></tr></table></body></html>`;
}
const row = (k, v) => `<tr><td style="padding:9px 0;border-bottom:1px solid #1f1f22;color:#9a9a98;font-size:14px">${k}</td><td style="padding:9px 0;border-bottom:1px solid #1f1f22;color:#f2f2f0;font-size:14px;text-align:right">${v}</td></tr>`;

function summary(o) {
  const kitName = esc(KITS[o.kitId]?.name || o.kit || 'Kit'), qty = o.qty || 1;
  const fullInr = (KITS[o.kitId]?.inr || 0) * qty;
  const full = o.currency === 'USD' ? money(Math.round((fullInr / USD_RATE) * 100), 'USD') : money(fullInr * 100, 'INR') + ' + GST';
  return `<table role="presentation" width="100%" cellpadding="0" cellspacing="0">${row('Kit', `${kitName} × ${qty}`)}${row('Paid today (booking)', money(o.amount, o.currency))}${fullInr ? row('Full price', full) : ''}${o.paymentId ? row('Payment ID', esc(o.paymentId)) : ''}${row('Order ID', esc(o.id))}</table>`;
}

async function sendCustomerMail(req, o) {
  if (!o.contact?.email) return;
  const name = esc((o.contact.name || '').split(' ')[0] || 'there');
  const inner = `<h1 style="margin:0 0 10px;font-size:30px;font-weight:500;letter-spacing:-.5px">You're booked, ${name}.</h1>
<p style="margin:0 0 22px;color:#bdbdba;font-size:15px;line-height:1.6">Thank you for pre-ordering the Hexstar 1U CubeSat. Your booking is confirmed. We'll email you before shipping (estimated Q1 2027) with the balance due and your delivery details.</p>
${summary(o)}
${o.shipping || o.shippingText ? `<p style="margin:22px 0 4px;color:#9a9a98;font-size:12px;letter-spacing:2px;text-transform:uppercase">Shipping to</p><p style="margin:0;color:#e6e6e3;font-size:14px;line-height:1.6">${o.shipping ? addr(o.shipping) : esc(o.shippingText)}</p>` : ''}
${o.business?.company ? `<p style="margin:16px 0 0;color:#e6e6e3;font-size:14px">Invoice to: ${esc(o.business.company)}${o.business.gstin ? ' · GSTIN ' + esc(o.business.gstin) : ''}</p>` : ''}`;
  return sendMail({ to: o.contact.email, subject: "You're booked: your Hexstar CubeSat pre-order", html: shell(req, inner, 'Your Hexstar CubeSat pre-order is confirmed.'), replyTo: adminEmails()[0] });
}

async function sendAdminMail(req, o) {
  const to = adminEmails(); if (!to.length) return;
  const c = o.contact || {};
  const inner = `<h1 style="margin:0 0 14px;font-size:26px;font-weight:500">New pre-order: ${money(o.amount, o.currency)}</h1>
${summary(o)}
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-top:14px">${row('Customer', esc(c.name))}${row('Email', esc(c.email))}${row('Phone', esc(c.phone))}
${row('Shipping', o.shipping ? addr(o.shipping) : esc(o.shippingText || ''))}${row('Billing', o.billingSame === false && o.billing ? addr(o.billing) : 'Same as shipping')}
${o.business?.company ? row('Company', esc(o.business.company)) : ''}${o.business?.gstin ? row('GSTIN', esc(o.business.gstin)) : ''}${row('Confirmed by', esc(o.confirmedBy || ''))}</table>
<p style="margin:20px 0 0"><a href="${siteUrl(req)}/admin.html" style="color:#000;background:#f2f2f0;padding:11px 18px;border-radius:999px;text-decoration:none;font-size:13px">Open admin panel</a></p>`;
  return sendMail({ to, subject: `New pre-order · ${c.name || ''} · ${money(o.amount, o.currency)}`, html: shell(req, inner, 'New Hexstar pre-order'), replyTo: c.email });
}

module.exports = { saveOrder, getOrder, markPaid, shell, row };
