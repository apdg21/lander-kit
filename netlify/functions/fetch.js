// Netlify function → /api/fetch is redirected here (see netlify.toml)
const { fetchPage } = require('../../lib/fetchCore');

exports.handler = async (event) => {
  const q = event.queryStringParameters || {};
  let body;
  try { body = await fetchPage(q.url || '', q.mode || 'auto'); }
  catch (e) { body = { ok: false, error: e.message }; }
  return { statusCode: 200, headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }, body: JSON.stringify(body) };
};
