// POST /api/inquiry: stores an enquiry, emails it to the admin and sends the visitor a short acknowledgement.
const crypto = require('crypto');
const { db, body, sendMail, adminEmails, esc, country, visitorHash, today } = require('./_lib');
const { shell, row } = require('./_orders');
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const clean = (v, n) => String(v ?? '').replace(/[\u0000-\u001f]/g, ' ').trim().slice(0, n);
const TOPICS = ['Pre-order', 'Schools & bulk orders', 'Partnership', 'Technical question', 'Other'];

module.exports = async (req, res) => {
  if (req.method !== 'POST') { res.setHeader('Allow', 'POST'); return res.status(405).json({ error: 'Method not allowed' }); }
  const b = body(req);
  if (b.website) return res.status(200).json({ ok: true }); // spam trap
  const q = { name: clean(b.name, 80), email: clean(b.email, 120), phone: clean(b.phone, 20), org: clean(b.org, 100), topic: TOPICS.includes(b.topic) ? b.topic : 'Other', message: clean(b.message, 2000) };
  const errs = [];
  if (q.name.length < 2) errs.push('Enter your name.');
  if (!EMAIL_RE.test(q.email)) errs.push('Enter a valid email.');
  if (q.phone.replace(/\D/g, '').length < 7) errs.push('Enter a valid phone number.');
  if (q.message.length < 5) errs.push('Write a short message.');
  if (errs.length) return res.status(400).json({ error: errs.join(' ') });
  // basic rate limit: 6 enquiries per visitor per hour
  const rl = `rl:inq:${visitorHash(req, today())}:${new Date().getUTCHours()}`;
  const r = await db(['INCR', rl], ['EXPIRE', rl, '3600']).catch(() => null);
  if (r && r[0] > 6) return res.status(429).json({ error: 'Too many messages. Please try again later.' });
  const id = 'inq_' + Date.now().toString(36) + crypto.randomBytes(3).toString('hex');
  const rec = { id, created: Date.now(), country: country(req), status: 'new', ...q };
  await db(['SET', `inq:${id}`, JSON.stringify(rec)], ['ZADD', 'inquiries', String(rec.created), id]).catch(() => {});
  const to = adminEmails();
  const adminHtml = shell(req, `<h1 style="margin:0 0 14px;font-size:24px;font-weight:500">New enquiry: ${esc(q.topic)}</h1>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0">${row('Name', esc(q.name))}${row('Email', esc(q.email))}${row('Phone', esc(q.phone))}${q.org ? row('Organisation', esc(q.org)) : ''}${row('Country', esc(rec.country))}</table>
<p style="margin:18px 0 0;color:#e6e6e3;font-size:15px;line-height:1.6;white-space:pre-wrap">${esc(q.message)}</p>`, 'New enquiry from the website');
  const userHtml = shell(req, `<h1 style="margin:0 0 10px;font-size:26px;font-weight:500">Thanks, ${esc(q.name.split(' ')[0])}. We got your message.</h1>
<p style="margin:0;color:#bdbdba;font-size:15px;line-height:1.6">Our team will get back to you within 1–2 working days. Here's a copy of what you sent:</p>
<p style="margin:16px 0 0;color:#e6e6e3;font-size:14px;line-height:1.6;white-space:pre-wrap;border-left:2px solid #333;padding-left:12px">${esc(q.message)}</p>`, 'We received your enquiry');
  await Promise.allSettled([to.length ? sendMail({ to, subject: `Enquiry · ${q.topic} · ${q.name}`, html: adminHtml, replyTo: q.email }) : null,
    sendMail({ to: q.email, subject: 'We received your enquiry: Hexstar Universe', html: userHtml, replyTo: to[0] })]);
  return res.status(200).json({ ok: true });
};
