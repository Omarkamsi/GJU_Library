# /root/ieee-gju/tasks/06_events_page.py
import sys
sys.path.insert(0, "/root/ieee-gju")
import wp_api
from config import SITE_URL

with open("/root/ieee-gju/assets/style.css") as f:
    CSS = f.read()
CSS_BLOCK = f"<style>\n{CSS}\n</style>"

EVENTS_HTML = CSS_BLOCK + """
<style>
.gju-filter-bar{background:var(--bg);border-bottom:1px solid var(--border);padding:1rem 2rem;position:sticky;top:72px;z-index:100;}
.gju-filter-bar-inner{max-width:1200px;margin:0 auto;display:flex;gap:.75rem;flex-wrap:wrap;align-items:center;}
</style>

<!-- PAGE HEADER -->
<div style="background:var(--bg-surface);border-bottom:1px solid var(--border);padding:4rem 2rem 3rem;">
  <div style="max-width:1200px;margin:0 auto;">
    <span class="gju-section-label">IEEE GJU</span>
    <h1 style="font-family:var(--font-display);font-size:clamp(3rem,6vw,5rem);margin:.5rem 0 1rem;color:var(--text);line-height:1;">Events</h1>
    <p style="color:var(--text-muted);max-width:560px;line-height:1.6;">Workshops, seminars, competitions, and networking events from IEEE GJU societies and the IEEE Jordan Section.</p>
  </div>
</div>

<!-- FILTERS -->
<div class="gju-filter-bar">
  <div class="gju-filter-bar-inner">
    <span style="font-family:var(--font-mono);font-size:.65rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:.1em;margin-right:.5rem;">Filter:</span>
    <button class="gju-filter-btn active" onclick="filterTime(this,'all')">All</button>
    <button class="gju-filter-btn" onclick="filterTime(this,'week')">This Week</button>
    <button class="gju-filter-btn" onclick="filterTime(this,'month')">This Month</button>
    <div style="width:1px;height:20px;background:var(--border);margin:0 .5rem;"></div>
    <button class="gju-filter-btn" onclick="filterType(this,'Workshop')">Workshop</button>
    <button class="gju-filter-btn" onclick="filterType(this,'Seminar')">Seminar</button>
    <button class="gju-filter-btn" onclick="filterType(this,'Competition')">Competition</button>
    <button class="gju-filter-btn" onclick="filterType(this,'Networking')">Networking</button>
  </div>
</div>

<!-- EVENTS GRID -->
<div style="background:var(--bg);">
<div class="gju-section">
  <div class="gju-events-grid" id="events-container">

    <div class="gju-event-card" data-type="Workshop" data-date="2026-05-01">
      <div class="gju-event-date">
        <span class="gju-event-day">01</span>
        <span class="gju-event-month">MAY</span>
      </div>
      <div class="gju-event-body">
        <span class="gju-event-tag">Workshop</span>
        <span class="gju-event-title">[PLACEHOLDER] Add your first event title</span>
        <span class="gju-event-meta">&#128205; GJU Campus, Madaba &nbsp;&middot;&nbsp; &#128336; 10:00 AM</span>
        <p style="font-size:.8rem;color:var(--text-muted);margin:.5rem 0 1rem;line-height:1.5;">Short description of the event. Update this with actual event details from vtools.ieee.org.</p>
        <a href="https://events.vtools.ieee.org" target="_blank" class="gju-btn gju-btn-primary" style="font-size:.75rem;padding:.5rem 1rem;">Register &rarr;</a>
      </div>
    </div>

    <div id="empty-state" style="display:none;grid-column:1/-1;text-align:center;padding:4rem 2rem;">
      <div style="font-family:var(--font-display);font-size:3rem;color:var(--text-muted);margin-bottom:1rem;">NO EVENTS</div>
      <p style="color:var(--text-muted);margin-bottom:1.5rem;">No upcoming events match your filter. Check back soon.</p>
      <a href="https://events.vtools.ieee.org" target="_blank" class="gju-btn gju-btn-ghost">Browse IEEE Jordan Events &rarr;</a>
    </div>

  </div>
  <div class="gju-cta-row" style="margin-top:2rem;">
    <a href="https://events.vtools.ieee.org" target="_blank" class="gju-btn gju-btn-ghost">View All IEEE Jordan Events &rarr;</a>
  </div>
</div>
</div>

<script>
var activeType = null;
function filterTime(btn, filter) {
  document.querySelectorAll('[onclick^="filterTime"]').forEach(function(b){ b.classList.remove('active'); });
  btn.classList.add('active');
  applyFilters();
}
function filterType(btn, type) {
  if (activeType === type) {
    activeType = null;
    document.querySelectorAll('[onclick^="filterType"]').forEach(function(b){ b.classList.remove('active'); });
  } else {
    activeType = type;
    document.querySelectorAll('[onclick^="filterType"]').forEach(function(b){ b.classList.remove('active'); });
    btn.classList.add('active');
  }
  applyFilters();
}
function applyFilters() {
  var cards = document.querySelectorAll('#events-container .gju-event-card');
  var visible = 0;
  cards.forEach(function(card) {
    var show = !activeType || card.dataset.type === activeType;
    card.style.display = show ? 'flex' : 'none';
    if (show) visible++;
  });
  var empty = document.getElementById('empty-state');
  if (empty) empty.style.display = visible === 0 ? 'block' : 'none';
}
</script>
"""

if __name__ == "__main__":
    # Create as draft
    result = wp_api.post("/pages", {
        "title": "Events",
        "slug": "events",
        "content": EVENTS_HTML,
        "status": "draft"
    })
    page_id = result["id"]
    print(f"Events page created as draft (id={page_id})")

    # Log undo
    wp_api.log_undo(
        "create Events page",
        "DELETE",
        f"{SITE_URL}/wp-json/wp/v2/pages/{page_id}?force=true",
        {}
    )

    # Publish immediately
    published = wp_api.put(f"/pages/{page_id}", {"status": "publish"})
    print(f"Events page published: {published['link']}")
