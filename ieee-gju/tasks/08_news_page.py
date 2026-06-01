# /root/ieee-gju/tasks/08_news_page.py
import sys
sys.path.insert(0, "/root/ieee-gju")
import wp_api
from config import SITE_URL

with open("/root/ieee-gju/assets/style.css") as f:
    CSS = f.read()
CSS_BLOCK = f"<style>\n{CSS}\n</style>"

NEWS_HTML = CSS_BLOCK + """
<style>
@media (max-width: 900px) { .gju-news-layout { grid-template-columns: 1fr !important; } }
</style>

<!-- PAGE HEADER -->
<div style="background:var(--bg-surface);border-bottom:1px solid var(--border);padding:4rem 2rem 3rem;">
  <div style="max-width:1200px;margin:0 auto;">
    <span class="gju-section-label">IEEE GJU</span>
    <h1 style="font-family:var(--font-display);font-size:clamp(3rem,6vw,5rem);margin:.5rem 0 1rem;color:var(--text);line-height:1;">News &amp; Announcements</h1>
    <p style="color:var(--text-muted);max-width:560px;line-height:1.6;">The latest updates, achievements, and announcements from IEEE GJU and its societies.</p>
  </div>
</div>

<!-- MAIN LAYOUT -->
<div style="background:var(--bg);">
<div style="max-width:1200px;margin:0 auto;padding:4rem 2rem;display:grid;grid-template-columns:1fr 280px;gap:4rem;align-items:start;" class="gju-news-layout">

  <!-- POSTS COLUMN -->
  <div>
    <!-- FEATURED POST -->
    <div class="gju-news-card" style="margin-bottom:2rem;overflow:hidden;">
      <div style="height:220px;background:linear-gradient(135deg,var(--primary) 0%,var(--bg-surface) 100%);display:flex;align-items:flex-end;padding:2rem;">
        <div>
          <span class="gju-category-tag">Announcement</span>
          <h2 style="font-family:var(--font-display);font-size:clamp(1.8rem,4vw,2.5rem);color:var(--text);margin:.5rem 0 0;line-height:1;">Welcome to the New IEEE GJU Website</h2>
        </div>
      </div>
      <div class="gju-news-card-body">
        <span class="gju-news-meta">APR 13, 2026 &nbsp;&middot;&nbsp; IEEE GJU Team</span>
        <p style="color:var(--text-muted);line-height:1.7;margin:.75rem 0 1.25rem;">We've launched a completely redesigned website for IEEE GJU, featuring updated information about all our societies, upcoming events, and new ways to connect with us. Explore our 11 active communities and join the IEEE family at GJU.</p>
        <a href="#" class="gju-btn gju-btn-ghost" style="font-size:.8rem;padding:.6rem 1.25rem;">Read More &rarr;</a>
      </div>
    </div>

    <!-- POST GRID -->
    <div class="gju-news-grid">
      <div class="gju-news-card">
        <div class="gju-news-card-body">
          <span class="gju-category-tag">Society News</span>
          <span class="gju-news-meta" style="margin-top:.5rem;">[PLACEHOLDER DATE]</span>
          <h3 style="font-size:1rem;color:var(--text);margin:.5rem 0 .5rem;font-family:var(--font-body);font-weight:600;">[PLACEHOLDER Post Title]</h3>
          <p style="font-size:.8rem;color:var(--text-muted);line-height:1.6;margin:0 0 .75rem;">[PLACEHOLDER excerpt]</p>
          <a href="#" style="font-size:.8rem;color:var(--accent);">Read More &rarr;</a>
        </div>
      </div>
      <div class="gju-news-card">
        <div class="gju-news-card-body">
          <span class="gju-category-tag">Achievement</span>
          <span class="gju-news-meta" style="margin-top:.5rem;">[PLACEHOLDER DATE]</span>
          <h3 style="font-size:1rem;color:var(--text);margin:.5rem 0 .5rem;font-family:var(--font-body);font-weight:600;">[PLACEHOLDER Post Title]</h3>
          <p style="font-size:.8rem;color:var(--text-muted);line-height:1.6;margin:0 0 .75rem;">[PLACEHOLDER excerpt]</p>
          <a href="#" style="font-size:.8rem;color:var(--accent);">Read More &rarr;</a>
        </div>
      </div>
      <div class="gju-news-card">
        <div class="gju-news-card-body">
          <span class="gju-category-tag">Workshop Recap</span>
          <span class="gju-news-meta" style="margin-top:.5rem;">[PLACEHOLDER DATE]</span>
          <h3 style="font-size:1rem;color:var(--text);margin:.5rem 0 .5rem;font-family:var(--font-body);font-weight:600;">[PLACEHOLDER Post Title]</h3>
          <p style="font-size:.8rem;color:var(--text-muted);line-height:1.6;margin:0 0 .75rem;">[PLACEHOLDER excerpt]</p>
          <a href="#" style="font-size:.8rem;color:var(--accent);">Read More &rarr;</a>
        </div>
      </div>
    </div>
  </div>

  <!-- SIDEBAR -->
  <div style="position:sticky;top:100px;">
    <div style="background:var(--bg-surface);border:1px solid var(--border);border-radius:6px;padding:1.5rem;margin-bottom:1.5rem;">
      <span class="gju-section-label" style="margin-bottom:.75rem;">Search</span>
      <input type="search" placeholder="Search posts..." style="width:100%;background:var(--bg);border:1px solid var(--border);border-radius:4px;color:var(--text);font-family:var(--font-body);font-size:.875rem;padding:.65rem .875rem;box-sizing:border-box;outline:none;">
    </div>

    <div style="background:var(--bg-surface);border:1px solid var(--border);border-radius:6px;padding:1.5rem;margin-bottom:1.5rem;">
      <span class="gju-section-label" style="margin-bottom:.75rem;">Categories</span>
      <div style="display:flex;flex-direction:column;gap:.4rem;">
        <a href="#" style="font-size:.85rem;color:var(--text-muted);padding:.3rem 0;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;text-decoration:none;">Announcements <span style="color:var(--accent);">&#8212;</span></a>
        <a href="#" style="font-size:.85rem;color:var(--text-muted);padding:.3rem 0;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;text-decoration:none;">Society News <span style="color:var(--accent);">&#8212;</span></a>
        <a href="#" style="font-size:.85rem;color:var(--text-muted);padding:.3rem 0;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;text-decoration:none;">Achievements <span style="color:var(--accent);">&#8212;</span></a>
        <a href="#" style="font-size:.85rem;color:var(--text-muted);padding:.3rem 0;display:flex;justify-content:space-between;text-decoration:none;">Workshop Recaps <span style="color:var(--accent);">&#8212;</span></a>
      </div>
    </div>

    <div style="background:var(--bg-surface);border:1px solid var(--border);border-radius:6px;padding:1.5rem;">
      <span class="gju-section-label" style="margin-bottom:.75rem;">Upcoming Events</span>
      <a href="/jo-gju/events/" class="gju-btn gju-btn-ghost" style="width:100%;text-align:center;display:block;box-sizing:border-box;margin-left:0;">View Events &rarr;</a>
    </div>
  </div>

</div>
</div>
"""

if __name__ == "__main__":
    result = wp_api.post("/pages", {
        "title": "News & Announcements",
        "slug": "news",
        "content": NEWS_HTML,
        "status": "draft"
    })
    page_id = result["id"]
    print(f"News page created as draft (id={page_id})")

    wp_api.log_undo(
        "create News & Announcements page",
        "DELETE",
        f"{SITE_URL}/wp-json/wp/v2/pages/{page_id}?force=true",
        {}
    )

    published = wp_api.put(f"/pages/{page_id}", {"status": "publish"})
    print(f"News page published: {published['link']}")
