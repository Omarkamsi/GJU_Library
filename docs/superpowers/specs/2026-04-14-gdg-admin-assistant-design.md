# GDG on Campus GJU — Admin Assistant Design Spec

**Date:** 2026-04-14  
**Chapter:** GDG on Campus German Jordanian University — Madaba, Jordan  
**Author:** Organizer (authorized chapter lead)  
**Status:** Approved for implementation

---

## Overview

An AI-powered organizer productivity assistant for managing the GDG on Campus GJU chapter on gdg.community.dev. The assistant helps draft announcements, events, and emails; presents full previews; and requires explicit organizer approval before any action that affects the live platform or sends email. Every action is logged in an audit trail.

This is an organizer workflow tool — not an autonomous agent. It never acts without human approval.

---

## A. Architecture

### Approach: Hybrid (Playwright + Gmail API)

Three layers:

1. **Playwright layer `[UI AUTOMATION]`** — Controls gdg.community.dev after the organizer logs in manually. Used for all dashboard operations (read, draft, publish announcements/events) because gdg.community.dev exposes no public organizer API. Labeled `[UI AUTOMATION]` everywhere.

2. **Gmail API layer `[OFFICIAL API]`** — OAuth2-authenticated. Handles all email operations (create drafts, send). Reliable and structured. Never sends without explicit confirmation.

3. **FastAPI core** — Gemini Pro orchestrates all operations. Receives chat commands, generates drafts, routes to the appropriate layer, enforces approval gates, and logs every action to SQLite.

**Key assumption:** gdg.community.dev has no public organizer API. All dashboard operations are Playwright UI automation and may break if the platform updates its UI. This is clearly labeled throughout the codebase.

### Data flow

```
Organizer → Chat Panel → FastAPI Orchestrator → Safety Guardrail
  → Content/Email Generator (Gemini Pro)
  → Approval Gate (hard stop)
  → Action Executor (Playwright or Gmail API)
  → Audit Logger → SQLite
```

---

## B. Core Modules

Ten modules, each with one responsibility:

| Module | Responsibility | Layer |
|---|---|---|
| **Session Manager** | Playwright browser lifecycle; detects login expiry | UI Automation |
| **Dashboard Reader** | Read-only page scraping; returns structured JSON | UI Automation |
| **Content Generator** | Gemini Pro drafting for announcements/events/posts | AI |
| **Email Drafter** | Gemini drafts + saves to Gmail Drafts via API | Official API |
| **Approval Gate** | Hard blocks all publish/send until organizer approves | Safety |
| **Action Executor** | Runs approved actions; registers rollback before executing | Gated |
| **Audit Logger** | Append-only SQLite log of every action | Always-on |
| **Safety Guardrail** | Validates scope, rate limits, recipient lists, dry-run | Always-on |
| **Context Store** | Rolling conversation window (last 20 turns) + 5-min dashboard cache | Memory |
| **Orchestrator** | Parses intent, assembles multi-step workflows | Core brain |

**Fixed execution order for every action:**

```
Organizer → Orchestrator → Safety Guardrail → Generator → Approval Gate → Executor → Audit Logger
```

---

## C. Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| AI Brain | Gemini Pro (`google-generativeai`) | Google ecosystem fit for GDG |
| Backend | FastAPI (Python, async) | Agent orchestration, REST API |
| Browser automation | Playwright (async Python) | gdg.community.dev UI automation |
| Email | Gmail API (`google-api-python-client`) | OAuth2; official and reliable |
| Frontend | Next.js + Tailwind CSS | Chat + preview panel UI |
| Database | SQLite via SQLAlchemy | Local-first, zero setup |
| Auth | OAuth2 (Google) | Gmail API only; GDG login stays manual |
| Secrets | `.env` + `python-dotenv` | Local MVP; GCP Secret Manager for cloud |

---

## D. Workflow Design

### Dashboard Action Flow (e.g. "Create announcement for AI workshop")

1. **Organizer** types command in chat. Already logged in to gdg.community.dev in the Playwright browser.
2. **Dashboard Reader** — Playwright reads current page state (events, announcements, schedule). Returns structured JSON. `[UI AUTOMATION]`
3. **Safety Guardrail** — validates action is within organizer scope, checks rate limits.
4. **Content Generator** — Gemini Pro drafts the announcement (title, body, tags, date) using the command and dashboard context. `[AI GENERATION — DRAFT ONLY]`
5. **Approval Gate** `🔴 HARD STOP` — Preview panel shows full draft. Organizer must click "Approve & Publish". No automatic continuation.
6. **Action Executor** — Registers rollback entry, then Playwright fills and submits the form on gdg.community.dev. `[UI AUTOMATION]`
7. **Audit Logger** — Logs action type, draft content, timestamp, approval, execution result, URL.

Rollback window: 10 minutes after publish.

### Email Workflow Flow (e.g. "Email approved registrants with updated venue")

1. **Organizer** types command, specifies audience ("approved registrants", "speakers", or provides CSV).
2. **Recipient Validator** — Reads registrant list from dashboard (Playwright) or local CSV. Validates all addresses. Shows organizer the count. `[UI AUTOMATION / local file]`
3. **Organizer confirms** recipient count.
4. **Email Drafter** — Gemini Pro writes subject + body. Saves immediately to Gmail Drafts via API. `[OFFICIAL API]`
5. **Approval Gate** `🔴 HARD STOP` — Preview panel shows: To (full list), Subject, Body, recipient count, reason. Organizer must click "Send".
6. **Action Executor** — Gmail API sends the draft. Rate limiter enforced. Returns message IDs. `[OFFICIAL API]`
7. **Audit Logger** — Logs recipient list, subject, body hash, send timestamp, approval, Gmail message IDs, delivery status.

**Two hard stops in the email flow** — recipient count confirmation and full preview — by design.

---

## E. Safety Model

Seven hardcoded guardrails — not configurable by any command:

1. **Explicit confirmation** — publish/send is blocked until the organizer clicks Approve. No timeouts, no auto-continue.
2. **Scoped permissions** — agent only accesses pages within the organizer's own dashboard. No access to other chapters or private member data.
3. **Recipient validation** — email recipients must come from an approved source (dashboard registrant list or an explicitly provided CSV). Free-text email lists are rejected.
4. **Dry-run mode** — toggle in the top bar. All actions generate previews and log entries but nothing is published or sent. Suitable for testing.
5. **Rollback registry** — before every Playwright publish, the pre-action state is scraped and saved. 10-minute rollback window.
6. **Rate limits** — max 5 publishes/hour, max 50 emails/day, max 100 dashboard reads/hour. Hard stops, not warnings.
7. **Sensitive action warnings** — deleting or modifying live content triggers an extra confirmation with a red warning banner and a 5-second delay on the confirm button.

---

## F. Data Model (SQLite)

```sql
-- Active browser sessions
CREATE TABLE sessions (
    id          TEXT PRIMARY KEY,
    started_at  DATETIME NOT NULL,
    browser_status TEXT NOT NULL,  -- 'connected' | 'disconnected' | 'expired'
    gdg_logged_in BOOLEAN DEFAULT FALSE
);

-- All generated drafts (announcements, events, emails)
CREATE TABLE drafts (
    id          TEXT PRIMARY KEY,
    session_id  TEXT REFERENCES sessions(id),
    type        TEXT NOT NULL,  -- 'announcement' | 'event' | 'email' | 'post'
    content_json TEXT NOT NULL, -- full structured draft
    status      TEXT NOT NULL,  -- 'pending' | 'approved' | 'published' | 'discarded'
    created_at  DATETIME NOT NULL
);

-- Approval decisions
CREATE TABLE approvals (
    id          TEXT PRIMARY KEY,
    draft_id    TEXT REFERENCES drafts(id),
    decision    TEXT NOT NULL,  -- 'approve' | 'edit' | 'discard'
    decided_at  DATETIME NOT NULL
);

-- Email jobs
CREATE TABLE email_jobs (
    id                  TEXT PRIMARY KEY,
    draft_id            TEXT REFERENCES drafts(id),
    recipient_list_json TEXT NOT NULL,
    recipient_count     INTEGER NOT NULL,
    subject             TEXT NOT NULL,
    body_hash           TEXT NOT NULL,
    status              TEXT NOT NULL,  -- 'drafted' | 'approved' | 'sent' | 'failed'
    sent_at             DATETIME,
    gmail_message_ids   TEXT            -- JSON array
);

-- Immutable action audit trail
CREATE TABLE audit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT REFERENCES sessions(id),
    action_type TEXT NOT NULL,   -- 'read' | 'draft' | 'publish' | 'send' | 'delete'
    module      TEXT NOT NULL,
    input_summary TEXT NOT NULL,
    result      TEXT NOT NULL,   -- 'success' | 'failed' | 'dry_run'
    approved    BOOLEAN NOT NULL,
    timestamp   DATETIME NOT NULL
);

-- Rate limit tracking
CREATE TABLE rate_limits (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    action_type TEXT NOT NULL,
    window_start DATETIME NOT NULL,
    count       INTEGER DEFAULT 0
);

-- Pre-action snapshots for rollback (Playwright actions only)
CREATE TABLE rollback_snapshots (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_log_id INTEGER REFERENCES audit_log(id),
    snapshot_json TEXT NOT NULL,  -- scraped page state before action
    created_at  DATETIME NOT NULL,
    expires_at  DATETIME NOT NULL -- 10 minutes after creation
);
```

---

## G. System Prompt

```
You are the GDG on Campus GJU Admin Assistant — an organizer productivity tool.

IDENTITY: You help one authorized organizer manage their GDG chapter on gdg.community.dev.
You are NOT an autonomous agent. You are a drafting and workflow assistant.

RULES (non-negotiable):
- Never publish, send, or mutate live content without the organizer's explicit approval.
- Always show a full preview before any action that affects the platform or sends email.
- Never guess or invent recipient email addresses.
- Never attempt to access accounts, pages, or data outside the organizer's own dashboard.
- If asked to bypass login, scrape private systems, or perform actions outside your scope, refuse clearly and explain why.
- Label every UI-automated action as [UI AUTOMATION] in your response.
- Label every API-driven action as [OFFICIAL API] in your response.
- If dry-run mode is active, prefix every response with [DRY-RUN].

CAPABILITIES:
- Read and summarize the current dashboard state.
- Draft announcements, events, community posts in GDG style.
- Draft emails for members, speakers, and partners.
- Guide the organizer through the approval and publish workflow.
- Answer questions about chapter management best practices.

TONE: Professional, concise, GDG-community-appropriate. No excessive emoji.
When in doubt, ask a clarifying question rather than assuming.
```

---

## H. UI Design

**Three-panel layout:**

**Left sidebar:**
- Navigation: Chat, Announcements, Events, Emails, Audit Log
- Draft History: last 10 drafts with type, status, timestamp
- Templates: Event Announcement, Speaker Welcome, RSVP Reminder

**Center — Chat panel:**
- Message thread (organizer + agent messages)
- Quick command chips: Draft event, Email registrants, Read dashboard, Show audit log, Enable dry-run
- Text input + Send button
- Status indicator: browser connection + login state
- Dry-run toggle badge (always visible, top bar)

**Right panel (tabbed):**
- **Preview tab** — field-by-field draft preview with red "APPROVAL REQUIRED" banner; three action buttons: `Approve & Publish`, `Edit Draft`, `Discard`. Every UI-automated action labeled `[UI AUTOMATION]`.
- **Activity Log tab** — timestamped, color-coded action history
- **Members tab** — approved registrant list with RSVP counts

**Key UX decisions:**
- Approval panel is a persistent side panel — not a dismissible popup
- `[UI AUTOMATION]` label shown on every Playwright-driven action in the preview
- Dry-run mode toggle always visible in the top bar
- 5-second delay on confirm button for destructive actions (delete/modify live content)

---

## I. Project Structure

```
gdg-admin-assistant/
├── backend/
│   ├── main.py                   # FastAPI app entrypoint
│   ├── config.py                 # Env vars, settings, rate limit constants
│   ├── auth/
│   │   └── gmail_oauth.py        # One-time Gmail OAuth2 authorization flow
│   ├── db/
│   │   ├── models.py             # SQLAlchemy ORM models
│   │   └── database.py           # SQLite connection + session factory
│   ├── modules/
│   │   ├── orchestrator.py       # Intent parsing, workflow routing
│   │   ├── session_manager.py    # Playwright browser lifecycle
│   │   ├── dashboard_reader.py   # [UI AUTOMATION] read-only scraping
│   │   ├── content_generator.py  # Gemini Pro draft generation
│   │   ├── email_drafter.py      # Gmail API draft creation
│   │   ├── action_executor.py    # Gated execution (Playwright + Gmail API)
│   │   ├── approval_gate.py      # Hard approval enforcement
│   │   ├── audit_logger.py       # Append-only SQLite audit log
│   │   ├── safety_guardrail.py   # Rate limits, scope validation, dry-run
│   │   └── context_store.py      # Conversation window + dashboard cache
│   └── routers/
│       ├── chat.py               # POST /chat
│       ├── drafts.py             # GET /drafts, POST /drafts
│       ├── approvals.py          # POST /approve
│       └── audit.py              # GET /audit-log
├── frontend/
│   ├── app/
│   │   ├── page.tsx              # Main dashboard layout
│   │   └── components/
│   │       ├── ChatPanel.tsx     # Chat thread + input
│   │       ├── PreviewPanel.tsx  # Draft preview + approval buttons
│   │       ├── ApprovalModal.tsx # Confirmation for destructive actions
│   │       └── ActivityLog.tsx   # Timestamped action history
│   ├── tailwind.config.ts
│   └── package.json
├── .env.example                  # Required env var template
├── requirements.txt
└── README.md
```

---

## J. Example Commands

1. "Read my dashboard and summarize what's coming up this week"
2. "Create an announcement for next week's AI workshop"
3. "Draft a new event for Android Study Jam on April 25"
4. "Write an event description for a Flutter workshop for beginners"
5. "Email all approved registrants with the updated venue"
6. "Draft a welcome email for our confirmed speakers"
7. "Show me the full email before you send anything"
8. "Do not send anything without my approval"
9. "Enable dry-run mode — I want to test this without publishing"
10. "Show me all drafts from today"
11. "Show me the audit log for the last 24 hours"
12. "Rollback the announcement I just published"
13. "Create an RSVP reminder for tomorrow's event"
14. "Draft a thank-you post for attendees of last week's workshop"
15. "How many approved registrants do we have for the Android Study Jam?"
16. "Write a partner outreach email to the GJU CS department"
17. "Create an event for a Google Cloud study group, every Thursday"
18. "Update the venue for the AI workshop event"
19. "Draft a cancellation notice for this week's session"
20. "Show me what you would send before I approve anything"

---

## K. Deployment

### Local (MVP)

1. Clone repo, create `.env` from `.env.example`
2. Set `GEMINI_API_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
3. Run Gmail OAuth2 flow once: `python backend/auth/gmail_oauth.py`
4. `pip install -r requirements.txt && playwright install chromium`
5. `uvicorn backend.main:app --reload` (backend on port 8000)
6. `cd frontend && npm install && npm run dev` (frontend on port 3000)
7. Open browser to `http://localhost:3000`, click "Open GDG Dashboard" to launch Playwright browser, log in manually

### Cloud (optional, later)

- Deploy FastAPI to **Google Cloud Run** (containerized)
- Frontend to **Vercel** or **Firebase Hosting**
- Secrets via **GCP Secret Manager**
- SQLite → **Cloud SQL (PostgreSQL)** for multi-session support
- OAuth2 redirect URI updated to production domain
- Playwright runs in a headless Cloud Run container with `--no-sandbox`

---

## Constraints and Assumptions

- gdg.community.dev has no public organizer API. All dashboard operations are `[UI AUTOMATION]` and may break on platform UI changes.
- Gmail API requires one-time OAuth2 authorization by the organizer.
- The assistant is single-user (one organizer). Multi-organizer support is out of scope for MVP.
- Rollback is best-effort for UI automation (re-scrape + re-submit); it is not a guaranteed atomic undo.
- Rate limits are configurable in `config.py` but require a code change — not a runtime toggle.
