# Landing Kit Generator

Paste a competitor product page link and get everything you need to build a new landing page in **your** template (vital-konzept.ch structure):

| Output tab | What it is |
|---|---|
| ⭐ **Master prompt** | Everything in one block. Paste it into a **new** AI chat (ChatGPT, Claude, Gemini …). It works without any earlier context. |
| Brief | Product facts, angles, FAQ, testimonials, ⚠️ risky claims, image plan, competitor images, open questions |
| Copy template | Every text slot of the template (hero, S1–S5, reviews, FAQ, packages …) with word limits and rules |
| Image prompts | Packaging reference → main/hero composite → before/after → mechanics → steps → doctor → testimonial → closing → bundles → sticky → review photos |
| Checklist | Intake, copy, compliance (Meta + UWG/HMG), images, template leftovers, checkout, QA |
| Competitor images | All images found on the page. Mark which one is the main / before-after / doctor … with the dropdowns |

Every tab has **Copy**, **Download .md** and **Download all**.

---

## How to use (daily workflow)

1. Paste the **competitor URL** and enter **your product name** (e.g. `Erovyn™`).
2. Optional but recommended: describe your **packaging** and the **text on the pack**.
   Check the auto-detected **Product category** (dental, joints/pain, skin, hair, weight, sleep, feet, men's intimacy, other). It controls the scenes, the expert (dentist, orthopaedist, urologist …), the FAQ examples and the target group. Fix it in the dropdown if it's wrong.
3. Click **Analyze competitor & generate kit** (takes 2–25 seconds).
4. Open **Competitor images** and spend 30 seconds on the dropdowns. Mark the competitor's Main, Before & after, Mechanics, Steps, Doctor, Testimonial and Product images. Many pages use meaningless file names (`me03.webp`), so the auto-guess is only a hint.
5. Open **⭐ Master prompt** → **Copy** → paste it into a new chat. The AI returns brief questions, the full copy, final image prompts and your checklist actions.

Your store settings (template URL, domain, email, language, prices, stock, old product names to search for) are saved in your browser. Set them once under **Store & template settings**.

### Works with any competitor page
- Advertorials and Funnelish/ClickFunnels pages (no headings needed: it reads the text around each image)
- Shopify product pages (also reads the hidden Shopify product JSON: title, variants, prices, all product images)
- WordPress / WooCommerce, custom pages and JavaScript-heavy pages (via the reader fallback)
- Any language: EN, DE, FR, IT, ES, PL, NL … are detected. The output language is set separately (default Swiss High German).
- Competitor sloppiness is handled: leftovers from THEIR old product (e.g. "5x DermoPur™ $129" on an Affinera page), blocks in another language, countdown digits and table separators are ignored. FAQ accordions and comparison tables are read properly.

### If a page can't be fetched
Fetching tries these ways automatically: **server** → **reader as rendered HTML** → **reader as text** → **manual**. On static hosting the reader's HTML mode gives the same quality as the server.
If all fail (login walls, heavy bot protection), open **Fallbacks**:
- **Page text**: on the competitor page press Ctrl+A, Ctrl+C, then paste here.
- **Image URLs**: right-click an image → "Copy image address", one URL per line.

Then click Analyze again. Manual mode works without any URL.

---

## Deploy (pick one)

### Option A — Vercel (recommended, free)
The server function may take up to 60 s, which is enough for slow pages.
1. Create a free account at vercel.com.
2. Either:
   - **Without Git:** install the CLI (`npm i -g vercel`), then in this folder run `vercel` and then `vercel --prod`.
   - **With GitHub:** push this folder to a repo, then in Vercel choose *Add New → Project → Import*. Leave all settings as they are; `vercel.json` already sets `public/` as the output and `api/fetch.js` as the function.
3. Done: `https://your-project.vercel.app`.

### Option B — Netlify (free)
1. Push the folder to GitHub, then in Netlify choose *Add new site → Import from Git*. Or use the CLI: `npm i -g netlify-cli`, then `netlify deploy --prod`.
2. `netlify.toml` already sets `public/` as the site and `/api/fetch` → `netlify/functions/fetch.js`.
3. Note: Netlify functions have a **10 s limit** on the free plan. For slow pages, the app automatically switches to the browser reader fallback, so it still works.
4. ⚠️ Netlify **drag & drop** only uploads static files (no function). That is fine too, see Option C.

### Option C — Static only (Netlify Drop, Cloudflare Pages, GitHub Pages, any web host)
Upload only the **`public/`** folder (it's one `index.html`). There is no server function. The page calls the reader (r.jina.ai) directly from the browser, and manual paste always works. That is enough for most competitor pages.
- Netlify Drop: go to app.netlify.com/drop and drag the `public` folder onto it.

### Option D — Your own server / VPS / local PC
Needs Node.js 18 or newer and no `npm install` (there are no dependencies).
```bash
node server.js            # http://localhost:3000
PORT=8080 node server.js  # other port
```

---

## Customise
- **Defaults** (template URL, domain, e-mail, prices, colours, review count …): edit the `DEFAULTS` object at the top of the `<script>` in `public/index.html`. You can also just change the settings in the UI; they are saved per browser.
- **Section → image order**: editable in the UI (Store & template settings → "Section → image order"), for when you change the template.
- **Fixed template strings** (countdown text, "50 % Rabatt endet um 23:59 Uhr", FAQ questions, section topics): search for `SECTION_TOPIC` / `buildCopy` in `public/index.html`.

## Files
```
public/index.html            whole app (UI + parsing + output builders), works standalone
lib/fetchCore.js             shared page fetcher (Chrome UA, SSRF guard, 4 MB cap, reader fallback, Shopify JSON)
server.js                    local / VPS server (static + /api/fetch)
api/fetch.js                 Vercel serverless function
netlify/functions/fetch.js   Netlify function
vercel.json / netlify.toml   deploy configs
```

## Safety notes
- The fetcher only allows public http(s) URLs (private/internal IPs are blocked) and caps pages at 4 MB.
- The reader fallback sends the competitor URL (never your data) to r.jina.ai.
- The kit flags risky claims (cm/%, studies, "clinically proven", doctors, time promises, cure/heal …). Copy the competitor's **angles**, not their claims (Meta ad policy, Swiss UWG/HMG).
