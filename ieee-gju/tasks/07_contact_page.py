# /root/ieee-gju/tasks/07_contact_page.py
import sys
sys.path.insert(0, "/root/ieee-gju")
import wp_api
from config import SITE_URL

with open("/root/ieee-gju/assets/style.css") as f:
    CSS = f.read()
CSS_BLOCK = f"<style>\n{CSS}\n</style>"

SOCIETIES = [
    "Computer Society (CS)",
    "Industrial Electronics Society (IES)",
    "Engineering in Medicine & Biology (EMBS)",
    "Women in Engineering (WIE)",
    "Industry Applications Society (IAS)",
    "Robotics & Automation Society (RAS)",
    "Consumer Technology Society (CTSoc)",
    "Power & Energy Society (PES)",
    "Technology & Engineering Management (TEMS)",
    "Aerospace & Electronic Systems (AESS)",
    "SIGHT (Humanitarian Technology)",
]

ACCORDION_ITEMS = ""
for society in SOCIETIES:
    ACCORDION_ITEMS += f"""
    <div class="gju-accordion-item">
      <button class="gju-accordion-trigger">{society} <span>+</span></button>
      <div class="gju-accordion-content">
        <strong style="color:var(--text);">Contact:</strong> [PLACEHOLDER Name]<br>
        <strong style="color:var(--text);">Email:</strong> <a href="mailto:[PLACEHOLDER]" style="color:var(--accent);">[PLACEHOLDER]@ieee.org</a><br>
        <strong style="color:var(--text);">WhatsApp:</strong> <a href="#" style="color:var(--accent);">[PLACEHOLDER link]</a>
      </div>
    </div>"""

CONTACT_HTML = CSS_BLOCK + f"""

<!-- PAGE HEADER -->
<div style="background:var(--bg-surface);border-bottom:1px solid var(--border);padding:4rem 2rem 3rem;">
  <div style="max-width:1200px;margin:0 auto;">
    <span class="gju-section-label">IEEE GJU</span>
    <h1 style="font-family:var(--font-display);font-size:clamp(3rem,6vw,5rem);margin:.5rem 0 1rem;color:var(--text);line-height:1;">Contact Us</h1>
    <p style="color:var(--text-muted);max-width:560px;line-height:1.6;">Have a question? Want to join a society? We'd love to hear from you.</p>
  </div>
</div>

<!-- CONTACT GRID -->
<div style="background:var(--bg);">
<div class="gju-section">
  <div class="gju-contact-grid">

    <!-- LEFT COLUMN -->
    <div>
      <span class="gju-section-label" style="margin-bottom:1.25rem;">Reach Us</span>
      <div class="gju-contact-channels" style="margin-bottom:2.5rem;">
        <a href="mailto:[PLACEHOLDER]@ieee.org" class="gju-channel-link">
          <div class="gju-channel-icon">&#9993;</div>
          <span>[PLACEHOLDER]@ieee.org</span>
        </a>
        <a href="https://wa.me/[PLACEHOLDER]" target="_blank" class="gju-channel-link">
          <div class="gju-channel-icon">&#128172;</div>
          <span>WhatsApp Group</span>
        </a>
        <a href="https://www.instagram.com/ieeegju/" target="_blank" class="gju-channel-link">
          <div class="gju-channel-icon">&#128247;</div>
          <span>@ieeegju on Instagram</span>
        </a>
        <a href="[PLACEHOLDER LinkedIn URL]" target="_blank" class="gju-channel-link">
          <div class="gju-channel-icon">&#128188;</div>
          <span>IEEE GJU on LinkedIn</span>
        </a>
      </div>

      <span class="gju-section-label" style="margin-bottom:1rem;">Society Contacts</span>
      <div class="gju-accordion">
        {ACCORDION_ITEMS}
      </div>
    </div>

    <!-- RIGHT COLUMN: FORM -->
    <div>
      <span class="gju-section-label" style="margin-bottom:1.5rem;">Send a Message</span>
      <form class="gju-form" id="contact-form">
        <label>Full Name</label>
        <input type="text" name="name" placeholder="Your full name" required>
        <label>Email Address</label>
        <input type="email" name="email" placeholder="your@email.com" required>
        <label>Subject</label>
        <select name="subject" required>
          <option value="" disabled selected>Select a subject</option>
          <option>General Inquiry</option>
          <option>Join a Society</option>
          <option>Event Question</option>
          <option>Partnership</option>
          <option>Other</option>
        </select>
        <label>Message</label>
        <textarea name="message" placeholder="Write your message here..." required></textarea>
        <button type="submit" class="gju-btn gju-btn-primary" style="width:100%;text-align:center;border:none;">Send Message</button>
      </form>
      <div id="form-success" style="display:none;text-align:center;padding:3rem;background:var(--bg-surface);border:1px solid var(--border);border-radius:6px;">
        <div style="font-family:var(--font-display);font-size:3rem;color:var(--accent);margin-bottom:1rem;">&#10003;</div>
        <h3 style="color:var(--text);margin-bottom:.5rem;font-family:var(--font-body);">Message Sent!</h3>
        <p style="color:var(--text-muted);">We'll get back to you soon.</p>
      </div>
    </div>

  </div>
</div>
</div>

<!-- MAP -->
<div style="background:var(--bg-surface);border-top:1px solid var(--border);padding:3rem 2rem;">
  <div style="max-width:1200px;margin:0 auto;">
    <span class="gju-section-label" style="margin-bottom:1rem;">Find Us</span>
    <div style="border-radius:6px;overflow:hidden;border:1px solid var(--border);">
      <iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3394.3!2d35.7538!3d31.7158!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x151b5fb85d7981af%3A0x631c30c0f8dc65e8!2sGerman%20Jordanian%20University!5e0!3m2!1sen!2sjo!4v1"
        width="100%" height="320" style="border:0;display:block;" allowfullscreen="" loading="lazy">
      </iframe>
    </div>
    <p style="font-size:.8rem;color:var(--text-muted);margin-top:.75rem;">German Jordanian University, Mushaqar, Madaba, Jordan</p>
  </div>
</div>

<script>
// Accordion + Form submit
document.addEventListener('DOMContentLoaded', function() {{
  document.querySelectorAll('.gju-accordion-trigger').forEach(function(btn) {{
    btn.addEventListener('click', function() {{
      var item = this.closest('.gju-accordion-item');
      var isOpen = item.classList.contains('open');
      document.querySelectorAll('.gju-accordion-item').forEach(function(el) {{ el.classList.remove('open'); }});
      if (!isOpen) item.classList.add('open');
    }});
  }});
  var form = document.getElementById('contact-form');
  if (form) {{
    form.addEventListener('submit', function() {{
      document.getElementById('contact-form').style.display = 'none';
      document.getElementById('form-success').style.display = 'block';
      return false;
    }});
  }}
}});
</script>
"""

if __name__ == "__main__":
    # Check if a contact page already exists; update it rather than creating a duplicate
    existing = wp_api.get("/pages", {"slug": "contact-us", "per_page": 1})
    if not existing:
        existing = wp_api.get("/pages", {"slug": "contact", "per_page": 1})

    if existing:
        page_id = existing[0]["id"]
        old_content = existing[0]["content"].get("raw", existing[0]["content"].get("rendered", ""))
        old_title = existing[0]["title"].get("raw", existing[0]["title"].get("rendered", "Contact Us"))
        print(f"Found existing Contact Us page (id={page_id}), updating...")
        wp_api.log_undo(
            "update Contact Us page",
            "PUT",
            f"{SITE_URL}/wp-json/wp/v2/pages/{page_id}",
            {"content": old_content, "title": old_title, "status": existing[0]["status"]}
        )
        published = wp_api.put(f"/pages/{page_id}", {
            "title": "Contact Us",
            "slug": "contact-us",
            "content": CONTACT_HTML,
            "status": "publish"
        })
        print(f"Contact page updated and published: {published['link']}")
    else:
        result = wp_api.post("/pages", {
            "title": "Contact Us",
            "slug": "contact",
            "content": CONTACT_HTML,
            "status": "draft"
        })
        page_id = result["id"]
        print(f"Contact page created as draft (id={page_id})")

        wp_api.log_undo(
            "create Contact Us page",
            "DELETE",
            f"{SITE_URL}/wp-json/wp/v2/pages/{page_id}?force=true",
            {}
        )

        published = wp_api.put(f"/pages/{page_id}", {"status": "publish"})
        print(f"Contact page published: {published['link']}")
