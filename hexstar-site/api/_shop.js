// Shared pricing and validation for the Hexstar pre-order API.
// Prices live here, on the server, so a visitor cannot change what they pay.
const KITS = {
  starter:   { name: 'Starter kit',    inr: 25000 },
  mission:   { name: 'Mission kit',    inr: 39000 },
  classroom: { name: 'Classroom pack', inr: 175000 },
};
const BOOKING_INR = 2000;   // pre-order booking amount per kit
const USD_RATE = 115;       // 1 USD = 115 INR
const MAX_QTY = 10;

// Amount in the smallest currency unit (paise / cents), as Razorpay expects.
function bookingAmount(currency, qty) {
  if (currency === 'USD') return Math.round((BOOKING_INR / USD_RATE) * 100) * qty;
  return BOOKING_INR * 100 * qty;
}

const GSTIN_RE = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$/;
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const clean = (v, max = 120) => String(v ?? '').replace(/[\u0000-\u001f]/g, ' ').trim().slice(0, max);

function validate(body) {
  const errors = [];
  const kit = clean(body.kit, 20);
  if (!KITS[kit]) errors.push('Choose a kit.');
  const qty = Number.parseInt(body.qty, 10);
  if (!(qty >= 1 && qty <= MAX_QTY)) errors.push(`Quantity must be between 1 and ${MAX_QTY}.`);
  const c = body.contact || {}, ship = body.shipping || {}, bill = body.billing || {}, biz = body.business || {};
  const contact = { name: clean(c.name, 80), email: clean(c.email, 120), phone: clean(c.phone, 20) };
  if (contact.name.length < 2) errors.push('Enter your full name.');
  if (!EMAIL_RE.test(contact.email)) errors.push('Enter a valid email address.');
  if (contact.phone.replace(/\D/g, '').length < 7) errors.push('Enter a valid phone number.');
  const addr = (a) => ({ line1: clean(a.line1), line2: clean(a.line2), city: clean(a.city, 60), state: clean(a.state, 60), postal: clean(a.postal, 12), country: clean(a.country, 2).toUpperCase() });
  const shipping = addr(ship);
  for (const k of ['line1', 'city', 'postal', 'country']) if (!shipping[k]) errors.push('Complete the shipping address.');
  if (shipping.country === 'IN' && !/^[1-9][0-9]{5}$/.test(shipping.postal)) errors.push('Enter a valid 6-digit PIN code.');
  const billingSame = body.billingSame !== false;
  const billing = billingSame ? shipping : addr(bill);
  if (!billingSame) for (const k of ['line1', 'city', 'postal', 'country']) if (!billing[k]) errors.push('Complete the billing address.');
  const business = { company: clean(biz.company, 100), gstin: clean(biz.gstin, 15).toUpperCase() };
  if (body.isBusiness && !business.company) errors.push('Enter your company name.');
  if (business.gstin && !GSTIN_RE.test(business.gstin)) errors.push('GSTIN looks invalid (15 characters, e.g. 29ABCDE1234F1Z5).');
  // India pays in INR, everyone else in USD.
  const currency = shipping.country === 'IN' ? 'INR' : 'USD';
  return { errors: [...new Set(errors)], kit, qty, contact, shipping, billing, billingSame, business: body.isBusiness ? business : null, currency };
}

const line = (a) => [a.line1, a.line2, a.city, a.state, a.postal, a.country].filter(Boolean).join(', ').slice(0, 250);

module.exports = { KITS, BOOKING_INR, USD_RATE, MAX_QTY, bookingAmount, validate, line };
