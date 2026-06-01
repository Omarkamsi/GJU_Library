# /root/ieee-gju/tasks/05_homepage.py
import sys
sys.path.insert(0, "/root/ieee-gju")
import wp_api
from config import SITE_URL, HOMEPAGE_ID

with open("/root/ieee-gju/assets/style.css") as f:
    CSS = f.read()
CSS_BLOCK = f"<style>\n{CSS}\n</style>"

HOMEPAGE_HTML = CSS_BLOCK + """

<!-- HERO -->
<section class="gju-hero">
  <div class="gju-hero-content">
    <span class="gju-hero-eyebrow">IEEE Student Branch &middot; German Jordanian University</span>
    <h1>ENGINEERING<br><span class="accent">TOMORROW</span></h1>
    <p class="gju-hero-sub">Connecting engineers, fostering innovation, and building the technical community at GJU.</p>
    <div>
      <a href="/jo-gju/communities/" class="gju-btn gju-btn-primary">Explore Communities</a>
      <a href="/jo-gju/events/" class="gju-btn gju-btn-ghost">Upcoming Events</a>
    </div>
  </div>
</section>

<!-- ABOUT STRIP -->
<div class="gju-about-strip">
  <blockquote>"IEEE's mission is to foster technological innovation and excellence for the benefit of humanity."</blockquote>
  <div class="gju-stats">
    <div><span class="gju-stat-number">11</span><span class="gju-stat-label">Active Societies</span></div>
    <div><span class="gju-stat-number">400K+</span><span class="gju-stat-label">IEEE Members Worldwide</span></div>
    <div><span class="gju-stat-number">160+</span><span class="gju-stat-label">Countries Represented</span></div>
  </div>
</div>

<!-- COMMUNITIES -->
<div style="background:var(--bg);">
<div class="gju-section">
  <span class="gju-section-label">Our Communities</span>
  <h2 class="gju-section-title">Find Your Society</h2>
  <div class="gju-communities-grid">
    <a href="/jo-gju/communities/computer-society-cs/" class="gju-society-card">
      <span class="gju-society-abbr">CS</span>
      <span class="gju-society-name">Computer Society</span>
      <span class="gju-society-desc">Cutting-edge software development, AI, cybersecurity, and more.</span>
    </a>
    <a href="/jo-gju/communities/industrial-electronics-society-ies/" class="gju-society-card">
      <span class="gju-society-abbr">IES</span>
      <span class="gju-society-name">Industrial Electronics Society</span>
      <span class="gju-society-desc">Practical applications of electrical engineering across industries.</span>
    </a>
    <a href="/jo-gju/communities/engineering-in-medicine-and-biology-society-embs/" class="gju-society-card">
      <span class="gju-society-abbr">EMBS</span>
      <span class="gju-society-name">Engineering in Medicine &amp; Biology</span>
      <span class="gju-society-desc">Where engineering meets healthcare to advance medical science.</span>
    </a>
    <a href="/jo-gju/communities/women-in-engineering-wie/" class="gju-society-card">
      <span class="gju-society-abbr">WIE</span>
      <span class="gju-society-name">Women in Engineering</span>
      <span class="gju-society-desc">Diversity, inclusion, empowerment, and mentorship in engineering.</span>
    </a>
    <a href="/jo-gju/communities/industry-applications-societyias/" class="gju-society-card">
      <span class="gju-society-abbr">IAS</span>
      <span class="gju-society-name">Industry Applications Society</span>
      <span class="gju-society-desc">At the intersection of theory and practice for engineers and academics.</span>
    </a>
    <a href="/jo-gju/communities/robotics-and-automation-society-ras/" class="gju-society-card">
      <span class="gju-society-abbr">RAS</span>
      <span class="gju-society-name">Robotics &amp; Automation Society</span>
      <span class="gju-society-desc">Advancing theory and practice in robotics and automation.</span>
    </a>
    <a href="/jo-gju/communities/consumer-technology-society-ctsoc/" class="gju-society-card">
      <span class="gju-society-abbr">CTSoc</span>
      <span class="gju-society-name">Consumer Technology Society</span>
      <span class="gju-society-desc">Innovating consumer technologies through conferences and publications.</span>
    </a>
    <a href="/jo-gju/communities/power-energy-society-pes/" class="gju-society-card">
      <span class="gju-society-abbr">PES</span>
      <span class="gju-society-name">Power &amp; Energy Society</span>
      <span class="gju-society-desc">Scientific and engineering information on electric power and energy.</span>
    </a>
    <a href="/jo-gju/communities/tems/" class="gju-society-card">
      <span class="gju-society-abbr">TEMS</span>
      <span class="gju-society-name">Technology &amp; Engineering Management</span>
      <span class="gju-society-desc">Bridging academia, industry, and government.</span>
    </a>
    <a href="/jo-gju/communities/aess/" class="gju-society-card">
      <span class="gju-society-abbr">AESS</span>
      <span class="gju-society-name">Aerospace &amp; Electronic Systems</span>
      <span class="gju-society-desc">Advancing systems engineering in aerospace, radar, navigation, and avionics.</span>
    </a>
    <a href="/jo-gju/communities/sight/" class="gju-society-card">
      <span class="gju-society-abbr">SIGHT</span>
      <span class="gju-society-name">Humanitarian Technology</span>
      <span class="gju-society-desc">Leveraging technology for sustainable development in underserved communities.</span>
    </a>
  </div>
</div>
</div>

<!-- UPCOMING EVENTS -->
<div style="background:var(--bg-surface);border-top:1px solid var(--border);border-bottom:1px solid var(--border);">
<div class="gju-section">
  <span class="gju-section-label">What's Happening</span>
  <h2 class="gju-section-title">Upcoming Events</h2>
  <div class="gju-events-grid">
    <div class="gju-event-card">
      <div class="gju-event-date">
        <span class="gju-event-day">&#8212;</span>
        <span class="gju-event-month">TBD</span>
      </div>
      <div class="gju-event-body">
        <span class="gju-event-tag">Workshop</span>
        <span class="gju-event-title">Add your first event here</span>
        <span class="gju-event-meta">&#128205; GJU Campus, Madaba</span>
        <a href="/jo-gju/events/" class="gju-btn gju-btn-ghost" style="font-size:0.75rem;padding:0.5rem 1rem;margin-left:0;">View Events &rarr;</a>
      </div>
    </div>
  </div>
  <div class="gju-cta-row"><a href="/jo-gju/events/" class="gju-btn gju-btn-ghost">View All Events &rarr;</a></div>
</div>
</div>

<!-- NEWS -->
<div style="background:var(--bg);">
<div class="gju-section">
  <span class="gju-section-label">Latest Updates</span>
  <h2 class="gju-section-title">News &amp; Announcements</h2>
  <div class="gju-news-grid">
    <div class="gju-news-card">
      <div class="gju-news-card-body">
        <span class="gju-category-tag">Announcement</span>
        <span class="gju-news-meta">APR 2026</span>
        <h3 style="font-size:1rem;margin:0 0 0.5rem;color:var(--text);font-family:var(--font-body);">Welcome to the new IEEE GJU website</h3>
        <p style="font-size:0.8rem;color:var(--text-muted);margin:0 0 0.75rem;">We've launched our redesigned site. Stay tuned for updates from all our societies.</p>
        <a href="/jo-gju/news/" style="font-size:0.8rem;color:var(--accent);">Read More &rarr;</a>
      </div>
    </div>
  </div>
  <div class="gju-cta-row"><a href="/jo-gju/news/" class="gju-btn gju-btn-ghost">View All News &rarr;</a></div>
</div>
</div>

<!-- HOW TO JOIN -->
<div style="background:var(--bg-surface);border-top:1px solid var(--border);">
<div class="gju-section" style="text-align:center;">
  <span class="gju-section-label">Get Involved</span>
  <h2 class="gju-section-title">How to Join IEEE</h2>
  <div class="gju-join-steps">
    <div class="gju-step-card">
      <span class="gju-step-number">01</span>
      <div class="gju-step-title">Discover</div>
      <p class="gju-step-desc">Explore our 11 active societies and find the one that matches your passion in engineering and technology.</p>
    </div>
    <div class="gju-step-card">
      <span class="gju-step-number">02</span>
      <div class="gju-step-title">Apply</div>
      <p class="gju-step-desc">Complete your IEEE membership application online. Student membership is available at a discounted rate.</p>
    </div>
    <div class="gju-step-card">
      <span class="gju-step-number">03</span>
      <div class="gju-step-title">Connect</div>
      <p class="gju-step-desc">Attend events, join society groups, collaborate on projects, and grow your professional network.</p>
    </div>
  </div>
  <div class="gju-cta-row" style="margin-top:2.5rem;">
    <a href="https://www.ieee.org/membership/join/index.html" target="_blank" class="gju-btn gju-btn-primary">Join IEEE Now &rarr;</a>
  </div>
</div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.gju-accordion-trigger').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var item = this.closest('.gju-accordion-item');
      var isOpen = item.classList.contains('open');
      document.querySelectorAll('.gju-accordion-item').forEach(function(el) { el.classList.remove('open'); });
      if (!isOpen) item.classList.add('open');
    });
  });
});
</script>
"""

if __name__ == "__main__":
    # Backup original (request edit context to get raw fields)
    original = wp_api.get(f"/pages/{HOMEPAGE_ID}", params={"context": "edit"})
    title_raw = original["title"].get("raw", original["title"].get("rendered", ""))
    content_raw = original["content"].get("raw", original["content"].get("rendered", ""))
    wp_api.log_undo(
        "rewrite homepage content",
        "PUT",
        f"{SITE_URL}/wp-json/wp/v2/pages/{HOMEPAGE_ID}",
        {"title": title_raw, "content": content_raw, "status": original["status"]}
    )

    result = wp_api.put(f"/pages/{HOMEPAGE_ID}", {
        "content": HOMEPAGE_HTML,
        "status": "publish"
    })
    print(f"Homepage updated: {result['link']}")
