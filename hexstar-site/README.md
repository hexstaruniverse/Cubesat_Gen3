# Hexstar 1U CubeSat: product website

A single-page, scroll-driven 3D site. It's plain HTML, CSS and JavaScript with a small custom WebGL2 renderer, so there's no framework, no build step and no external libraries (only Google Fonts).

## Run it locally
Browsers block `fetch()` from `file://`, so serve the folder:

    cd hexstar-site
    python3 -m http.server 8000
    # open http://localhost:8000

Any static host works (Netlify, Vercel, GitHub Pages, cPanel, S3, ...). Upload the whole folder as is.

## Files
- `index.html`: the whole site (markup, styles, renderer, scroll choreography, dashboard).
- `assets/`
  - `*_F_color.jpg`, `*_F_orm.png`, `*_F_h.jpg` (and `*_B_*`): PCB textures rendered from your Gerbers (colour, roughness/metal/mask, height).
  - `boards.json`: 3D component bodies and hotspot data (names and descriptions) for each board.
  - `frame.json`: the CubeSat structure STL files, packed (int16, 0.01 mm).
  - `clouds.jpg`: cloud texture for the near-space Earth.
  - `logo.png`: the Hexstar logo with white text.
- `docs/`: datasheet PDFs linked from the Datasheets section.
- `tools/`: the Python scripts that generated the assets (Gerber rasteriser, component layout, datasheets). They need `numpy`, `opencv-python`, `openpyxl` and `reportlab`. Edit the input/output paths at the top of each script before running.

## Backend: payments, emails, admin panel, enquiries
Everything runs as small Vercel functions in `api/` (files starting with `_` are shared code, not URLs):
- `create-order.js`: validates the checkout form, prices it on the server, creates the Razorpay order and saves it.
- `verify.js`: checks the payment signature, marks the order paid and sends the two emails (customer + admin).
- `razorpay-webhook.js`: the same confirmation, sent by Razorpay itself, so an order is never missed if the customer closes the tab. Emails are sent only once per order.
- `inquiry.js`: the Enquiry form (name, email, phone, organisation, topic, message). Saves it, emails the admin and sends the customer a copy. Rate-limited, with a spam trap.
- `track.js`: counts visits by day, country and page. No IP addresses or cookies are stored.
- `admin.js` + `admin.html`: the admin panel at `/admin.html` (orders, visitors by country, enquiries, CSV export). Password protected.
- `geo.js`: the visitor's country, used to show ₹ or $.

Prices, the ₹2,000 booking and the rate (1 USD = 115 INR) are in `api/_shop.js`. Email wording is in `api/_orders.js` and `api/inquiry.js`; the email picture is `assets/email-cubesat.jpg`.

### One-time setup
1. **Database.** In Vercel open the project → Storage → Create → *Upstash for Redis* (free plan is fine) → connect it to this project. It adds `KV_REST_API_URL` and `KV_REST_API_TOKEN` automatically.
2. **Resend (email).** Sign up at resend.com → Domains → add your domain and add the DNS records it shows → API Keys → create one. Until the domain is verified, Resend only delivers to your own Resend account email.
3. **Razorpay webhook.** Razorpay dashboard → Settings → Webhooks → Add: URL `https://YOUR-SITE/api/razorpay-webhook`, events `payment.captured` and `order.paid`, and choose a secret.
4. **Environment variables** (Vercel → Settings → Environment Variables):

| Name | Value |
|---|---|
| `RAZORPAY_KEY_ID` | key id (`rzp_test_...` first, `rzp_live_...` later) |
| `RAZORPAY_KEY_SECRET` | the secret shown with that key id |
| `RAZORPAY_WEBHOOK_SECRET` | the secret you chose in step 3 |
| `RESEND_API_KEY` | `re_...` |
| `MAIL_FROM` | e.g. `Hexstar Universe <orders@yourdomain.com>` (verified domain) |
| `ADMIN_EMAIL` | where order and enquiry alerts go (comma-separate several) |
| `ADMIN_PASSWORD` | a long password for `/admin.html` |
| `SITE_URL` | optional, e.g. `https://hexstaruniverse.com` (used for email image links) |

5. Redeploy, then place a test order with a Razorpay test card and check both inboxes and `/admin.html`.

Never put keys in the code or in GitHub; only in Vercel's environment variables. Card, UPI and netbanking details are entered on Razorpay, never on this site. For USD payments, international payments must be enabled on your Razorpay account.

## Instagram reel ring
The "Follow the mission" section shows your reels on a 3D ring that rotates in a loop. Edit `INSTAGRAM` in `index.html`:
- `handle` / `profile`: your Instagram username and profile link.
- `reels`: one entry per reel. Each has `video` (a vertical, muted mp4 in `assets/reels/`, ideally 4 to 10 seconds and under 1 MB), `poster` (a still image), `url` (the reel's Instagram link), `caption` and an optional `views`.

The demo clips in `assets/reels/` are cut from the product video. Replace them with your own reels.

## Things to edit
- Prices, kit contents, Gen 1 / Gen 2 cards: the `#kits` section in `index.html`.
- Hotspot text: `HS` in `tools/comps.py` (then re-run it), or edit `assets/boards.json` directly.

## Hosting notes
The checkout needs the `api/` functions, so host on Vercel (or any platform that runs Node serverless functions). The datasheet buttons use the claude.ai artifact save prompt when that's available. On a normal website they open the PDF in a new tab. To force a download instead, add a `download` attribute to the `<a class="doc">` links.
