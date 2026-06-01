#!/usr/bin/env python3
"""
Full homepage redesign for IEEE GJU Student Branch.
Injects CSS via [vc_raw_html] shortcode + builds all 7 sections.
Targets page ID 2.
"""
import sys, base64
sys.path.insert(0, '/root/ieee-gju')
import wp_api as api

HOMEPAGE_ID = 2

# ── Read CSS ────────────────────────────────────────────────────────────────
with open('/root/ieee-gju/assets/style.css', 'r') as f:
    css = f.read()

style_block = f"<style>{css}</style>"
b64 = base64.b64encode(style_block.encode()).decode()
css_shortcode = f"[vc_raw_html]{b64}[/vc_raw_html]"

# ── Homepage HTML ───────────────────────────────────────────────────────────
html = """
<!-- ══════════════════════════════════════════════════
     HERO
══════════════════════════════════════════════════ -->
<section class="gju-hero">
  <div class="gju-hero-content">
    <div class="gju-hero-badge">
      <span class="gju-hero-badge-dot"></span>
      IEEE Student Branch &bull; German Jordanian University
    </div>
    <h1>
      ENGINEERING<br>
      <span class="hero-accent">TOMORROW</span>
    </h1>
    <p class="gju-hero-sub">
      The official IEEE Student Branch at GJU — connecting engineers,
      advancing innovation, and building the next generation of technical
      leaders in Jordan and beyond.
    </p>
    <div class="gju-hero-ctas">
      <a href="https://www.ieee.org/membership/join/index.html" target="_blank" class="gju-btn gju-btn-primary">Join IEEE</a>
      <a href="/jo-gju/communities/" class="gju-btn gju-btn-outline">Explore Communities</a>
    </div>
  </div>
  <div class="gju-scroll-cue">
    <span>Scroll</span>
    <span class="gju-scroll-arrow"></span>
  </div>
</section>

<!-- Stats bar -->
<div style="background:#0d1a35;border-top:1px solid rgba(247,181,0,0.18);border-bottom:1px solid rgba(247,181,0,0.18);">
  <div class="gju-hero-stats">
    <div class="gju-hero-stat">
      <span class="gju-hero-stat-num">11</span>
      <span class="gju-hero-stat-label">Active Societies</span>
    </div>
    <div class="gju-hero-stat">
      <span class="gju-hero-stat-num">400K+</span>
      <span class="gju-hero-stat-label">IEEE Members Worldwide</span>
    </div>
    <div class="gju-hero-stat">
      <span class="gju-hero-stat-num">160+</span>
      <span class="gju-hero-stat-label">Countries</span>
    </div>
    <div class="gju-hero-stat">
      <span class="gju-hero-stat-num">GJU</span>
      <span class="gju-hero-stat-label">Our Campus</span>
    </div>
  </div>
</div>

<!-- ══════════════════════════════════════════════════
     ABOUT
══════════════════════════════════════════════════ -->
<div class="bg-1">
<div class="gju-section">
  <span class="gju-section-label">Who We Are</span>
  <h2 class="gju-section-title">IEEE GJU Student Branch</h2>
  <hr class="gju-divider">
  <div class="gju-about-wrap">
    <div class="gju-about-text">
      <p>
        Founded at the German Jordanian University in Madaba, our IEEE Student
        Branch brings together engineering and technology students who want to
        go beyond the classroom — to build, compete, collaborate, and lead.
      </p>
      <p>
        We host 11 active technical societies, covering everything from robotics
        and AI to biomedical engineering and power systems. Whether you want to
        win a hackathon, earn an IEEE certification, or simply meet people who
        share your passion — this is your home.
      </p>
      <a href="/jo-gju/about/" class="gju-btn gju-btn-ghost" style="padding-left:0">Learn more about us</a>
    </div>
    <div class="gju-about-highlights">
      <div class="gju-highlight-row">
        <span class="gju-highlight-icon">&#127942;</span>
        <div>
          <h4>Award-Winning Projects</h4>
          <p>Our members have taken top prizes at regional and international IEEE competitions.</p>
        </div>
      </div>
      <div class="gju-highlight-row">
        <span class="gju-highlight-icon">&#127891;</span>
        <div>
          <h4>Workshops &amp; Training</h4>
          <p>Hands-on technical sessions run throughout the semester across all societies.</p>
        </div>
      </div>
      <div class="gju-highlight-row">
        <span class="gju-highlight-icon">&#128101;</span>
        <div>
          <h4>Strong Community</h4>
          <p>A diverse, inclusive network of students and faculty advisors at GJU.</p>
        </div>
      </div>
      <div class="gju-highlight-row">
        <span class="gju-highlight-icon">&#127758;</span>
        <div>
          <h4>Global IEEE Network</h4>
          <p>Your membership connects you to 400K+ engineers in 160+ countries.</p>
        </div>
      </div>
    </div>
  </div>
</div>
</div>

<hr class="section-divider">

<!-- ══════════════════════════════════════════════════
     COMMUNITIES
══════════════════════════════════════════════════ -->
<div class="bg-2">
<div class="gju-section">
  <span class="gju-section-label">Our Communities</span>
  <h2 class="gju-section-title">Find Your Society</h2>
  <p class="gju-section-sub">
    Eleven active IEEE societies at GJU — each with its own events, projects,
    and leadership opportunities. Pick the one that matches your passion.
  </p>
  <div class="gju-society-grid">

    <a href="/jo-gju/communities/computer-society-cs/" class="gju-society-card">
      <span class="gju-society-abbr">CS</span>
      <span class="gju-society-name">Computer Society</span>
      <span class="gju-society-desc">Software development, AI, cybersecurity, data science, and the future of computing.</span>
    </a>

    <a href="/jo-gju/communities/robotics-and-automation-society-ras/" class="gju-society-card">
      <span class="gju-society-abbr">RAS</span>
      <span class="gju-society-name">Robotics &amp; Automation Society</span>
      <span class="gju-society-desc">Design, build, and program the robots and automated systems of tomorrow.</span>
    </a>

    <a href="/jo-gju/communities/engineering-in-medicine-and-biology-society-embs/" class="gju-society-card">
      <span class="gju-society-abbr">EMBS</span>
      <span class="gju-society-name">Engineering in Medicine &amp; Biology</span>
      <span class="gju-society-desc">Where engineering meets healthcare to advance medical science and patient outcomes.</span>
    </a>

    <a href="/jo-gju/communities/power-energy-society-pes/" class="gju-society-card">
      <span class="gju-society-abbr">PES</span>
      <span class="gju-society-name">Power &amp; Energy Society</span>
      <span class="gju-society-desc">Electric power systems, renewable energy, and the grid of the future.</span>
    </a>

    <a href="/jo-gju/communities/industrial-electronics-society-ies/" class="gju-society-card">
      <span class="gju-society-abbr">IES</span>
      <span class="gju-society-name">Industrial Electronics Society</span>
      <span class="gju-society-desc">Practical applications of electronics and control across industrial sectors.</span>
    </a>

    <a href="/jo-gju/communities/women-in-engineering-wie/" class="gju-society-card">
      <span class="gju-society-abbr">WIE</span>
      <span class="gju-society-name">Women in Engineering</span>
      <span class="gju-society-desc">Diversity, inclusion, empowerment, and mentorship in engineering for all.</span>
    </a>

    <a href="/jo-gju/communities/industry-applications-societyias/" class="gju-society-card">
      <span class="gju-society-abbr">IAS</span>
      <span class="gju-society-name">Industry Applications Society</span>
      <span class="gju-society-desc">Bridging the gap between theory and real-world engineering practice.</span>
    </a>

    <a href="/jo-gju/communities/consumer-technology-society-ctsoc/" class="gju-society-card">
      <span class="gju-society-abbr">CTSoc</span>
      <span class="gju-society-name">Consumer Technology Society</span>
      <span class="gju-society-desc">Innovating the products and experiences people use every day.</span>
    </a>

    <a href="/jo-gju/communities/tems/" class="gju-society-card">
      <span class="gju-society-abbr">TEMS</span>
      <span class="gju-society-name">Technology &amp; Engineering Management</span>
      <span class="gju-society-desc">Leadership, strategy, and management skills for engineers in industry.</span>
    </a>

    <a href="/jo-gju/communities/aess/" class="gju-society-card">
      <span class="gju-society-abbr">AESS</span>
      <span class="gju-society-name">Aerospace &amp; Electronic Systems</span>
      <span class="gju-society-desc">Radar, navigation, avionics, and the systems engineering behind aerospace.</span>
    </a>

    <a href="/jo-gju/communities/sight/" class="gju-society-card">
      <span class="gju-society-abbr">SIGHT</span>
      <span class="gju-society-name">Humanitarian Technology</span>
      <span class="gju-society-desc">Leveraging technology for sustainable development in underserved communities.</span>
    </a>

  </div>
  <div class="gju-cta-row">
    <a href="/jo-gju/communities/" class="gju-btn gju-btn-outline">View All Communities</a>
  </div>
</div>
</div>

<hr class="section-divider">

<!-- ══════════════════════════════════════════════════
     EVENTS
══════════════════════════════════════════════════ -->
<div class="bg-1">
<div class="gju-section">
  <span class="gju-section-label">What&rsquo;s Happening</span>
  <h2 class="gju-section-title">Events &amp; Activities</h2>
  <div class="gju-events-cta-block">
    <div>
      <h3>Stay in the loop.</h3>
      <p>
        From technical workshops and hackathons to industry talks and career
        fairs — there&rsquo;s always something happening at IEEE GJU. Track
        all upcoming events through the IEEE vTools portal.
      </p>
      <div class="gju-events-tags">
        <span class="gju-tag">Workshops</span>
        <span class="gju-tag">Hackathons</span>
        <span class="gju-tag">Talks</span>
        <span class="gju-tag">Competitions</span>
        <span class="gju-tag">Career Fairs</span>
      </div>
      <div style="margin-top:1.75rem;display:flex;gap:1rem;flex-wrap:wrap">
        <a href="/jo-gju/events/" class="gju-btn gju-btn-primary">Browse Events</a>
        <a href="https://events.vtools.ieee.org/org/jo-gju" target="_blank" class="gju-btn gju-btn-outline">IEEE vTools</a>
      </div>
    </div>
    <div class="gju-events-visual">
      <div class="gju-event-mini">
        <span class="gju-event-mini-date">Upcoming</span>
        <span class="gju-event-mini-title">Technical Workshop</span>
        <span class="gju-event-mini-type">GJU Campus &bull; Madaba</span>
      </div>
      <div class="gju-event-mini">
        <span class="gju-event-mini-date">Upcoming</span>
        <span class="gju-event-mini-title">Hackathon &amp; Project Competition</span>
        <span class="gju-event-mini-type">Open to all GJU students</span>
      </div>
      <div class="gju-event-mini">
        <span class="gju-event-mini-date">Recurring</span>
        <span class="gju-event-mini-title">Industry Speaker Series</span>
        <span class="gju-event-mini-type">Online &amp; On-campus</span>
      </div>
      <div class="gju-event-mini">
        <span class="gju-event-mini-date">Semester</span>
        <span class="gju-event-mini-title">Society General Meetings</span>
        <span class="gju-event-mini-type">All 11 societies</span>
      </div>
    </div>
  </div>
</div>
</div>

<hr class="section-divider">

<!-- ══════════════════════════════════════════════════
     WHY JOIN
══════════════════════════════════════════════════ -->
<div class="bg-3">
<div class="gju-section">
  <span class="gju-section-label">Why It Matters</span>
  <h2 class="gju-section-title">Why Join IEEE GJU?</h2>
  <p class="gju-section-sub">
    Membership isn&rsquo;t just a card. It&rsquo;s access to a world-class
    network, skills that matter, and experiences that shape careers.
  </p>
  <div class="gju-benefits-grid">
    <div class="gju-benefit-card">
      <span class="gju-benefit-icon">&#127760;</span>
      <h3>Global Network</h3>
      <p>Connect with 400,000+ engineers in 160+ countries. IEEE membership opens doors to a truly global professional community.</p>
    </div>
    <div class="gju-benefit-card">
      <span class="gju-benefit-icon">&#128187;</span>
      <h3>Technical Skills</h3>
      <p>Hands-on workshops, coding sessions, and project teams run by your peers and IEEE-certified experts.</p>
    </div>
    <div class="gju-benefit-card">
      <span class="gju-benefit-icon">&#127941;</span>
      <h3>Competitions</h3>
      <p>Represent GJU at regional and international IEEE competitions — from robotics to engineering design challenges.</p>
    </div>
    <div class="gju-benefit-card">
      <span class="gju-benefit-icon">&#128274;</span>
      <h3>IEEE Resources</h3>
      <p>Access IEEE Xplore, the world&rsquo;s largest repository of technical papers, standards, and research journals.</p>
    </div>
    <div class="gju-benefit-card">
      <span class="gju-benefit-icon">&#127891;</span>
      <h3>Leadership &amp; Growth</h3>
      <p>Take on committee roles, run your own events, and build the organisational and leadership skills employers look for.</p>
    </div>
    <div class="gju-benefit-card">
      <span class="gju-benefit-icon">&#128188;</span>
      <h3>Career Opportunities</h3>
      <p>Meet industry professionals, attend career fairs, and get introductions through the IEEE Jordan Section network.</p>
    </div>
  </div>
</div>
</div>

<hr class="section-divider">

<!-- ══════════════════════════════════════════════════
     HOW TO JOIN
══════════════════════════════════════════════════ -->
<div class="bg-2">
<div class="gju-section" style="text-align:center">
  <span class="gju-section-label">Get Started</span>
  <h2 class="gju-section-title">How to Join</h2>
  <p class="gju-section-sub" style="margin:0 auto var(--space-xl)">
    Three simple steps to become an IEEE GJU member and unlock everything the branch has to offer.
  </p>
  <div class="gju-steps-row">
    <div class="gju-step">
      <div class="gju-step-num">01</div>
      <h3>Discover</h3>
      <p>Explore our 11 active societies and find the one — or several — that match your interests and career goals.</p>
    </div>
    <div class="gju-step">
      <div class="gju-step-num">02</div>
      <h3>Apply</h3>
      <p>Complete your IEEE membership application at ieee.org. Student membership is available at a significantly discounted rate.</p>
    </div>
    <div class="gju-step">
      <div class="gju-step-num">03</div>
      <h3>Connect</h3>
      <p>Attend events, join society groups, collaborate on projects, and grow your professional network from day one.</p>
    </div>
  </div>
  <div class="gju-cta-row">
    <a href="https://www.ieee.org/membership/join/index.html" target="_blank" class="gju-btn gju-btn-primary" style="font-size:1rem;padding:1rem 2.5rem">
      Join IEEE Now
    </a>
  </div>
</div>
</div>

<hr class="section-divider">

<!-- ══════════════════════════════════════════════════
     SOCIAL / CONNECT
══════════════════════════════════════════════════ -->
<div class="bg-1">
<div class="gju-section">
  <div class="gju-connect-wrap">
    <div>
      <span class="gju-section-label">Stay Connected</span>
      <h2 class="gju-section-title">Follow &amp; Connect</h2>
      <hr class="gju-divider">
      <p style="font-size:1.05rem;color:#374558;max-width:480px;line-height:1.7">
        Follow us on social media for the latest events, announcements, and
        highlights from across all IEEE GJU societies.
      </p>
      <div class="gju-social-row">
        <a href="https://www.instagram.com/ieeegju/" target="_blank" class="gju-social-btn">
          &#128247;&nbsp; Instagram
        </a>
        <a href="https://www.linkedin.com/company/ieee-gju-student-branch/" target="_blank" class="gju-social-btn">
          &#128101;&nbsp; LinkedIn
        </a>
        <a href="https://chat.whatsapp.com/ITEd4RGpRbIHRGPgQzojYo" target="_blank" class="gju-social-btn">
          &#128172;&nbsp; WhatsApp
        </a>
      </div>
    </div>
    <div class="gju-connect-cta-block">
      <h3>Ready?</h3>
      <p>Join hundreds of GJU students already part of the IEEE community.</p>
      <a href="https://www.ieee.org/membership/join/index.html" target="_blank" class="gju-btn gju-btn-primary">
        Become a Member
      </a>
    </div>
  </div>
</div>
</div>
"""

# ── Combine & Push ──────────────────────────────────────────────────────────
content = css_shortcode + "\n\n" + html.strip()

# Snapshot current content for undo
current = api.get(f"/pages/{HOMEPAGE_ID}", {"context": "edit"})
old_content = current.get("content", {}).get("raw", "")

api.log_undo(
    description="Homepage redesign v4 — light theme, updated social links, larger badge",
    method="PUT",
    url=f"/pages/{HOMEPAGE_ID}",
    payload={"content": old_content, "status": "publish"},
)

result = api.put(f"/pages/{HOMEPAGE_ID}", {
    "content": content,
    "status": "publish",
})

link = result.get("link", "")
print(f"Homepage updated: {link}")
print(f"Content size: {len(content):,} chars | CSS: {len(css):,} chars")
