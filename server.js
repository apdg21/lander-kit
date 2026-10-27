// Local / VPS / Render / Railway server: serves /public and the /api/fetch endpoint. No dependencies.
// Start:  node server.js   (PORT env optional, default 3000)
const http = require('http');
const fs = require('fs');
const path = require('path');
const { fetchPage } = require('./lib/fetchCore');

const PUBLIC = path.join(__dirname, 'public');
const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.svg': 'image/svg+xml', '.png': 'image/png', '.ico': 'image/x-icon', '.json': 'application/json' };

http.createServer(async (req, res) => {
  const u = new URL(req.url, 'http://x');
  if (u.pathname === '/api/fetch') {
    let body;
    try { body = await fetchPage(u.searchParams.get('url') || '', u.searchParams.get('mode') || 'auto'); }
    catch (e) { body = { ok: false, error: e.message }; }
    res.writeHead(200, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
    return res.end(JSON.stringify(body));
  }
  let file = path.normalize(path.join(PUBLIC, u.pathname === '/' ? 'index.html' : u.pathname));
  if (!file.startsWith(PUBLIC)) { res.writeHead(403); return res.end(); }
  fs.readFile(file, (err, data) => {
    if (err) { res.writeHead(404); return res.end('Not found'); }
    res.writeHead(200, { 'Content-Type': TYPES[path.extname(file)] || 'application/octet-stream' });
    res.end(data);
  });
}).listen(process.env.PORT || 3000, '0.0.0.0', () => console.log('Landing Kit running on port ' + (process.env.PORT || 3000)));
