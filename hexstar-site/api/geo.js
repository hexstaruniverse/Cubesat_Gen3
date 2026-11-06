// GET /api/geo: returns the visitor's country code from Vercel's edge headers (no third-party lookup).
module.exports = (req, res) => {
  res.setHeader('Cache-Control', 'no-store');
  res.status(200).json({ country: req.headers['x-vercel-ip-country'] || null });
};
