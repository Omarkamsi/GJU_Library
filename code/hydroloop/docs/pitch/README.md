# HydroLoop Pitch Deck

Single-file HTML pitch deck. No build step, no dependencies.

## View

```bash
# Open directly in your browser
open docs/pitch/index.html        # macOS
xdg-open docs/pitch/index.html    # Linux
start docs/pitch/index.html       # Windows
```

Or serve from the repo root:
```bash
python3 -m http.server 8002
# → http://localhost:8002/docs/pitch/
```

## Navigate

| Key                | Action               |
|--------------------|----------------------|
| → / Space / PgDn   | Next slide           |
| ← / PgUp           | Previous slide       |
| Home / End         | Jump to first/last   |
| Click dots         | Jump to slide        |

## Slides

1. **Title** — Brand, tagline, badges
2. **The Problem** — 3 stats (Jordan #2 water-stressed, 0 buildings monitored, 0 W measured)
3. **The Solution** — Two layers + public dashboard architecture
4. **Live demo** — Three big tiles (kWh/L/devices online) + repo URL
5. **Why HydroLoop wins** — 4 differentiators

## Export to PDF

Print from Chrome / Edge / Safari → Save as PDF. CSS includes
`@page` rules so each slide becomes a 1280×720 page.

```bash
# Headless, if you have Chrome installed:
google-chrome --headless --disable-gpu \
  --print-to-pdf=hydroloop-pitch.pdf \
  --print-to-pdf-no-header \
  file:///$(pwd)/docs/pitch/index.html
```

## Edit

The deck is one `index.html` file plus `gju-logo.png`. Tweak the
inline `<style>` block for colors/fonts; edit slide content
directly in the `<section class="slide">` blocks.

To match the live dashboard later, replace the hard-coded numbers
on slide 4 with values fetched from `/api/summary`.
