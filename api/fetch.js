// Vercel serverless function → available at /api/fetch?url=...&mode=auto|direct|reader
const { fetchPage } = require('../lib/fetchCore');

module.exports = async (req, res) => {
  let body;
  try { body = await fetchPage(req.query.url || '', req.query.mode || 'auto'); }
  catch (e) { body = { ok: false, error: e.message }; }
  res.setHeader('Content-Type', 'application/json');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.status(200).send(JSON.stringify(body));
};
