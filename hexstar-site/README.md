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

## Things to edit
- Pre-order / payment links: `PREORDER_LINKS` near the top of the main `<script>` in `index.html`.
- Prices, kit contents, Gen 1 / Gen 2 cards: the `#kits` section in `index.html`.
- Hotspot text: `HS` in `tools/comps.py` (then re-run it), or edit `assets/boards.json` directly.

## Hosting notes
The datasheet buttons use the claude.ai artifact save prompt when that's available. On a normal website they open the PDF in a new tab. To force a download instead, add a `download` attribute to the `<a class="doc">` links.
