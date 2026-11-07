// Shared backend helpers: database (Upstash Redis over REST), email (Resend), admin auth, request utils.
// Everything degrades gracefully: if a service is not configured, the site keeps working and the call is skipped.
const crypto = require('crypto');

// ---------- database (Upstash Redis REST; Vercel's "Upstash for Redis" integration sets KV_REST_API_*)
const DB_URL = () => process.env.UPSTASH_REDIS_REST_URL || process.env.KV_REST_API_URL;
const DB_TOKEN = () => process.env.UPSTASH_REDIS_REST_TOKEN || process.env.KV_REST_API_TOKEN;
const dbReady = () => !!(DB_URL() && DB_TOKEN());

async function db(...commands) { // db(['SET','k','v'], ['INCR','n']) -> array of results
  if (!dbReady()) return null;
  const r = await fetch(DB_URL().replace(/\/$/, '') + '/pipeline', {
    method: 'POST', headers: { Authorization: `Bearer ${DB_TOKEN()}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(commands),
  });
  if (!r.ok) throw new Error('Database error ' + r.status);
  const out = await r.json();
  return out.map((x) => (x && 'result' in x ? x.result : null));
}

// ---------- email (Resend)
const mailReady = () => !!process.env.RESEND_API_KEY;
async function sendMail({ to, subject, html, replyTo }) {
  if (!mailReady() || !to) return { skipped: true };
  const r = await fetch('https://api.resend.com/emails', {
    method: 'POST', headers: { Authorization: `Bearer ${process.env.RESEND_API_KEY}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ from: process.env.MAIL_FROM || 'Hexstar Universe <onboarding@resend.dev>', to: Array.isArray(to) ? to : [to], subject, html, ...(replyTo ? { reply_to: replyTo } : {}) }),
  });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) console.error('Resend error', r.status, j);
  return j;
}
const adminEmails = () => (process.env.ADMIN_EMAIL || '').split(',').map((s) => s.trim()).filter(Boolean);

// ---------- admin auth (stateless signed token, 12 h)
const authKey = () => process.env.ADMIN_PASSWORD ? crypto.createHash('sha256').update('hx-admin|' + process.env.ADMIN_PASSWORD).digest() : null;
function makeToken() {
  const exp = Date.now() + 12 * 3600 * 1000;
  const sig = crypto.createHmac('sha256', authKey()).update(String(exp)).digest('hex');
  return `${exp}.${sig}`;
}
function checkToken(req) {
  const key = authKey(); if (!key) return false;
  const t = String(req.headers.authorization || '').replace(/^Bearer\s+/i, '');
  const [exp, sig] = t.split('.');
  if (!exp || !sig || Number(exp) < Date.now()) return false;
  const good = crypto.createHmac('sha256', key).update(exp).digest('hex');
  return good.length === sig.length && crypto.timingSafeEqual(Buffer.from(good), Buffer.from(sig));
}
function passwordOk(p) {
  const want = process.env.ADMIN_PASSWORD || '';
  if (!want) return false;
  const a = crypto.createHash('sha256').update(String(p || '')).digest(), b = crypto.createHash('sha256').update(want).digest();
  return crypto.timingSafeEqual(a, b);
}

// ---------- request helpers
function body(req) { let b = req.body; if (typeof b === 'string') { try { b = JSON.parse(b); } catch { b = {}; } } return b || {}; }
function rawBody(req) { return new Promise((res) => { if (req.readableEnded || req.complete && !req.readable) return res(''); let d = ''; const t = setTimeout(() => res(d), 2000); req.on('data', (c) => (d += c)); req.on('end', () => { clearTimeout(t); res(d); }); req.on('error', () => { clearTimeout(t); res(d); }); }); }
const country = (req) => String(req.headers['x-vercel-ip-country'] || '').toUpperCase().slice(0, 2) || 'XX';
const ip = (req) => String(req.headers['x-forwarded-for'] || req.socket?.remoteAddress || '').split(',')[0].trim();
const visitorHash = (req, day) => crypto.createHash('sha256').update(`${day}|${ip(req)}|${req.headers['user-agent'] || ''}|${process.env.RAZORPAY_KEY_SECRET || 'hx'}`).digest('hex').slice(0, 24);
const today = () => new Date().toISOString().slice(0, 10);
const siteUrl = (req) => (process.env.SITE_URL || `https://${req.headers['x-forwarded-host'] || req.headers.host || ''}`).replace(/\/$/, '');
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

// ---------- money formatting
function money(amountMinor, currency) {
  const v = amountMinor / 100;
  return currency === 'USD' ? '$' + v.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '₹' + v.toLocaleString('en-IN', { maximumFractionDigits: 2 });
}

module.exports = { db, dbReady, sendMail, mailReady, adminEmails, makeToken, checkToken, passwordOk, body, rawBody, country, visitorHash, today, siteUrl, esc, money };
