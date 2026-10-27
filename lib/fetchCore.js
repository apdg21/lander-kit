// Shared page fetcher used by server.js (local/VPS), Vercel (api/fetch.js) and Netlify (netlify/functions/fetch.js).
// 1) fetches the competitor page directly  2) falls back to the r.jina.ai reader for JS-rendered/blocked pages
// 3) for Shopify product URLs also loads the product JSON (/products/<handle>.js)
const dns = require('dns').promises;
const net = require('net');

const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36';
const MAX_BYTES = 4 * 1024 * 1024;

function isPrivateIp(ip) {
  if (net.isIPv6(ip)) {
    const v = ip.toLowerCase();
    if (v === '::1' || v.startsWith('fc') || v.startsWith('fd') || v.startsWith('fe80')) return true;
    if (v.startsWith('::ffff:')) return isPrivateIp(v.slice(7));
    return false;
  }
  const p = ip.split('.').map(Number);
  return p[0] === 10 || p[0] === 127 || p[0] === 0 ||
    (p[0] === 169 && p[1] === 254) ||
    (p[0] === 172 && p[1] >= 16 && p[1] <= 31) ||
    (p[0] === 192 && p[1] === 168) ||
    (p[0] === 100 && p[1] >= 64 && p[1] <= 127);
}

async function assertPublicUrl(raw) {
  let url;
  try { url = new URL(raw); } catch { throw new Error('Invalid URL'); }
  if (!/^https?:$/.test(url.protocol)) throw new Error('Only http/https URLs are allowed');
  const { address } = await dns.lookup(url.hostname);
  if (isPrivateIp(address)) throw new Error('Private/internal addresses are not allowed');
  return url;
}

async function fetchText(url, timeoutMs = 15000, extraHeaders = {}) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(url, {
      redirect: 'follow',
      signal: ctrl.signal,
      headers: { 'User-Agent': UA, 'Accept': 'text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8', 'Accept-Language': 'en,de;q=0.8,*;q=0.5', ...extraHeaders },
    });
    const buf = Buffer.from(await res.arrayBuffer());
    return { status: res.status, url: res.url, text: buf.subarray(0, MAX_BYTES).toString('utf8') };
  } finally { clearTimeout(t); }
}

function visibleTextLength(html) {
  return html.replace(/<script[\s\S]*?<\/script>|<style[\s\S]*?<\/style>|<noscript[\s\S]*?<\/noscript>/gi, ' ')
    .replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim().length;
}

async function fetchPage(target, mode = 'auto') {
  const url = await assertPublicUrl(target);
  const out = { ok: true, url: url.href, finalUrl: url.href, status: null, html: '', reader: '', shopify: null, notes: [] };

  if (mode !== 'reader') {
    try {
      const r = await fetchText(url.href);
      out.status = r.status; out.finalUrl = r.url;
      if (r.status < 400) out.html = r.text; else out.notes.push(`Direct fetch returned HTTP ${r.status}`);
    } catch (e) { out.notes.push('Direct fetch failed: ' + e.message); }
  }

  const thin = !out.html || visibleTextLength(out.html) < 1500;
  if (mode === 'reader' || (mode === 'auto' && thin)) {
    // 1) rendered HTML via reader (keeps FAQ buttons, tables, alt texts) 2) markdown as last resort
    try {
      const r = await fetchText('https://r.jina.ai/' + url.href, 45000, { 'X-Return-Format': 'html' });
      if (r.status < 400 && visibleTextLength(r.text) > (out.html ? visibleTextLength(out.html) : 0) + 300) { out.html = r.text; out.notes.push('Used reader (rendered HTML) – page was JS-rendered, blocked or thin.'); }
    } catch (e) { out.notes.push('Reader (html) failed: ' + e.message); }
    if (!out.html || visibleTextLength(out.html) < 1500) {
      try {
        const r = await fetchText('https://r.jina.ai/' + url.href, 45000, { 'Accept': 'text/plain' });
        if (r.status < 400) { out.reader = r.text; out.notes.push('Used reader fallback (markdown).'); }
        else out.notes.push(`Reader returned HTTP ${r.status}`);
      } catch (e) { out.notes.push('Reader fallback failed: ' + e.message); }
    }
  }

  if (/\/products\/[^/?#]+/.test(url.pathname)) {
    try {
      const handlePath = url.pathname.match(/^(.*\/products\/[^/?#]+)/)[1];
      const r = await fetchText(url.origin + handlePath + '.js', 10000, { 'Accept': 'application/json' });
      if (r.status < 400) out.shopify = JSON.parse(r.text);
    } catch { /* not Shopify – ignore */ }
  }

  if (!out.html && !out.reader && !out.shopify) { out.ok = false; out.error = out.notes.join(' | ') || 'Nothing could be fetched'; }
  return out;
}

module.exports = { fetchPage };
