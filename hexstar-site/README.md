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

## Pre-orders and payments (Razorpay)
`checkout.html` collects contact details, shipping and billing addresses, and optional business details (company name, GSTIN). It then opens Razorpay's secure checkout. Card, UPI and netbanking details are entered on Razorpay, never on this site.

The server side is three small Vercel functions in `api/`:
- `api/create-order.js`: validates the form, works out the price on the server, and creates a Razorpay order. Customer details are saved in the order's notes, so you'll see them in your Razorpay dashboard.
- `api/verify.js`: checks the Razorpay payment signature before showing the success screen.
- `api/geo.js`: returns the visitor's country, used to pick ₹ or $.

Prices, the ₹2,000 booking amount and the rate (1 USD = 115 INR) are set in `api/_shop.js`. Change them there and in the page text.

**Setup (one time):** in Vercel, open the project, go to Settings → Environment Variables, and add:
- `RAZORPAY_KEY_ID`: your key id (starts with `rzp_live_` or `rzp_test_`)
- `RAZORPAY_KEY_SECRET`: your key secret

Then redeploy. Use test keys first to try a payment, then switch to live keys. For USD payments, international payments must be enabled on your Razorpay account.

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
