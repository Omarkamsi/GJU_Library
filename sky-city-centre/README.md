# Sky City Centre — Website

Luxurious, high-converting single-page site for **Sky City Centre Physical Therapy & Rehabilitation** (سما العاصمة للعلاج الطبيعي), Amman, Jordan.

## What's here

- `index.html` — self-contained single-page site. No build step, no dependencies beyond CDN-loaded Tailwind and Google Fonts.

## Preview

Open `index.html` in any modern browser. That's it.

```bash
# Optional: serve locally with Python for proper fetching
python3 -m http.server 8000
# then open http://localhost:8000
```

## Features

- **Bilingual (English ↔ Arabic)** with RTL support. Toggle in the top-right of the nav. Preference is saved to localStorage.
- **Single long-form landing page** optimized for conversion: hero → services → pillars → signature patient story → reviews → how-it-works → location → final CTA.
- **Fully responsive** (mobile-first, tested at 375/768/1024/1440).
- **Accessible**: semantic HTML, 4.5:1+ contrast, visible focus rings, `aria-pressed` on toggle, reduced-motion support.
- **Luxury visual system**: deep teal + ivory + gold palette, Fraunces display + Inter body, IBM Plex Sans Arabic for Arabic.
- **Scroll-reveal animations** (disabled if `prefers-reduced-motion`).
- **Real content** pulled from the owner's Google listing and verified 5.0★ reviews.

## How to customize

### Contact info
Search `index.html` for these and replace:
- Phone: `+962777900130` / `07 7790 0130`
- Website: `besmartjo.com`
- Address: "Jumeian Building, 2nd Floor..." / "عمارة جميعان..."

### Photos
Hero, story section, and location use Unsplash placeholders. Replace the URLs:
- Hero bg: search for `photo-1576091160550-2173dba999ef`
- Story bg: search for `photo-1559757175-5700dde675bc`
- Location image: search for `photo-1629909613654-28e377c37b09`

Drop in your own photos (treatment rooms, team, patients with consent).

### Colors
Defined in `<script>tailwind.config</script>` and in the CSS `:root` variables at the top of the `<style>` block:
- `--teal-deep: #0B3B3C`
- `--gold: #C9A86A`
- `--ivory: #F7F3EC`

### Copy
All user-facing text is duplicated in `data-en` and `data-ar` attributes. Edit both to keep translations in sync.

### Reviews
Three real reviews are hardcoded. To add/change, find the `review-card` articles in the `#reviews` section.

## Deployment

**Drag-and-drop (easiest):**
- Netlify Drop: https://app.netlify.com/drop
- Vercel: `vercel deploy`
- Cloudflare Pages: upload via dashboard

**Static hosting:** works on any server. Just upload `index.html`.

## Design decisions

- **Why single page?** Higher conversion for local service businesses. Visitors scan → trust → call. Multi-page adds friction.
- **Why teal + gold?** Teal reads as *clinical trust*; gold elevates it to *premium care*. Together they avoid both sterile-medical and spa-fluffy.
- **Why Fraunces?** Warm, editorial serif — feels human and premium without being corporate. Pairs naturally with clean sans body.
- **Why the story section?** The wheelchair-to-walking story from the owner's own post is the most powerful proof point available. It's positioned right before reviews for maximum emotional impact.
- **Why 24/7 messaging?** It's a genuine differentiator in Amman and the owner emphasized it. It reinforces both *convenience* and *commitment*.

## Next steps (optional)

- Replace stock photography with real clinic photos (permission-cleared)
- Add a Google Maps embed in the Visit section
- Add a contact form (requires a backend or form service like Formspree)
- Add structured data (Schema.org `MedicalBusiness`) for SEO
- Set up Google Analytics / Meta Pixel for tracking
