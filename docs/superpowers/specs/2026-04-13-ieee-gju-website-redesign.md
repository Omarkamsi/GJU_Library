# IEEE GJU Website Redesign — Design Spec
**Date:** 2026-04-13
**Site:** https://edu.ieee.org/jo-gju/
**Platform:** WordPress (hosted on IEEE edu platform)
**Delivery Method:** WordPress REST API with full undo logging

---

## 1. Project Overview

A comprehensive redesign and content expansion of the IEEE GJU (German Jordanian University) student branch website. The goal is to modernize the visual identity, expand content coverage (events, news, societies), and improve student engagement through better contact and community discovery.

---

## 2. Undo & Safety Strategy

Every change made via the REST API is reversible. The following safeguards apply before any modification:

- **CSS changes:** Existing custom CSS is saved to `undo-log/original-css.txt` before overwriting. Revert = one API call.
- **Page edits:** Existing page content is saved to `undo-log/pages/<slug>.json` before modification. Revert = one API call.
- **New pages:** Created as **Drafts** first. Only published after explicit approval. Deleting a draft = zero visible impact.
- **Menu changes:** Current menu structure saved to `undo-log/menus.json` before modification. Revert = one API call.
- **Undo log:** All changes recorded in `undo-log/undo-log.json` with timestamp, resource type, resource ID, and reversal payload.

---

## 3. Visual Design System

### Color Palette
| Role | Value |
|---|---|
| Background | `#0a0f1e` (near-black navy) |
| Primary | `#003087` (IEEE dark blue) |
| Accent | `#f7b500` (IEEE gold) |
| Surface (cards/panels) | `#0d1a3a` |
| Text primary | `#e8edf5` |
| Text muted | `#8da0bb` |

### Typography
| Role | Font |
|---|---|
| Display / Headings | Bebas Neue |
| Body | DM Sans |
| Accent labels / dates | JetBrains Mono |

### Visual Details
- Subtle circuit-board grid texture on hero background
- Gold horizontal rule lines as section dividers
- Cards: dark surface + gold left border on hover
- Glowing gold underline on active nav items
- Gold focus rings on all form inputs

---

## 4. Navigation Menu

```
Home
Communities  ▾
  ├── Computer Society (CS)
  ├── Industrial Electronics (IES)
  ├── Engineering in Medicine & Biology (EMBS)
  ├── Women in Engineering (WIE)
  ├── Industry Applications (IAS)
  ├── Robotics & Automation (RAS)
  ├── Consumer Technology (CTSoc)
  ├── Power & Energy (PES)
  ├── Technology & Engineering Management (TEMS)
  ├── Aerospace & Electronic Systems (AESS)
  └── SIGHT (Humanitarian Technology)
Events
News & Announcements
How to Join
Contact Us
```

**Behavior:**
- Sticky header — visible while scrolling
- Communities dropdown: dark surface background, gold left border per item on hover
- Active page: gold underline indicator
- Mobile: hamburger menu collapse

---

## 5. Homepage Sections

### 5.1 Hero
- Full-viewport, dark background with circuit-board texture overlay
- Headline: **"ENGINEERING TOMORROW"** (Bebas Neue, large)
- Subline: *"IEEE Student Branch — German Jordanian University"*
- Two CTAs: `Explore Communities` (gold filled) + `Upcoming Events` (ghost/outline)

### 5.2 About Strip
- Full-width narrow band
- IEEE mission statement (large italic DM Sans)
- Two stat counters: *"11 Active Societies"* and *"IEEE — 400,000+ Members Worldwide"*
- Gold divider lines top and bottom

### 5.3 Communities Grid
- 3×4 card grid (11 societies)
- Each card: society abbreviation in Bebas Neue (gold, large), full name, one-line description
- Hover: gold left border + subtle glow
- Links to individual society sub-pages

### 5.4 Upcoming Events
- 3-column card row
- Source: vtools IEEE Jordan feed (embedded or manually maintained)
- Card: title, date (JetBrains Mono), location tag, short description
- CTA: "View All Events"

### 5.5 News & Announcements
- 2-column: featured post (large, left) + 2 smaller posts stacked (right)
- Timestamp in gold monospace
- CTA: "View All News"

### 5.6 How to Join
- 3-step horizontal flow: **Discover → Apply → Connect**
- Each step: dark surface card, gold step number, short description
- CTA: `Join IEEE Now` → links to IEEE global membership page

### 5.7 Footer
- Left: IEEE GJU logo + tagline
- Center: Quick nav links
- Right: Social icons (Instagram, LinkedIn, WhatsApp, Email)
- Bottom bar: copyright + link to ieee.org

---

## 6. Events Page

### Layout
- Sticky filter bar + 2-column masonry card grid

### Filters
- Time: `All` `This Week` `This Month`
- Type: `Workshop` `Seminar` `Competition` `Networking`
- Active filter: gold highlight; inactive: dark surface pill

### Event Card
- Date: day (large JetBrains Mono) + month (small above)
- Gold type tag
- Title, location, short description
- `Register →` button linking to vtools event page

### Data Source
- Primary: manually maintained WordPress posts synced from `events.vtools.ieee.org` (Jordan Section)
- Fallback: embedded vtools widget

### Empty State
- Centered message: *"No upcoming events. Check back soon."*
- Link to full IEEE Jordan events calendar

---

## 7. Contact Page

### Layout
Two-column split:
- Left (40%): Contact info + society contacts accordion
- Right (60%): Contact form

### Left Column — Reach Us
- Email (placeholder)
- WhatsApp group link (placeholder)
- Instagram: @ieeegju
- LinkedIn: IEEE GJU (placeholder link)

### Left Column — Society Contacts
Expandable accordion, one open at a time. 11 societies listed:
- CS, IES, EMBS, WIE, IAS, RAS, CTSoc, PES, TEMS, AESS, SIGHT
- Each entry: Contact Person (placeholder), Email (placeholder), WhatsApp (placeholder)

### Right Column — Contact Form
Fields:
- Full Name
- Email Address
- Subject (dropdown): General Inquiry / Join a Society / Event Question / Partnership / Other
- Message (textarea)
- `Send Message` CTA (gold filled)

Success state: animated gold checkmark + *"We'll get back to you soon."*

### Map Strip
Below both columns — embedded Google Map showing GJU campus (Madaba, Jordan).

---

## 8. News & Announcements Page

### Layout
- Featured post hero (top, full-width)
- Paginated post list below (6 per page)
- Sidebar (desktop): search, filter by category, recent posts, link to Events

### Featured Post Hero
- Background image or gradient fallback
- Title (Bebas Neue, large), gold category tag, date (JetBrains Mono), excerpt
- `Read More →` CTA

### Post Card
- Thumbnail image
- Date, category tag, title (DM Sans Bold), excerpt
- `Read More →` link

### Categories
`Announcement` `Achievement` `Workshop Recap` `Society News`

### Individual Post
- Wide centered reading column
- Title, author + date (monospace), body (DM Sans)
- Social share buttons at bottom

---

## 9. Societies Descriptions

| Society | Abbreviation | Description |
|---|---|---|
| Computer Society | CS | Cutting-edge software development, AI, cybersecurity, and more. |
| Industrial Electronics Society | IES | Practical applications of electrical engineering across industries. |
| Engineering in Medicine & Biology | EMBS | Where engineering meets healthcare to advance medical science. |
| Women in Engineering | WIE | Diversity, inclusion, empowerment and mentorship in engineering. |
| Industry Applications Society | IAS | At the intersection of theory and practice for engineers and academics. |
| Robotics & Automation Society | RAS | Advancing theory and practice in robotics and automation. |
| Consumer Technology Society | CTSoc | Innovating consumer technologies through conferences and publications. |
| Power & Energy Society | PES | Scientific and engineering information on electric power and energy. |
| Technology & Engineering Management | TEMS | Bridging academia, industry, and government. |
| Aerospace & Electronic Systems | AESS | Advancing systems engineering in aerospace, radar, navigation, and avionics. |
| SIGHT | SIGHT | Leveraging technology for sustainable development in underserved communities. |

---

## 10. Implementation Notes

- All new pages created as WordPress Posts/Pages via REST API
- Custom CSS injected via `/wp/v2/settings` (additional_css) or theme customizer endpoint
- Nav menus managed via `/wp/v2/menus` (if WP-REST-API-Menus plugin active) or fallback to manual
- Events page: WordPress custom post type `event` or standard posts with `Events` category
- Contact form: WPForms or Contact Form 7 (whichever is already installed on the site)
- Google Fonts (Bebas Neue, DM Sans, JetBrains Mono) loaded via `wp_enqueue_style` or injected CSS `@import`
- All placeholder contact info marked with `[PLACEHOLDER]` tag for easy find-and-replace later
