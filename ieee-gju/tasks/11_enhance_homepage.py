"""Enhanced homepage — stronger visuals, fixed inline vars, enriched sections."""
import sys, base64
sys.path.insert(0, "/root/ieee-gju")
import wp_api
from config import SITE_URL, HOMEPAGE_ID

# ── Updated CSS additions (append to style.css for this push) ─────────────
with open("/root/ieee-gju/assets/style.css") as f:
    BASE_CSS = f.read()

EXTRA_CSS = """
/* ── Hero enhancements ──────────────────────────────────────────────────── */
.gju-hero::before {
  animation: gridPulse 8s ease-in-out infinite;
}
@keyframes gridPulse {
  0%, 100% { opacity: 0.6; }
  50%       { opacity: 1; }
}
.gju-hero-glow {
  position: absolute;
  width: 600px; height: 600px;
  background: radial-gradient(circle, rgba(0,48,135,0.35) 0%, transparent 70%);
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  pointer-events: none;
  animation: glowPulse 6s ease-in-out infinite;
}
@keyframes glowPulse {
  0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 0.8; }
  50%       { transform: translate(-50%, -50%) scale(1.15); opacity: 1; }
}
.gju-hero-badge {
  display: inline-flex; align-items: center; gap: 0.5rem;
  background: rgba(247,181,0,0.1);
  border: 1px solid rgba(247,181,0,0.3);
  border-radius: 100px;
  padding: 0.35rem 1rem;
  font-family: var(--font-mono); font-size: 0.65rem;
  color: var(--accent); letter-spacing: 0.12em; text-transform: uppercase;
  margin-bottom: 1.5rem;
}
.gju-hero-badge::before {
  content: ''; display: block;
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--accent);
  animation: blink 1.5s ease-in-out infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.2} }
.gju-hero h1 .line2 { color: var(--accent); display: block; }
.gju-scroll-hint {
  position: absolute; bottom: 2.5rem; left: 50%;
  transform: translateX(-50%);
  display: flex; flex-direction: column; align-items: center; gap: 0.4rem;
  font-family: var(--font-mono); font-size: 0.6rem; color: var(--accent);
  letter-spacing: 0.15em; text-transform: uppercase; opacity: 0.6;
}
.gju-scroll-hint span { animation: scrollBounce 1.8s ease-in-out infinite; }
@keyframes scrollBounce { 0%,100%{transform:translateY(0)} 50%{transform:translateY(6px)} }

/* ── Stats counter ──────────────────────────────────────────────────────── */
.gju-stat-card {
  background: rgba(247,181,0,0.04);
  border: 1px solid rgba(247,181,0,0.15);
  border-radius: 8px;
  padding: 1.5rem 2rem;
  min-width: 160px;
  transition: border-color 0.25s;
}
.gju-stat-card:hover { border-color: rgba(247,181,0,0.45); }

/* ── Gold divider ───────────────────────────────────────────────────────── */
.gju-gold-divider {
  width: 60px; height: 3px;
  background: linear-gradient(90deg, var(--accent), transparent);
  margin: 0.75rem 0 1.5rem;
  border: none;
}

/* ── Society card icon ring ─────────────────────────────────────────────── */
.gju-society-icon-ring {
  width: 48px; height: 48px;
  border-radius: 50%;
  background: rgba(247,181,0,0.08);
  border: 1px solid rgba(247,181,0,0.2);
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 1rem;
  font-size: 1.2rem;
}

/* ── Events banner ──────────────────────────────────────────────────────── */
.gju-events-banner {
  display: flex; align-items: center; justify-content: space-between;
  gap: 2rem;
  background: rgba(247,181,0,0.05);
  border: 1px solid rgba(247,181,0,0.2);
  border-radius: 10px;
  padding: 2rem 2.5rem;
  margin-top: 2.5rem;
  flex-wrap: wrap;
}
.gju-events-banner-text h3 {
  font-family: var(--font-display);
  font-size: 1.8rem; color: #fff; margin: 0 0 0.4rem; line-height: 1.1;
}
.gju-events-banner-text p {
  font-size: 0.875rem; color: #d0d6de; margin: 0;
}
.gju-events-banner-actions { display: flex; gap: 1rem; flex-wrap: wrap; }

/* ── News featured card ─────────────────────────────────────────────────── */
.gju-news-featured {
  display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-top: 2rem;
}
.gju-news-card-featured {
  background: #0d1a3a;
  border: 1px solid rgba(247,181,0,0.2);
  border-radius: 8px; padding: 2.5rem;
  display: flex; flex-direction: column; justify-content: flex-end;
  min-height: 280px;
  position: relative; overflow: hidden;
  transition: border-color 0.25s;
}
.gju-news-card-featured:hover { border-color: rgba(247,181,0,0.5); }
.gju-news-card-featured h3 {
  font-family: var(--font-display); font-size: 1.8rem;
  color: #fff; margin: 0.5rem 0 0.75rem; line-height: 1.1;
}
.gju-news-card-featured p { font-size: 0.875rem; color: #d0d6de; margin: 0 0 1.25rem; }
.gju-news-small-stack { display: flex; flex-direction: column; gap: 1rem; }
.gju-news-card-small {
  background: #0d1a3a;
  border: 1px solid rgba(247,181,0,0.15);
  border-radius: 8px; padding: 1.5rem;
  flex: 1;
  transition: border-color 0.25s;
}
.gju-news-card-small:hover { border-color: rgba(247,181,0,0.45); }
.gju-news-card-small h3 {
  font-family: var(--font-body); font-size: 0.95rem; font-weight: 600;
  color: #fff; margin: 0.4rem 0 0.5rem;
}
.gju-news-card-small p { font-size: 0.8rem; color: #d0d6de; margin: 0; }

/* ── Social connect strip ───────────────────────────────────────────────── */
.gju-social-strip {
  background: #0a0f1e;
  border-top: 1px solid rgba(247,181,0,0.2);
  padding: 4rem 2rem; text-align: center;
}
.gju-social-strip h2 {
  font-family: var(--font-display); font-size: clamp(2rem,5vw,3.5rem);
  color: #fff; margin: 0 0 0.5rem;
}
.gju-social-strip p { color: #d0d6de; font-size: 0.95rem; margin: 0 auto 2rem; max-width: 500px; }
.gju-social-links {
  display: flex; justify-content: center; gap: 1rem; flex-wrap: wrap;
}
.gju-social-link {
  display: flex; align-items: center; gap: 0.6rem;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 8px;
  padding: 0.75rem 1.25rem;
  color: #d0d6de !important;
  font-family: var(--font-mono); font-size: 0.75rem;
  text-transform: uppercase; letter-spacing: 0.08em;
  transition: all 0.25s;
  text-decoration: none !important;
}
.gju-social-link:hover {
  border-color: var(--accent);
  color: var(--accent) !important;
  background: rgba(247,181,0,0.06);
  opacity: 1 !important;
}

/* ── Responsive additions ───────────────────────────────────────────────── */
@media (max-width: 768px) {
  .gju-news-featured { grid-template-columns: 1fr; }
  .gju-events-banner { flex-direction: column; text-align: center; }
  .gju-events-banner-actions { justify-content: center; }
}
"""

FULL_CSS = BASE_CSS + "\n" + EXTRA_CSS
STYLE_BLOCK = f"<style>\n{FULL_CSS}\n</style>"
B64 = base64.b64encode(STYLE_BLOCK.encode()).decode()
VC = f"[vc_raw_html]{B64}[/vc_raw_html]"

# ── Enhanced homepage HTML ─────────────────────────────────────────────────
HOMEPAGE_HTML = """
<!-- HERO -->
<section class="gju-hero">
  <div class="gju-hero-glow"></div>
  <div class="gju-hero-content">
    <div class="gju-hero-badge">IEEE Student Branch &mdash; Est. GJU, Madaba</div>
    <h1>ENGINEERING<span class="line2">TOMORROW</span></h1>
    <p class="gju-hero-sub">Connecting engineers, fostering innovation, and building the next generation of technical leaders at German Jordanian University.</p>
    <div>
      <a href="/jo-gju/communities/" class="gju-btn gju-btn-primary">Explore Communities</a>
      <a href="/jo-gju/events/" class="gju-btn gju-btn-ghost">Upcoming Events</a>
    </div>
  </div>
  <div class="gju-scroll-hint">
    <span>&#8595;</span>
    Scroll
  </div>
</section>

<!-- ABOUT STRIP -->
<div style="background:#0d1a3a;border-top:1px solid rgba(247,181,0,0.2);border-bottom:1px solid rgba(247,181,0,0.2);">
<div class="gju-about-strip">
  <blockquote>"IEEE's mission is to foster technological innovation and excellence for the benefit of humanity."</blockquote>
  <div class="gju-stats">
    <div class="gju-stat-card">
      <span class="gju-stat-number">11</span>
      <span class="gju-stat-label">Active Societies</span>
    </div>
    <div class="gju-stat-card">
      <span class="gju-stat-number">400K+</span>
      <span class="gju-stat-label">IEEE Members Worldwide</span>
    </div>
    <div class="gju-stat-card">
      <span class="gju-stat-number">160+</span>
      <span class="gju-stat-label">Countries Represented</span>
    </div>
  </div>
</div>
</div>

<!-- COMMUNITIES -->
<div style="background:#0a0f1e;">
<div class="gju-section">
  <span class="gju-section-label">Our Communities</span>
  <h2 class="gju-section-title">Find Your Society</h2>
  <hr class="gju-gold-divider">
  <div class="gju-communities-grid">
    <a href="/jo-gju/communities/computer-society-cs/" class="gju-society-card">
      <div class="gju-society-icon-ring">&#128187;</div>
      <span class="gju-society-abbr">CS</span>
      <span class="gju-society-name">Computer Society</span>
      <span class="gju-society-desc">Cutting-edge software development, AI, cybersecurity, and more.</span>
    </a>
    <a href="/jo-gju/communities/industrial-electronics-society-ies/" class="gju-society-card">
      <div class="gju-society-icon-ring">&#9889;</div>
      <span class="gju-society-abbr">IES</span>
      <span class="gju-society-name">Industrial Electronics Society</span>
      <span class="gju-society-desc">Practical applications of electrical engineering across industries.</span>
    </a>
    <a href="/jo-gju/communities/engineering-in-medicine-and-biology-society-embs/" class="gju-society-card">
      <div class="gju-society-icon-ring">&#10084;</div>
      <span class="gju-society-abbr">EMBS</span>
      <span class="gju-society-name">Engineering in Medicine &amp; Biology</span>
      <span class="gju-society-desc">Where engineering meets healthcare to advance medical science.</span>
    </a>
    <a href="/jo-gju/communities/women-in-engineering-wie/" class="gju-society-card">
      <div class="gju-society-icon-ring">&#11088;</div>
      <span class="gju-society-abbr">WIE</span>
      <span class="gju-society-name">Women in Engineering</span>
      <span class="gju-society-desc">Diversity, inclusion, empowerment, and mentorship in engineering.</span>
    </a>
    <a href="/jo-gju/communities/industry-applications-societyias/" class="gju-society-card">
      <div class="gju-society-icon-ring">&#127981;</div>
      <span class="gju-society-abbr">IAS</span>
      <span class="gju-society-name">Industry Applications Society</span>
      <span class="gju-society-desc">At the intersection of theory and practice for engineers and academics.</span>
    </a>
    <a href="/jo-gju/communities/robotics-and-automation-society-ras/" class="gju-society-card">
      <div class="gju-society-icon-ring">&#129302;</div>
      <span class="gju-society-abbr">RAS</span>
      <span class="gju-society-name">Robotics &amp; Automation Society</span>
      <span class="gju-society-desc">Advancing theory and practice in robotics and automation.</span>
    </a>
    <a href="/jo-gju/communities/consumer-technology-society-ctsoc/" class="gju-society-card">
      <div class="gju-society-icon-ring">&#128241;</div>
      <span class="gju-society-abbr">CTSoc</span>
      <span class="gju-society-name">Consumer Technology Society</span>
      <span class="gju-society-desc">Innovating consumer technologies through conferences and publications.</span>
    </a>
    <a href="/jo-gju/communities/power-energy-society-pes/" class="gju-society-card">
      <div class="gju-society-icon-ring">&#128161;</div>
      <span class="gju-society-abbr">PES</span>
      <span class="gju-society-name">Power &amp; Energy Society</span>
      <span class="gju-society-desc">Scientific and engineering information on electric power and energy.</span>
    </a>
    <a href="/jo-gju/communities/tems/" class="gju-society-card">
      <div class="gju-society-icon-ring">&#128200;</div>
      <span class="gju-society-abbr">TEMS</span>
      <span class="gju-society-name">Technology &amp; Engineering Management</span>
      <span class="gju-society-desc">Bridging academia, industry, and government.</span>
    </a>
    <a href="/jo-gju/communities/aess/" class="gju-society-card">
      <div class="gju-society-icon-ring">&#9992;</div>
      <span class="gju-society-abbr">AESS</span>
      <span class="gju-society-name">Aerospace &amp; Electronic Systems</span>
      <span class="gju-society-desc">Advancing systems engineering in aerospace, radar, navigation, and avionics.</span>
    </a>
    <a href="/jo-gju/communities/sight/" class="gju-society-card">
      <div class="gju-society-icon-ring">&#127758;</div>
      <span class="gju-society-abbr">SIGHT</span>
      <span class="gju-society-name">Humanitarian Technology</span>
      <span class="gju-society-desc">Leveraging technology for sustainable development in underserved communities.</span>
    </a>
  </div>
</div>
</div>

<!-- UPCOMING EVENTS -->
<div style="background:#0d1a3a;border-top:1px solid rgba(247,181,0,0.2);border-bottom:1px solid rgba(247,181,0,0.2);">
<div class="gju-section">
  <span class="gju-section-label">What's Happening</span>
  <h2 class="gju-section-title">Upcoming Events</h2>
  <hr class="gju-gold-divider">
  <div class="gju-events-banner">
    <div class="gju-events-banner-text">
      <h3>IEEE Jordan Section Events</h3>
      <p>Browse workshops, seminars, competitions and networking events from the IEEE Jordan Section and all GJU societies.</p>
    </div>
    <div class="gju-events-banner-actions">
      <a href="https://events.vtools.ieee.org/events/list?filter_organization=all&filter_country=JO" target="_blank" class="gju-btn gju-btn-primary">Browse Events &rarr;</a>
      <a href="/jo-gju/events/" class="gju-btn gju-btn-ghost">Events Page</a>
    </div>
  </div>
</div>
</div>

<!-- NEWS -->
<div style="background:#0a0f1e;">
<div class="gju-section">
  <span class="gju-section-label">Latest Updates</span>
  <h2 class="gju-section-title">News &amp; Announcements</h2>
  <hr class="gju-gold-divider">
  <div class="gju-news-featured">
    <div class="gju-news-card-featured">
      <span class="gju-category-tag">Announcement</span>
      <h3>Welcome to the New IEEE GJU Website</h3>
      <p>We've launched our fully redesigned site. Explore our 11 active societies, find upcoming events, and connect with the community.</p>
      <a href="/jo-gju/news/" class="gju-btn gju-btn-primary" style="align-self:flex-start">Read More &rarr;</a>
    </div>
    <div class="gju-news-small-stack">
      <div class="gju-news-card-small">
        <span class="gju-category-tag">Society News</span>
        <h3>Explore Our 11 Active Societies</h3>
        <p>From Robotics to Humanitarian Tech — find the society that matches your passion.</p>
      </div>
      <div class="gju-news-card-small">
        <span class="gju-category-tag">Events</span>
        <h3>IEEE Jordan Events Now Listed</h3>
        <p>Check the latest workshops and seminars from IEEE Jordan Section on our Events page.</p>
      </div>
    </div>
  </div>
  <div class="gju-cta-row"><a href="/jo-gju/news/" class="gju-btn gju-btn-ghost">View All News &rarr;</a></div>
</div>
</div>

<!-- HOW TO JOIN -->
<div style="background:#0d1a3a;border-top:1px solid rgba(247,181,0,0.2);">
<div class="gju-section" style="text-align:center;">
  <span class="gju-section-label">Get Involved</span>
  <h2 class="gju-section-title">How to Join IEEE</h2>
  <hr class="gju-gold-divider" style="margin:0.75rem auto 2rem;">
  <div class="gju-join-steps">
    <div class="gju-step-card">
      <span class="gju-step-number">01</span>
      <div class="gju-step-title">Discover</div>
      <p class="gju-step-desc">Explore our 11 active societies and find the one that matches your passion in engineering and technology.</p>
    </div>
    <div class="gju-step-card">
      <span class="gju-step-number">02</span>
      <div class="gju-step-title">Apply</div>
      <p class="gju-step-desc">Complete your IEEE membership application online. Student membership is available at a significantly discounted rate.</p>
    </div>
    <div class="gju-step-card">
      <span class="gju-step-number">03</span>
      <div class="gju-step-title">Connect</div>
      <p class="gju-step-desc">Attend events, join society groups, collaborate on projects, and grow your professional network globally.</p>
    </div>
  </div>
  <div class="gju-cta-row" style="margin-top:2.5rem;">
    <a href="https://www.ieee.org/membership/join/index.html" target="_blank" class="gju-btn gju-btn-primary">Join IEEE Now &rarr;</a>
  </div>
</div>
</div>

<!-- SOCIAL CONNECT -->
<div class="gju-social-strip">
  <h2>Stay Connected</h2>
  <p>Follow us for the latest news, event announcements, and community highlights.</p>
  <div class="gju-social-links">
    <a href="https://www.instagram.com/ieeegju/" target="_blank" class="gju-social-link">&#128247; Instagram</a>
    <a href="https://www.linkedin.com/company/ieee-gju" target="_blank" class="gju-social-link">&#128101; LinkedIn</a>
    <a href="https://events.vtools.ieee.org/events/list?filter_organization=all&filter_country=JO" target="_blank" class="gju-social-link">&#128197; IEEE Events</a>
    <a href="https://ieee.org" target="_blank" class="gju-social-link">&#127760; IEEE.org</a>
  </div>
</div>
"""

if __name__ == "__main__":
    # Backup current
    current = wp_api.get(f"/pages/{HOMEPAGE_ID}", params={"context": "edit"})
    raw = current["content"].get("raw", "")
    wp_api.log_undo(
        "homepage enhancement v2",
        "PUT",
        f"{SITE_URL}/wp-json/wp/v2/pages/{HOMEPAGE_ID}",
        {"content": raw, "status": current["status"]}
    )

    new_content = VC + "\n\n" + HOMEPAGE_HTML.strip()
    result = wp_api.put(f"/pages/{HOMEPAGE_ID}", {
        "content": new_content,
        "status": "publish"
    })
    print(f"Homepage enhanced: {result.get('link')}")
    print(f"Content size: {len(new_content):,} chars | CSS: {len(FULL_CSS):,} chars")
