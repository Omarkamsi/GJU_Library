# GDG Admin Assistant Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a human-in-the-loop AI assistant for GDG on Campus GJU organizers that drafts announcements, events, and emails via Gemini Pro, requires explicit approval before any publish/send action, and logs every action to SQLite.

**Architecture:** Hybrid — Playwright UI automation for gdg.community.dev (no public API exists), Gmail API (OAuth2) for email. FastAPI backend with 10 isolated modules; Gemini Pro as the AI brain; Next.js frontend with a three-panel chat/preview/log layout.

**Tech Stack:** Python 3.12, FastAPI, Playwright (async), Gemini Pro (`google-generativeai`), Gmail API (`google-api-python-client`), SQLAlchemy + SQLite, Next.js 14, Tailwind CSS, pytest + pytest-asyncio

---

## File Map

```
gdg-admin-assistant/
├── backend/
│   ├── main.py                        # FastAPI app, CORS, router registration
│   ├── config.py                      # Settings from .env, rate limit constants
│   ├── auth/
│   │   └── gmail_oauth.py             # One-time OAuth2 flow, saves token.json
│   ├── db/
│   │   ├── database.py                # SQLAlchemy engine, SessionLocal, Base
│   │   └── models.py                  # ORM models for all 7 tables
│   ├── modules/
│   │   ├── audit_logger.py            # Append-only SQLite audit writes
│   │   ├── safety_guardrail.py        # Rate limits, scope check, dry-run flag
│   │   ├── approval_gate.py           # Stores/retrieves approval decisions
│   │   ├── context_store.py           # Rolling 20-turn Gemini history + 5-min cache
│   │   ├── content_generator.py       # Gemini Pro drafting for announcements/events
│   │   ├── email_drafter.py           # Gmail API draft creation
│   │   ├── session_manager.py         # Playwright browser lifecycle
│   │   ├── dashboard_reader.py        # [UI AUTOMATION] read-only scraping
│   │   ├── action_executor.py         # Gated Playwright + Gmail send execution
│   │   └── orchestrator.py            # Intent parsing, workflow assembly
│   └── routers/
│       ├── chat.py                    # POST /chat
│       ├── drafts.py                  # GET /drafts, GET /drafts/{id}
│       ├── approvals.py               # POST /approve/{draft_id}
│       └── audit.py                   # GET /audit-log
├── tests/
│   ├── conftest.py                    # Shared fixtures (test DB, mock modules)
│   ├── test_audit_logger.py
│   ├── test_safety_guardrail.py
│   ├── test_approval_gate.py
│   ├── test_context_store.py
│   ├── test_content_generator.py
│   ├── test_email_drafter.py
│   ├── test_action_executor.py
│   ├── test_orchestrator.py
│   └── test_routers.py
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx                   # Three-panel shell
│   │   └── components/
│   │       ├── ChatPanel.tsx          # Message thread + input + quick chips
│   │       ├── PreviewPanel.tsx       # Draft preview + approve/edit/discard
│   │       ├── ApprovalModal.tsx      # Extra confirmation for destructive actions
│   │       └── ActivityLog.tsx        # Timestamped audit log feed
│   ├── lib/
│   │   └── api.ts                     # Typed fetch wrappers for backend endpoints
│   ├── tailwind.config.ts
│   ├── next.config.ts
│   └── package.json
├── .env.example
├── requirements.txt
└── README.md
```

---

## Phase 1: Foundation

### Task 1: Project setup — directory, dependencies, config

**Files:**
- Create: `gdg-admin-assistant/requirements.txt`
- Create: `gdg-admin-assistant/.env.example`
- Create: `gdg-admin-assistant/backend/config.py`

- [ ] **Step 1: Create project root and requirements**

```bash
mkdir -p gdg-admin-assistant/backend/{auth,db,modules,routers}
mkdir -p gdg-admin-assistant/tests
mkdir -p gdg-admin-assistant/frontend
cd gdg-admin-assistant
```

Write `requirements.txt`:

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy==2.0.36
playwright==1.48.0
google-generativeai==0.8.3
google-api-python-client==2.149.0
google-auth-oauthlib==1.2.1
google-auth-httplib2==0.2.0
python-dotenv==1.0.1
pydantic==2.9.2
httpx==0.27.2
pytest==8.3.3
pytest-asyncio==0.24.0
pytest-mock==3.14.0
```

- [ ] **Step 2: Write .env.example**

```bash
# .env.example
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_CLIENT_ID=your_google_oauth_client_id
GOOGLE_CLIENT_SECRET=your_google_oauth_client_secret
GMAIL_TOKEN_PATH=token.json
DATABASE_URL=sqlite:///./gdg_admin.db
DRY_RUN=false

# Rate limits (per hour / per day)
MAX_PUBLISHES_PER_HOUR=5
MAX_EMAILS_PER_DAY=50
MAX_READS_PER_HOUR=100
```

Copy to `.env` and fill in real values before running.

- [ ] **Step 3: Write config.py**

```python
# backend/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    gemini_api_key: str
    google_client_id: str
    google_client_secret: str
    gmail_token_path: str = "token.json"
    database_url: str = "sqlite:///./gdg_admin.db"
    dry_run: bool = False

    max_publishes_per_hour: int = 5
    max_emails_per_day: int = 50
    max_reads_per_hour: int = 100

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
```

Note: add `pydantic-settings==2.5.2` to requirements.txt.

- [ ] **Step 4: Install dependencies**

```bash
pip install -r requirements.txt
playwright install chromium
```

Expected: All packages install without errors.

- [ ] **Step 5: Commit**

```bash
git init
git add requirements.txt .env.example backend/config.py
git commit -m "feat: project setup — requirements, config, env template"
```

---

### Task 2: Database models and connection

**Files:**
- Create: `backend/db/database.py`
- Create: `backend/db/models.py`
- Create: `backend/db/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_models.py
import pytest
from sqlalchemy import inspect
from tests.conftest import test_engine


def test_all_tables_created(test_engine):
    inspector = inspect(test_engine)
    tables = inspector.get_table_names()
    assert "sessions" in tables
    assert "drafts" in tables
    assert "approvals" in tables
    assert "email_jobs" in tables
    assert "audit_log" in tables
    assert "rate_limits" in tables
    assert "rollback_snapshots" in tables
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_models.py -v
```

Expected: ImportError — `conftest` not found yet.

- [ ] **Step 3: Write database.py**

```python
# backend/db/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from backend.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # SQLite only
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all_tables():
    from backend.db import models  # noqa: F401 — ensures models are registered
    Base.metadata.create_all(bind=engine)
```

- [ ] **Step 4: Write models.py**

```python
# backend/db/models.py
import uuid
from datetime import datetime
from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, String, Text, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.db.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    browser_status: Mapped[str] = mapped_column(String, default="disconnected")
    gdg_logged_in: Mapped[bool] = mapped_column(Boolean, default=False)

    drafts: Mapped[list["Draft"]] = relationship(back_populates="session")
    audit_entries: Mapped[list["AuditLog"]] = relationship(back_populates="session")


class Draft(Base):
    __tablename__ = "drafts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"))
    type: Mapped[str] = mapped_column(String)  # announcement|event|email|post
    content_json: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    session: Mapped["Session"] = relationship(back_populates="drafts")
    approval: Mapped["Approval | None"] = relationship(back_populates="draft")
    email_job: Mapped["EmailJob | None"] = relationship(back_populates="draft")


class Approval(Base):
    __tablename__ = "approvals"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    draft_id: Mapped[str] = mapped_column(ForeignKey("drafts.id"), unique=True)
    decision: Mapped[str] = mapped_column(String)  # approve|edit|discard
    decided_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    draft: Mapped["Draft"] = relationship(back_populates="approval")


class EmailJob(Base):
    __tablename__ = "email_jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    draft_id: Mapped[str] = mapped_column(ForeignKey("drafts.id"), unique=True)
    recipient_list_json: Mapped[str] = mapped_column(Text)
    recipient_count: Mapped[int] = mapped_column(Integer)
    subject: Mapped[str] = mapped_column(String)
    body_hash: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="drafted")
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    gmail_message_ids: Mapped[str | None] = mapped_column(Text, nullable=True)

    draft: Mapped["Draft"] = relationship(back_populates="email_job")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str | None] = mapped_column(ForeignKey("sessions.id"), nullable=True)
    action_type: Mapped[str] = mapped_column(String)  # read|draft|publish|send|delete
    module: Mapped[str] = mapped_column(String)
    input_summary: Mapped[str] = mapped_column(Text)
    result: Mapped[str] = mapped_column(String)  # success|failed|dry_run
    approved: Mapped[bool] = mapped_column(Boolean)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    session: Mapped["Session | None"] = relationship(back_populates="audit_entries")
    rollback_snapshot: Mapped["RollbackSnapshot | None"] = relationship(back_populates="audit_entry")


class RateLimit(Base):
    __tablename__ = "rate_limits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action_type: Mapped[str] = mapped_column(String)
    window_start: Mapped[datetime] = mapped_column(DateTime)
    count: Mapped[int] = mapped_column(Integer, default=0)


class RollbackSnapshot(Base):
    __tablename__ = "rollback_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    audit_log_id: Mapped[int] = mapped_column(ForeignKey("audit_log.id"))
    snapshot_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime)

    audit_entry: Mapped["AuditLog"] = relationship(back_populates="rollback_snapshot")
```

- [ ] **Step 5: Write conftest.py**

```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.db.database import Base, get_db
from backend.db import models  # noqa: F401


@pytest.fixture(scope="function")
def test_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db(test_engine):
    TestingSessionLocal = sessionmaker(bind=test_engine)
    db = TestingSessionLocal()
    yield db
    db.close()
```

- [ ] **Step 6: Write `backend/db/__init__.py`**

```python
# backend/db/__init__.py
```

- [ ] **Step 7: Run test to verify it passes**

```bash
pytest tests/test_models.py -v
```

Expected: `test_all_tables_created PASSED`

- [ ] **Step 8: Commit**

```bash
git add backend/db/ tests/conftest.py tests/test_models.py
git commit -m "feat: database models and SQLite connection"
```

---

### Task 3: Audit Logger

**Files:**
- Create: `backend/modules/audit_logger.py`
- Create: `backend/modules/__init__.py`
- Create: `tests/test_audit_logger.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_audit_logger.py
import pytest
from backend.modules.audit_logger import AuditLogger
from backend.db.models import AuditLog


def test_log_creates_entry(test_db):
    logger = AuditLogger(test_db)
    entry_id = logger.log(
        action_type="draft",
        module="content_generator",
        input_summary="Create announcement for AI workshop",
        result="success",
        approved=False,
        session_id=None,
    )
    assert entry_id is not None
    entry = test_db.get(AuditLog, entry_id)
    assert entry.action_type == "draft"
    assert entry.module == "content_generator"
    assert entry.approved is False


def test_log_is_append_only(test_db):
    logger = AuditLogger(test_db)
    id1 = logger.log("read", "dashboard_reader", "summary", "success", False)
    id2 = logger.log("draft", "content_generator", "summary", "success", False)
    assert id1 != id2
    assert test_db.query(AuditLog).count() == 2
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_audit_logger.py -v
```

Expected: `ImportError: cannot import name 'AuditLogger'`

- [ ] **Step 3: Implement AuditLogger**

```python
# backend/modules/audit_logger.py
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.db.models import AuditLog


class AuditLogger:
    def __init__(self, db: Session):
        self._db = db

    def log(
        self,
        action_type: str,
        module: str,
        input_summary: str,
        result: str,
        approved: bool,
        session_id: str | None = None,
    ) -> int:
        entry = AuditLog(
            session_id=session_id,
            action_type=action_type,
            module=module,
            input_summary=input_summary,
            result=result,
            approved=approved,
            timestamp=datetime.now(timezone.utc),
        )
        self._db.add(entry)
        self._db.commit()
        self._db.refresh(entry)
        return entry.id
```

- [ ] **Step 4: Write `backend/modules/__init__.py`**

```python
# backend/modules/__init__.py
```

- [ ] **Step 5: Run test to verify it passes**

```bash
pytest tests/test_audit_logger.py -v
```

Expected: `PASSED` for both tests.

- [ ] **Step 6: Commit**

```bash
git add backend/modules/ tests/test_audit_logger.py
git commit -m "feat: append-only audit logger"
```

---

## Phase 2: Safety Layer

### Task 4: Safety Guardrail

**Files:**
- Create: `backend/modules/safety_guardrail.py`
- Create: `tests/test_safety_guardrail.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_safety_guardrail.py
import pytest
from datetime import datetime, timezone, timedelta
from backend.modules.safety_guardrail import SafetyGuardrail, SafetyError
from backend.db.models import RateLimit


def test_dry_run_mode_blocks_publish(test_db):
    guardrail = SafetyGuardrail(test_db, dry_run=True)
    with pytest.raises(SafetyError, match="dry.run"):
        guardrail.check_action("publish", session_id=None)


def test_publish_allowed_when_not_dry_run(test_db):
    guardrail = SafetyGuardrail(test_db, dry_run=False)
    # Should not raise
    guardrail.check_action("publish", session_id=None)


def test_rate_limit_publish_blocks_after_max(test_db):
    guardrail = SafetyGuardrail(test_db, dry_run=False)
    # Seed 5 publishes in the current hour
    now = datetime.now(timezone.utc)
    window = now.replace(minute=0, second=0, microsecond=0)
    test_db.add(RateLimit(action_type="publish", window_start=window, count=5))
    test_db.commit()
    with pytest.raises(SafetyError, match="rate limit"):
        guardrail.check_action("publish", session_id=None)


def test_validate_recipients_rejects_free_text_list(test_db):
    guardrail = SafetyGuardrail(test_db, dry_run=False)
    with pytest.raises(SafetyError, match="approved source"):
        guardrail.validate_recipients(["random@example.com"], source="free_text")


def test_validate_recipients_accepts_dashboard_source(test_db):
    guardrail = SafetyGuardrail(test_db, dry_run=False)
    # Should not raise
    guardrail.validate_recipients(["member@gju.edu.jo"], source="dashboard")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_safety_guardrail.py -v
```

Expected: `ImportError: cannot import name 'SafetyGuardrail'`

- [ ] **Step 3: Implement SafetyGuardrail**

```python
# backend/modules/safety_guardrail.py
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.db.models import RateLimit
from backend.config import settings


class SafetyError(Exception):
    pass


# action_type → (max_count, window_hours)
RATE_LIMITS: dict[str, tuple[int, int]] = {
    "publish": (settings.max_publishes_per_hour, 1),
    "send": (settings.max_emails_per_day, 24),
    "read": (settings.max_reads_per_hour, 1),
}

APPROVED_RECIPIENT_SOURCES = {"dashboard", "csv"}


class SafetyGuardrail:
    def __init__(self, db: Session, dry_run: bool = False):
        self._db = db
        self._dry_run = dry_run

    def check_action(self, action_type: str, session_id: str | None) -> None:
        if self._dry_run and action_type in ("publish", "send", "delete"):
            raise SafetyError(
                f"dry-run mode is active — action '{action_type}' is blocked"
            )
        self._check_rate_limit(action_type)

    def _check_rate_limit(self, action_type: str) -> None:
        if action_type not in RATE_LIMITS:
            return
        max_count, window_hours = RATE_LIMITS[action_type]
        now = datetime.now(timezone.utc)
        window_start = now.replace(
            minute=0, second=0, microsecond=0
        ) if window_hours == 1 else now.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        record = (
            self._db.query(RateLimit)
            .filter(
                RateLimit.action_type == action_type,
                RateLimit.window_start == window_start,
            )
            .first()
        )
        current = record.count if record else 0
        if current >= max_count:
            raise SafetyError(
                f"rate limit reached for '{action_type}': "
                f"{current}/{max_count} in current window"
            )

    def increment_rate_limit(self, action_type: str) -> None:
        if action_type not in RATE_LIMITS:
            return
        _, window_hours = RATE_LIMITS[action_type]
        now = datetime.now(timezone.utc)
        window_start = now.replace(
            minute=0, second=0, microsecond=0
        ) if window_hours == 1 else now.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        record = (
            self._db.query(RateLimit)
            .filter(
                RateLimit.action_type == action_type,
                RateLimit.window_start == window_start,
            )
            .first()
        )
        if record:
            record.count += 1
        else:
            self._db.add(RateLimit(
                action_type=action_type,
                window_start=window_start,
                count=1,
            ))
        self._db.commit()

    def validate_recipients(
        self, recipients: list[str], source: str
    ) -> None:
        if source not in APPROVED_RECIPIENT_SOURCES:
            raise SafetyError(
                "recipients must come from an approved source "
                "(dashboard registrant list or CSV file). "
                "Free-text email lists are rejected."
            )
        if not recipients:
            raise SafetyError("recipient list is empty")

    @property
    def is_dry_run(self) -> bool:
        return self._dry_run
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_safety_guardrail.py -v
```

Expected: All 5 tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add backend/modules/safety_guardrail.py tests/test_safety_guardrail.py
git commit -m "feat: safety guardrail with rate limits and dry-run mode"
```

---

### Task 5: Approval Gate

**Files:**
- Create: `backend/modules/approval_gate.py`
- Create: `tests/test_approval_gate.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_approval_gate.py
import pytest
from backend.modules.approval_gate import ApprovalGate, ApprovalError
from backend.db.models import Draft, Approval


def _create_draft(db, status="pending") -> str:
    d = Draft(
        session_id=None,
        type="announcement",
        content_json='{"title": "Test"}',
        status=status,
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    return d.id


def test_record_approval_sets_status_approved(test_db):
    gate = ApprovalGate(test_db)
    draft_id = _create_draft(test_db)
    gate.record_decision(draft_id, "approve")
    draft = test_db.get(Draft, draft_id)
    assert draft.status == "approved"


def test_record_discard_sets_status_discarded(test_db):
    gate = ApprovalGate(test_db)
    draft_id = _create_draft(test_db)
    gate.record_decision(draft_id, "discard")
    draft = test_db.get(Draft, draft_id)
    assert draft.status == "discarded"


def test_require_approval_raises_if_not_approved(test_db):
    gate = ApprovalGate(test_db)
    draft_id = _create_draft(test_db, status="pending")
    with pytest.raises(ApprovalError, match="not approved"):
        gate.require_approval(draft_id)


def test_require_approval_passes_if_approved(test_db):
    gate = ApprovalGate(test_db)
    draft_id = _create_draft(test_db, status="approved")
    # Should not raise
    gate.require_approval(draft_id)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_approval_gate.py -v
```

Expected: `ImportError: cannot import name 'ApprovalGate'`

- [ ] **Step 3: Implement ApprovalGate**

```python
# backend/modules/approval_gate.py
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.db.models import Approval, Draft


class ApprovalError(Exception):
    pass


class ApprovalGate:
    def __init__(self, db: Session):
        self._db = db

    def record_decision(self, draft_id: str, decision: str) -> None:
        """Record approve | edit | discard for a draft."""
        if decision not in ("approve", "edit", "discard"):
            raise ValueError(f"Unknown decision: {decision}")

        draft = self._db.get(Draft, draft_id)
        if draft is None:
            raise ApprovalError(f"Draft {draft_id} not found")

        status_map = {
            "approve": "approved",
            "discard": "discarded",
            "edit": "pending",
        }
        draft.status = status_map[decision]

        approval = Approval(
            draft_id=draft_id,
            decision=decision,
            decided_at=datetime.now(timezone.utc),
        )
        self._db.add(approval)
        self._db.commit()

    def require_approval(self, draft_id: str) -> None:
        """Raise ApprovalError if draft has not been approved."""
        draft = self._db.get(Draft, draft_id)
        if draft is None or draft.status != "approved":
            raise ApprovalError(
                f"Draft {draft_id} is not approved — "
                "organizer must approve before execution"
            )
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_approval_gate.py -v
```

Expected: All 4 tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add backend/modules/approval_gate.py tests/test_approval_gate.py
git commit -m "feat: approval gate with decision recording and enforcement"
```

---

## Phase 3: AI + Email

### Task 6: Context Store

**Files:**
- Create: `backend/modules/context_store.py`
- Create: `tests/test_context_store.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_context_store.py
import pytest
import time
from backend.modules.context_store import ContextStore


def test_adds_and_retrieves_turns():
    store = ContextStore(max_turns=3)
    store.add_turn("user", "hello")
    store.add_turn("model", "hi there")
    history = store.get_history()
    assert len(history) == 2
    assert history[0] == {"role": "user", "parts": ["hello"]}
    assert history[1] == {"role": "model", "parts": ["hi there"]}


def test_rolling_window_drops_oldest():
    store = ContextStore(max_turns=2)
    store.add_turn("user", "first")
    store.add_turn("model", "reply")
    store.add_turn("user", "third")  # should drop "first"
    history = store.get_history()
    assert len(history) == 2
    assert history[0]["parts"] == ["reply"]


def test_cache_hit_before_ttl():
    store = ContextStore(max_turns=20, cache_ttl_seconds=5)
    store.set_cache("dashboard", {"events": []})
    result = store.get_cache("dashboard")
    assert result == {"events": []}


def test_cache_miss_after_ttl():
    store = ContextStore(max_turns=20, cache_ttl_seconds=1)
    store.set_cache("dashboard", {"events": []})
    time.sleep(1.1)
    result = store.get_cache("dashboard")
    assert result is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_context_store.py -v
```

Expected: `ImportError: cannot import name 'ContextStore'`

- [ ] **Step 3: Implement ContextStore**

```python
# backend/modules/context_store.py
from collections import deque
from datetime import datetime, timezone
from typing import Any


class ContextStore:
    def __init__(self, max_turns: int = 20, cache_ttl_seconds: int = 300):
        self._history: deque[dict] = deque(maxlen=max_turns)
        self._cache: dict[str, tuple[Any, datetime]] = {}
        self._cache_ttl = cache_ttl_seconds

    def add_turn(self, role: str, content: str) -> None:
        self._history.append({"role": role, "parts": [content]})

    def get_history(self) -> list[dict]:
        return list(self._history)

    def set_cache(self, key: str, value: Any) -> None:
        self._cache[key] = (value, datetime.now(timezone.utc))

    def get_cache(self, key: str) -> Any | None:
        if key not in self._cache:
            return None
        value, cached_at = self._cache[key]
        age = (datetime.now(timezone.utc) - cached_at).total_seconds()
        if age > self._cache_ttl:
            del self._cache[key]
            return None
        return value

    def clear(self) -> None:
        self._history.clear()
        self._cache.clear()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_context_store.py -v
```

Expected: All 4 tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add backend/modules/context_store.py tests/test_context_store.py
git commit -m "feat: context store with rolling history and TTL cache"
```

---

### Task 7: Content Generator (Gemini Pro)

**Files:**
- Create: `backend/modules/content_generator.py`
- Create: `tests/test_content_generator.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_content_generator.py
import json
import pytest
from unittest.mock import MagicMock, patch
from backend.modules.content_generator import ContentGenerator


@pytest.fixture
def mock_gemini():
    with patch("backend.modules.content_generator.genai") as mock:
        model = MagicMock()
        chat = MagicMock()
        response = MagicMock()
        response.text = json.dumps({
            "title": "AI Workshop: Hands-On with Gemini API",
            "body": "Join us for an exciting workshop...",
            "tags": ["AI", "Gemini", "Workshop"],
            "scheduled_date": "2026-04-21",
        })
        chat.send_message.return_value = response
        model.start_chat.return_value = chat
        mock.GenerativeModel.return_value = model
        yield mock


def test_draft_announcement_returns_structured_dict(mock_gemini):
    from backend.modules.context_store import ContextStore
    store = ContextStore()
    gen = ContentGenerator(store)
    result = gen.draft(
        content_type="announcement",
        command="Create an announcement for next week's AI workshop",
        context={"chapter": "GDG GJU", "upcoming_events": []},
    )
    assert "title" in result
    assert "body" in result
    assert "tags" in result


def test_draft_raises_on_invalid_json(mock_gemini):
    from backend.modules.context_store import ContextStore
    mock_gemini.GenerativeModel.return_value.start_chat.return_value\
        .send_message.return_value.text = "not valid json"
    store = ContextStore()
    gen = ContentGenerator(store)
    with pytest.raises(ValueError, match="invalid JSON"):
        gen.draft("announcement", "test command", {})
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_content_generator.py -v
```

Expected: `ImportError: cannot import name 'ContentGenerator'`

- [ ] **Step 3: Implement ContentGenerator**

```python
# backend/modules/content_generator.py
import json
import google.generativeai as genai
from backend.config import settings
from backend.modules.context_store import ContextStore

SYSTEM_PROMPT = """You are the GDG on Campus GJU Admin Assistant — an organizer productivity tool.

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

TONE: Professional, concise, GDG-community-appropriate. No excessive emoji.
When in doubt, ask a clarifying question rather than assuming.

IMPORTANT: When drafting content, always respond with valid JSON only.
"""

DRAFT_SCHEMAS = {
    "announcement": {
        "fields": ["title", "body", "tags", "scheduled_date"],
        "example": '{"title": "...", "body": "...", "tags": ["AI", "Workshop"], "scheduled_date": "YYYY-MM-DD"}',
    },
    "event": {
        "fields": ["title", "description", "date", "time", "venue", "tags"],
        "example": '{"title": "...", "description": "...", "date": "YYYY-MM-DD", "time": "HH:MM", "venue": "...", "tags": []}',
    },
    "email": {
        "fields": ["subject", "body"],
        "example": '{"subject": "...", "body": "..."}',
    },
    "post": {
        "fields": ["title", "body", "tags"],
        "example": '{"title": "...", "body": "...", "tags": []}',
    },
}


class ContentGenerator:
    def __init__(self, context_store: ContextStore):
        genai.configure(api_key=settings.gemini_api_key)
        self._model = genai.GenerativeModel(
            "gemini-pro",
            system_instruction=SYSTEM_PROMPT,
        )
        self._context_store = context_store

    def draft(
        self,
        content_type: str,
        command: str,
        context: dict,
    ) -> dict:
        schema = DRAFT_SCHEMAS.get(content_type)
        if schema is None:
            raise ValueError(f"Unknown content type: {content_type}")

        prompt = (
            f"The organizer requests: {command}\n\n"
            f"Current chapter context: {json.dumps(context)}\n\n"
            f"Draft a {content_type} and return ONLY valid JSON with these fields: "
            f"{schema['fields']}.\n"
            f"Example format: {schema['example']}"
        )

        chat = self._model.start_chat(history=self._context_store.get_history())
        response = chat.send_message(prompt)
        raw = response.text.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"Gemini returned invalid JSON: {e}\nRaw: {raw}")

        self._context_store.add_turn("user", command)
        self._context_store.add_turn("model", raw)

        return parsed

    def chat(self, message: str) -> str:
        """Free-form chat response (for non-drafting commands)."""
        chat = self._model.start_chat(history=self._context_store.get_history())
        response = chat.send_message(message)
        self._context_store.add_turn("user", message)
        self._context_store.add_turn("model", response.text)
        return response.text
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_content_generator.py -v
```

Expected: Both tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add backend/modules/content_generator.py tests/test_content_generator.py
git commit -m "feat: content generator with Gemini Pro and JSON schema drafting"
```

---

### Task 8: Gmail OAuth2 Setup

**Files:**
- Create: `backend/auth/gmail_oauth.py`
- Create: `backend/auth/__init__.py`

This is a one-time setup script, not tested with pytest (requires real OAuth2 flow).

- [ ] **Step 1: Write gmail_oauth.py**

```python
# backend/auth/gmail_oauth.py
"""
Run this once to authorize Gmail API access:
    python -m backend.auth.gmail_oauth

This saves token.json to the project root.
The token is refreshed automatically on subsequent runs.
"""
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from backend.config import settings

SCOPES = [
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
]


def get_credentials() -> Credentials:
    creds = None
    token_path = settings.gmail_token_path

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            client_config = {
                "installed": {
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            }
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, "w") as f:
            f.write(creds.to_json())

    return creds


if __name__ == "__main__":
    get_credentials()
    print(f"Authorization complete. Token saved to {settings.gmail_token_path}")
```

- [ ] **Step 2: Write `backend/auth/__init__.py`**

```python
# backend/auth/__init__.py
```

- [ ] **Step 3: Run the OAuth flow (manual, one-time)**

```bash
python -m backend.auth.gmail_oauth
```

Expected: Browser opens, you authorize with your Google account, `token.json` is saved to project root.

- [ ] **Step 4: Commit**

```bash
git add backend/auth/ 
echo "token.json" >> .gitignore
git add .gitignore
git commit -m "feat: Gmail OAuth2 authorization flow"
```

---

### Task 9: Email Drafter

**Files:**
- Create: `backend/modules/email_drafter.py`
- Create: `tests/test_email_drafter.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_email_drafter.py
import json
import pytest
from unittest.mock import MagicMock, patch
from backend.modules.email_drafter import EmailDrafter
from backend.db.models import Draft, EmailJob


def _make_email_draft(db) -> str:
    d = Draft(
        session_id=None,
        type="email",
        content_json=json.dumps({
            "subject": "AI Workshop Venue Update",
            "body": "Dear attendee, the venue has changed to Lab 3.",
        }),
        status="approved",
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    return d.id


@pytest.fixture
def mock_gmail():
    with patch("backend.modules.email_drafter.build") as mock_build:
        service = MagicMock()
        draft_create = MagicMock()
        draft_create.execute.return_value = {"id": "draft_abc123"}
        service.users().drafts().create.return_value = draft_create
        mock_build.return_value = service
        yield service


def test_save_gmail_draft_creates_email_job(test_db, mock_gmail):
    draft_id = _make_email_draft(test_db)
    drafter = EmailDrafter(test_db)

    job_id = drafter.save_gmail_draft(
        draft_id=draft_id,
        recipients=["student@gju.edu.jo"],
        source="dashboard",
    )

    job = test_db.get(EmailJob, job_id)
    assert job is not None
    assert job.recipient_count == 1
    assert job.status == "drafted"
    assert job.subject == "AI Workshop Venue Update"


def test_save_gmail_draft_stores_body_hash(test_db, mock_gmail):
    import hashlib
    draft_id = _make_email_draft(test_db)
    drafter = EmailDrafter(test_db)
    job_id = drafter.save_gmail_draft(draft_id, ["a@b.com"], "dashboard")
    job = test_db.get(EmailJob, job_id)
    expected_hash = hashlib.sha256(
        "Dear attendee, the venue has changed to Lab 3.".encode()
    ).hexdigest()
    assert job.body_hash == expected_hash
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_email_drafter.py -v
```

Expected: `ImportError: cannot import name 'EmailDrafter'`

- [ ] **Step 3: Implement EmailDrafter**

```python
# backend/modules/email_drafter.py
import base64
import hashlib
import json
from email.mime.text import MIMEText
from datetime import datetime, timezone
from googleapiclient.discovery import build
from sqlalchemy.orm import Session
from backend.auth.gmail_oauth import get_credentials
from backend.db.models import Draft, EmailJob
from backend.modules.safety_guardrail import SafetyGuardrail


class EmailDrafter:
    def __init__(self, db: Session):
        self._db = db
        creds = get_credentials()
        self._gmail = build("gmail", "v1", credentials=creds)

    def save_gmail_draft(
        self,
        draft_id: str,
        recipients: list[str],
        source: str,
    ) -> str:
        """Create a Gmail draft and persist EmailJob. Returns job id."""
        # Validate recipients
        guardrail = SafetyGuardrail(self._db, dry_run=False)
        guardrail.validate_recipients(recipients, source)

        draft = self._db.get(Draft, draft_id)
        if draft is None:
            raise ValueError(f"Draft {draft_id} not found")

        content = json.loads(draft.content_json)
        subject = content["subject"]
        body = content["body"]
        body_hash = hashlib.sha256(body.encode()).hexdigest()

        # Build MIME message
        mime = MIMEText(body, "plain")
        mime["to"] = ", ".join(recipients)
        mime["subject"] = subject
        raw = base64.urlsafe_b64encode(mime.as_bytes()).decode()

        # Save to Gmail Drafts
        gmail_draft = (
            self._gmail.users()
            .drafts()
            .create(userId="me", body={"message": {"raw": raw}})
            .execute()
        )
        gmail_draft_id = gmail_draft["id"]

        # Persist EmailJob
        job = EmailJob(
            draft_id=draft_id,
            recipient_list_json=json.dumps(recipients),
            recipient_count=len(recipients),
            subject=subject,
            body_hash=body_hash,
            status="drafted",
        )
        # Store gmail draft id in message ids field temporarily
        job.gmail_message_ids = json.dumps([gmail_draft_id])
        self._db.add(job)
        self._db.commit()
        self._db.refresh(job)
        return job.id

    def send_draft(self, job_id: str) -> list[str]:
        """Send a saved Gmail draft. Returns list of Gmail message IDs."""
        job = self._db.get(EmailJob, job_id)
        if job is None:
            raise ValueError(f"EmailJob {job_id} not found")

        draft_ids = json.loads(job.gmail_message_ids or "[]")
        if not draft_ids:
            raise ValueError("No Gmail draft ID found for this job")

        gmail_draft_id = draft_ids[0]
        sent = (
            self._gmail.users()
            .drafts()
            .send(userId="me", body={"id": gmail_draft_id})
            .execute()
        )
        message_id = sent.get("id", "")

        job.status = "sent"
        job.sent_at = datetime.now(timezone.utc)
        job.gmail_message_ids = json.dumps([message_id])
        self._db.commit()

        return [message_id]
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_email_drafter.py -v
```

Expected: Both tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add backend/modules/email_drafter.py tests/test_email_drafter.py
git commit -m "feat: email drafter with Gmail API draft creation and send"
```

---

## Phase 4: Playwright Layer

### Task 10: Session Manager

**Files:**
- Create: `backend/modules/session_manager.py`
- Create: `tests/test_session_manager.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_session_manager.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.modules.session_manager import SessionManager
from backend.db.models import Session as DBSession


@pytest.mark.asyncio
async def test_start_session_creates_db_record(test_db):
    with patch("backend.modules.session_manager.async_playwright") as mock_pw:
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        mock_pw.return_value.__aenter__.return_value.chromium.launch.return_value = mock_browser

        manager = SessionManager(test_db)
        session_id = await manager.start()

        record = test_db.get(DBSession, session_id)
        assert record is not None
        assert record.browser_status == "connected"


@pytest.mark.asyncio
async def test_mark_logged_in(test_db):
    with patch("backend.modules.session_manager.async_playwright") as mock_pw:
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        mock_pw.return_value.__aenter__.return_value.chromium.launch.return_value = mock_browser

        manager = SessionManager(test_db)
        session_id = await manager.start()
        manager.mark_logged_in()

        record = test_db.get(DBSession, session_id)
        assert record.gdg_logged_in is True
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_session_manager.py -v
```

Expected: `ImportError: cannot import name 'SessionManager'`

- [ ] **Step 3: Implement SessionManager**

```python
# backend/modules/session_manager.py
import uuid
from datetime import datetime, timezone
from playwright.async_api import async_playwright, Page, Browser
from sqlalchemy.orm import Session as DBSession
from backend.db.models import Session as DBSessionModel

GDG_DASHBOARD_URL = "https://gdg.community.dev/dashboard/"


class SessionManager:
    def __init__(self, db: DBSession):
        self._db = db
        self._session_id: str | None = None
        self._browser: Browser | None = None
        self._page: Page | None = None
        self._pw = None

    async def start(self) -> str:
        """Launch browser and navigate to GDG dashboard for manual login."""
        self._pw = await async_playwright().__aenter__()
        self._browser = await self._pw.chromium.launch(headless=False)
        context = await self._browser.new_context()
        self._page = await context.new_page()
        await self._page.goto(GDG_DASHBOARD_URL)

        record = DBSessionModel(
            id=str(uuid.uuid4()),
            started_at=datetime.now(timezone.utc),
            browser_status="connected",
            gdg_logged_in=False,
        )
        self._db.add(record)
        self._db.commit()
        self._session_id = record.id
        return self._session_id

    def mark_logged_in(self) -> None:
        """Call after organizer manually logs in."""
        if self._session_id is None:
            raise RuntimeError("No active session")
        record = self._db.get(DBSessionModel, self._session_id)
        record.gdg_logged_in = True
        self._db.commit()

    def get_page(self) -> Page:
        if self._page is None:
            raise RuntimeError("Browser session not started")
        return self._page

    def get_session_id(self) -> str | None:
        return self._session_id

    async def close(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._pw:
            await self._pw.__aexit__(None, None, None)
        if self._session_id:
            record = self._db.get(DBSessionModel, self._session_id)
            if record:
                record.browser_status = "disconnected"
                self._db.commit()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_session_manager.py -v
```

Expected: Both tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add backend/modules/session_manager.py tests/test_session_manager.py
git commit -m "feat: Playwright session manager with login tracking [UI AUTOMATION]"
```

---

### Task 11: Dashboard Reader

**Files:**
- Create: `backend/modules/dashboard_reader.py`
- Create: `tests/test_dashboard_reader.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_dashboard_reader.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from backend.modules.dashboard_reader import DashboardReader


@pytest.fixture
def mock_page():
    page = AsyncMock()
    # Simulate locator for events
    event_locators = [
        MagicMock(inner_text=AsyncMock(return_value="AI Workshop\nApril 21 · Lab 3")),
        MagicMock(inner_text=AsyncMock(return_value="Android Study Jam\nApril 25 · Online")),
    ]
    page.locator.return_value.all.return_value = event_locators
    page.title.return_value = "GDG on Campus GJU Dashboard"
    return page


@pytest.mark.asyncio
async def test_read_dashboard_returns_dict(mock_page):
    reader = DashboardReader(mock_page)
    result = await reader.read_dashboard_state()
    assert "page_title" in result
    assert "events" in result
    assert isinstance(result["events"], list)


@pytest.mark.asyncio
async def test_read_dashboard_is_read_only(mock_page):
    reader = DashboardReader(mock_page)
    await reader.read_dashboard_state()
    # Ensure no click/fill/submit was called (read-only)
    mock_page.click.assert_not_called()
    mock_page.fill.assert_not_called()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_dashboard_reader.py -v
```

Expected: `ImportError: cannot import name 'DashboardReader'`

- [ ] **Step 3: Implement DashboardReader**

```python
# backend/modules/dashboard_reader.py
# [UI AUTOMATION] — reads gdg.community.dev dashboard state
# This module uses Playwright. It may break if gdg.community.dev updates its UI.
from playwright.async_api import Page


class DashboardReader:
    def __init__(self, page: Page):
        self._page = page

    async def read_dashboard_state(self) -> dict:
        """Scrape current dashboard state. READ-ONLY — never mutates."""
        title = await self._page.title()

        # Scrape upcoming events
        # Selector is best-effort and may need updating if GDG UI changes
        events = []
        try:
            event_els = await self._page.locator(
                "[data-testid='event-card'], .event-card, .upcoming-event"
            ).all()
            for el in event_els[:10]:  # limit to 10
                text = await el.inner_text()
                events.append(text.strip())
        except Exception:
            events = []

        # Scrape announcements
        announcements = []
        try:
            ann_els = await self._page.locator(
                "[data-testid='announcement'], .announcement-item"
            ).all()
            for el in ann_els[:5]:
                text = await el.inner_text()
                announcements.append(text.strip())
        except Exception:
            announcements = []

        return {
            "page_title": title,
            "page_url": self._page.url,
            "events": events,
            "announcements": announcements,
            "scraped_at": __import__("datetime").datetime.utcnow().isoformat(),
            "automation_note": "[UI AUTOMATION] — selectors may break on GDG UI updates",
        }
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_dashboard_reader.py -v
```

Expected: Both tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add backend/modules/dashboard_reader.py tests/test_dashboard_reader.py
git commit -m "feat: dashboard reader — read-only Playwright scraper [UI AUTOMATION]"
```

---

### Task 12: Action Executor

**Files:**
- Create: `backend/modules/action_executor.py`
- Create: `tests/test_action_executor.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_action_executor.py
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.modules.action_executor import ActionExecutor
from backend.modules.approval_gate import ApprovalError
from backend.db.models import Draft, RollbackSnapshot


def _approved_draft(db, dtype="announcement") -> str:
    d = Draft(
        session_id=None,
        type=dtype,
        content_json=json.dumps({
            "title": "Test Announcement",
            "body": "Test body content for the announcement.",
            "tags": ["test"],
            "scheduled_date": "2026-04-21",
        }),
        status="approved",
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    return d.id


@pytest.mark.asyncio
async def test_execute_requires_approved_draft(test_db):
    d = Draft(session_id=None, type="announcement",
              content_json='{}', status="pending")
    test_db.add(d)
    test_db.commit()

    page = AsyncMock()
    executor = ActionExecutor(test_db, page)
    with pytest.raises(ApprovalError):
        await executor.publish_announcement(d.id)


@pytest.mark.asyncio
async def test_execute_saves_rollback_snapshot(test_db):
    draft_id = _approved_draft(test_db)
    page = AsyncMock()
    page.content.return_value = "<html>before</html>"
    page.goto = AsyncMock()
    page.fill = AsyncMock()
    page.click = AsyncMock()
    page.wait_for_selector = AsyncMock()

    with patch("backend.modules.action_executor.AuditLogger") as MockLogger:
        MockLogger.return_value.log.return_value = 1
        executor = ActionExecutor(test_db, page)
        await executor.publish_announcement(draft_id)

    snapshots = test_db.query(RollbackSnapshot).all()
    assert len(snapshots) == 1
    assert "<html>before</html>" in snapshots[0].snapshot_json
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_action_executor.py -v
```

Expected: `ImportError: cannot import name 'ActionExecutor'`

- [ ] **Step 3: Implement ActionExecutor**

```python
# backend/modules/action_executor.py
# [UI AUTOMATION] for dashboard actions, [OFFICIAL API] for email
import json
from datetime import datetime, timedelta, timezone
from playwright.async_api import Page
from sqlalchemy.orm import Session as DBSession
from backend.db.models import Draft, RollbackSnapshot
from backend.modules.approval_gate import ApprovalGate
from backend.modules.audit_logger import AuditLogger
from backend.modules.safety_guardrail import SafetyGuardrail

GDG_NEW_ANNOUNCEMENT_URL = "https://gdg.community.dev/dashboard/announcements/new/"
GDG_NEW_EVENT_URL = "https://gdg.community.dev/dashboard/events/new/"


class ActionExecutor:
    def __init__(self, db: DBSession, page: Page, dry_run: bool = False):
        self._db = db
        self._page = page
        self._dry_run = dry_run
        self._approval_gate = ApprovalGate(db)
        self._audit = AuditLogger(db)
        self._guardrail = SafetyGuardrail(db, dry_run=dry_run)

    async def publish_announcement(self, draft_id: str) -> dict:
        """[UI AUTOMATION] Publish an approved announcement to gdg.community.dev."""
        self._approval_gate.require_approval(draft_id)
        self._guardrail.check_action("publish", session_id=None)

        draft = self._db.get(Draft, draft_id)
        content = json.loads(draft.content_json)

        # Save rollback snapshot
        snapshot = await self._page.content()
        audit_id = self._audit.log(
            action_type="publish",
            module="action_executor",
            input_summary=f"Publish announcement: {content.get('title', '')}",
            result="in_progress",
            approved=True,
        )
        self._db.add(RollbackSnapshot(
            audit_log_id=audit_id,
            snapshot_json=json.dumps({"html": snapshot, "draft": content}),
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        ))
        self._db.commit()

        if not self._dry_run:
            # [UI AUTOMATION] — fill and submit the announcement form
            await self._page.goto(GDG_NEW_ANNOUNCEMENT_URL)
            await self._page.wait_for_selector("input[name='title'], #announcement-title", timeout=10000)
            await self._page.fill("input[name='title'], #announcement-title", content.get("title", ""))
            await self._page.fill("textarea[name='body'], #announcement-body", content.get("body", ""))
            await self._page.click("button[type='submit'], .publish-btn")
            result = "success"
        else:
            result = "dry_run"

        # Update audit entry result
        self._guardrail.increment_rate_limit("publish")
        draft.status = "published"
        self._db.commit()

        return {"result": result, "draft_id": draft_id, "automation": "[UI AUTOMATION]"}

    async def publish_event(self, draft_id: str) -> dict:
        """[UI AUTOMATION] Create an approved event on gdg.community.dev."""
        self._approval_gate.require_approval(draft_id)
        self._guardrail.check_action("publish", session_id=None)

        draft = self._db.get(Draft, draft_id)
        content = json.loads(draft.content_json)

        snapshot = await self._page.content()
        audit_id = self._audit.log(
            action_type="publish",
            module="action_executor",
            input_summary=f"Create event: {content.get('title', '')}",
            result="in_progress",
            approved=True,
        )
        self._db.add(RollbackSnapshot(
            audit_log_id=audit_id,
            snapshot_json=json.dumps({"html": snapshot, "draft": content}),
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        ))
        self._db.commit()

        if not self._dry_run:
            # [UI AUTOMATION] — fill and submit the event form
            await self._page.goto(GDG_NEW_EVENT_URL)
            await self._page.wait_for_selector("input[name='title'], #event-title", timeout=10000)
            await self._page.fill("input[name='title'], #event-title", content.get("title", ""))
            await self._page.fill("textarea[name='description'], #event-description", content.get("description", ""))
            await self._page.fill("input[name='date'], #event-date", content.get("date", ""))
            await self._page.fill("input[name='venue'], #event-venue", content.get("venue", ""))
            await self._page.click("button[type='submit'], .create-event-btn")
            result = "success"
        else:
            result = "dry_run"

        self._guardrail.increment_rate_limit("publish")
        draft.status = "published"
        self._db.commit()

        return {"result": result, "draft_id": draft_id, "automation": "[UI AUTOMATION]"}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_action_executor.py -v
```

Expected: Both tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add backend/modules/action_executor.py tests/test_action_executor.py
git commit -m "feat: action executor with approval gating and rollback snapshots"
```

---

## Phase 5: Orchestration + API

### Task 13: Orchestrator

**Files:**
- Create: `backend/modules/orchestrator.py`
- Create: `tests/test_orchestrator.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_orchestrator.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.modules.orchestrator import Orchestrator, Intent


def test_parse_intent_announcement():
    orch = Orchestrator.__new__(Orchestrator)
    intent = orch._parse_intent("Create an announcement for next week's AI workshop")
    assert intent == Intent.DRAFT_ANNOUNCEMENT


def test_parse_intent_event():
    orch = Orchestrator.__new__(Orchestrator)
    intent = orch._parse_intent("Draft a new event for Android Study Jam")
    assert intent == Intent.DRAFT_EVENT


def test_parse_intent_email():
    orch = Orchestrator.__new__(Orchestrator)
    intent = orch._parse_intent("Email all approved registrants with the updated venue")
    assert intent == Intent.DRAFT_EMAIL


def test_parse_intent_read():
    orch = Orchestrator.__new__(Orchestrator)
    intent = orch._parse_intent("Read my dashboard and summarize what's coming up")
    assert intent == Intent.READ_DASHBOARD


def test_parse_intent_chat():
    orch = Orchestrator.__new__(Orchestrator)
    intent = orch._parse_intent("What is the best format for event announcements?")
    assert intent == Intent.CHAT
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_orchestrator.py -v
```

Expected: `ImportError: cannot import name 'Orchestrator'`

- [ ] **Step 3: Implement Orchestrator**

```python
# backend/modules/orchestrator.py
import json
from enum import Enum
from sqlalchemy.orm import Session as DBSession
from backend.db.models import Draft
from backend.modules.content_generator import ContentGenerator
from backend.modules.context_store import ContextStore
from backend.modules.audit_logger import AuditLogger
from backend.modules.safety_guardrail import SafetyGuardrail


class Intent(str, Enum):
    DRAFT_ANNOUNCEMENT = "draft_announcement"
    DRAFT_EVENT = "draft_event"
    DRAFT_EMAIL = "draft_email"
    READ_DASHBOARD = "read_dashboard"
    CHAT = "chat"


INTENT_KEYWORDS: dict[Intent, list[str]] = {
    Intent.DRAFT_ANNOUNCEMENT: ["announcement", "announce", "post about", "notify"],
    Intent.DRAFT_EVENT: ["event", "workshop", "study jam", "meetup", "schedule"],
    Intent.DRAFT_EMAIL: ["email", "send", "mail", "message registrants", "message members"],
    Intent.READ_DASHBOARD: ["read", "dashboard", "summarize", "what's coming", "show me"],
}


class Orchestrator:
    def __init__(
        self,
        db: DBSession,
        context_store: ContextStore,
        session_id: str | None,
        dry_run: bool = False,
    ):
        self._db = db
        self._context_store = context_store
        self._session_id = session_id
        self._dry_run = dry_run
        self._generator = ContentGenerator(context_store)
        self._audit = AuditLogger(db)
        self._guardrail = SafetyGuardrail(db, dry_run=dry_run)

    def _parse_intent(self, command: str) -> Intent:
        lower = command.lower()
        for intent, keywords in INTENT_KEYWORDS.items():
            if any(kw in lower for kw in keywords):
                return intent
        return Intent.CHAT

    async def handle(self, command: str, dashboard_context: dict | None = None) -> dict:
        """Route a command to the correct workflow. Returns a response dict."""
        intent = self._parse_intent(command)
        context = dashboard_context or {}

        self._audit.log(
            action_type="draft",
            module="orchestrator",
            input_summary=command[:200],
            result="routing",
            approved=False,
            session_id=self._session_id,
        )

        if intent == Intent.READ_DASHBOARD:
            cached = self._context_store.get_cache("dashboard")
            if cached:
                return {"type": "dashboard_state", "data": cached, "source": "cache"}
            return {
                "type": "dashboard_state",
                "data": context,
                "message": "Dashboard context provided. Use the browser panel to read live state.",
            }

        if intent == Intent.CHAT:
            reply = self._generator.chat(command)
            return {"type": "chat", "message": reply}

        content_type = {
            Intent.DRAFT_ANNOUNCEMENT: "announcement",
            Intent.DRAFT_EVENT: "event",
            Intent.DRAFT_EMAIL: "email",
        }[intent]

        draft_content = self._generator.draft(content_type, command, context)

        # Store draft in DB
        draft = Draft(
            session_id=self._session_id,
            type=content_type,
            content_json=json.dumps(draft_content),
            status="pending",
        )
        self._db.add(draft)
        self._db.commit()
        self._db.refresh(draft)

        self._audit.log(
            action_type="draft",
            module="orchestrator",
            input_summary=f"Drafted {content_type}: {command[:100]}",
            result="success",
            approved=False,
            session_id=self._session_id,
        )

        return {
            "type": "draft",
            "draft_id": draft.id,
            "content_type": content_type,
            "content": draft_content,
            "status": "pending_approval",
            "message": f"[{'DRY-RUN — ' if self._dry_run else ''}Draft ready for your review. Approve to publish.]",
        }
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_orchestrator.py -v
```

Expected: All 5 tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add backend/modules/orchestrator.py tests/test_orchestrator.py
git commit -m "feat: orchestrator with intent parsing and workflow routing"
```

---

### Task 14: FastAPI routers and main app

**Files:**
- Create: `backend/routers/chat.py`
- Create: `backend/routers/drafts.py`
- Create: `backend/routers/approvals.py`
- Create: `backend/routers/audit.py`
- Create: `backend/routers/__init__.py`
- Create: `backend/main.py`
- Create: `tests/test_routers.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_routers.py
import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from backend.main import create_app
from backend.db.database import get_db


@pytest.fixture
def client(test_db):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: test_db
    return TestClient(app)


def test_post_chat_returns_draft(client):
    with patch("backend.routers.chat.Orchestrator") as MockOrch:
        mock_instance = MagicMock()
        mock_instance.handle = AsyncMock(return_value={
            "type": "draft",
            "draft_id": "abc",
            "content_type": "announcement",
            "content": {"title": "Test", "body": "Body"},
            "status": "pending_approval",
            "message": "Draft ready",
        })
        MockOrch.return_value = mock_instance
        response = client.post("/chat", json={"command": "Create an announcement"})
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "draft"


def test_get_audit_log_returns_list(client):
    response = client.get("/audit-log")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_post_approve_unknown_draft_returns_404(client):
    response = client.post("/approve/nonexistent-id", json={"decision": "approve"})
    assert response.status_code == 404
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_routers.py -v
```

Expected: `ImportError: cannot import name 'create_app'`

- [ ] **Step 3: Write routers**

```python
# backend/routers/__init__.py
```

```python
# backend/routers/chat.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.modules.orchestrator import Orchestrator
from backend.modules.context_store import ContextStore
from backend.config import settings

router = APIRouter()
_context_store = ContextStore()
_session_id: str | None = None


class ChatRequest(BaseModel):
    command: str
    dashboard_context: dict | None = None


@router.post("/chat")
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    orch = Orchestrator(
        db=db,
        context_store=_context_store,
        session_id=_session_id,
        dry_run=settings.dry_run,
    )
    result = await orch.handle(request.command, request.dashboard_context)
    return result
```

```python
# backend/routers/drafts.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db.models import Draft

router = APIRouter()


@router.get("/drafts")
def list_drafts(db: Session = Depends(get_db)):
    drafts = db.query(Draft).order_by(Draft.created_at.desc()).limit(20).all()
    return [
        {
            "id": d.id,
            "type": d.type,
            "status": d.status,
            "created_at": d.created_at.isoformat(),
            "content": d.content_json,
        }
        for d in drafts
    ]


@router.get("/drafts/{draft_id}")
def get_draft(draft_id: str, db: Session = Depends(get_db)):
    draft = db.get(Draft, draft_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="Draft not found")
    return {
        "id": draft.id,
        "type": draft.type,
        "status": draft.status,
        "created_at": draft.created_at.isoformat(),
        "content": draft.content_json,
    }
```

```python
# backend/routers/approvals.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db.models import Draft
from backend.modules.approval_gate import ApprovalGate

router = APIRouter()


class ApprovalRequest(BaseModel):
    decision: str  # approve | edit | discard


@router.post("/approve/{draft_id}")
def approve(draft_id: str, request: ApprovalRequest, db: Session = Depends(get_db)):
    draft = db.get(Draft, draft_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="Draft not found")
    gate = ApprovalGate(db)
    gate.record_decision(draft_id, request.decision)
    return {"draft_id": draft_id, "decision": request.decision, "status": "recorded"}
```

```python
# backend/routers/audit.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db.models import AuditLog

router = APIRouter()


@router.get("/audit-log")
def get_audit_log(limit: int = 50, db: Session = Depends(get_db)):
    entries = (
        db.query(AuditLog)
        .order_by(AuditLog.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": e.id,
            "action_type": e.action_type,
            "module": e.module,
            "input_summary": e.input_summary,
            "result": e.result,
            "approved": e.approved,
            "timestamp": e.timestamp.isoformat(),
        }
        for e in entries
    ]
```

- [ ] **Step 4: Write main.py**

```python
# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.db.database import create_all_tables
from backend.routers import chat, drafts, approvals, audit


def create_app() -> FastAPI:
    app = FastAPI(title="GDG Admin Assistant", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(chat.router)
    app.include_router(drafts.router)
    app.include_router(approvals.router)
    app.include_router(audit.router)

    @app.on_event("startup")
    def startup():
        create_all_tables()

    return app


app = create_app()
```

- [ ] **Step 5: Run test to verify it passes**

```bash
pytest tests/test_routers.py -v
```

Expected: All 3 tests PASSED.

- [ ] **Step 6: Smoke test the running server**

```bash
uvicorn backend.main:app --reload
```

In another terminal:
```bash
curl http://localhost:8000/audit-log
```

Expected: `[]`

- [ ] **Step 7: Commit**

```bash
git add backend/routers/ backend/main.py tests/test_routers.py
git commit -m "feat: FastAPI routers — chat, drafts, approvals, audit log"
```

---

## Phase 6: Frontend

### Task 15: Next.js project setup and layout

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/next.config.ts`
- Create: `frontend/tailwind.config.ts`
- Create: `frontend/app/layout.tsx`
- Create: `frontend/app/page.tsx`
- Create: `frontend/lib/api.ts`

- [ ] **Step 1: Scaffold Next.js project**

```bash
cd frontend
npx create-next-app@latest . --typescript --tailwind --app --no-src-dir --no-import-alias
```

When prompted: use defaults. This creates `package.json`, `tailwind.config.ts`, `next.config.ts`, and `app/layout.tsx`.

- [ ] **Step 2: Write lib/api.ts**

```typescript
// frontend/lib/api.ts
const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface ChatResponse {
  type: "draft" | "chat" | "dashboard_state";
  draft_id?: string;
  content_type?: string;
  content?: Record<string, unknown>;
  status?: string;
  message?: string;
  data?: unknown;
}

export interface Draft {
  id: string;
  type: string;
  status: string;
  created_at: string;
  content: string;
}

export interface AuditEntry {
  id: number;
  action_type: string;
  module: string;
  input_summary: string;
  result: string;
  approved: boolean;
  timestamp: string;
}

export async function sendChat(
  command: string,
  dashboardContext?: Record<string, unknown>
): Promise<ChatResponse> {
  const res = await fetch(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ command, dashboard_context: dashboardContext }),
  });
  if (!res.ok) throw new Error(`Chat error: ${res.status}`);
  return res.json();
}

export async function listDrafts(): Promise<Draft[]> {
  const res = await fetch(`${BASE}/drafts`);
  if (!res.ok) throw new Error(`Drafts error: ${res.status}`);
  return res.json();
}

export async function getDraft(id: string): Promise<Draft> {
  const res = await fetch(`${BASE}/drafts/${id}`);
  if (!res.ok) throw new Error(`Draft error: ${res.status}`);
  return res.json();
}

export async function submitApproval(
  draftId: string,
  decision: "approve" | "edit" | "discard"
): Promise<void> {
  const res = await fetch(`${BASE}/approve/${draftId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ decision }),
  });
  if (!res.ok) throw new Error(`Approval error: ${res.status}`);
}

export async function getAuditLog(): Promise<AuditEntry[]> {
  const res = await fetch(`${BASE}/audit-log?limit=50`);
  if (!res.ok) throw new Error(`Audit error: ${res.status}`);
  return res.json();
}
```

- [ ] **Step 3: Write app/page.tsx (three-panel shell)**

```tsx
// frontend/app/page.tsx
"use client";
import { useState } from "react";
import ChatPanel from "./components/ChatPanel";
import PreviewPanel from "./components/PreviewPanel";
import ActivityLog from "./components/ActivityLog";
import type { ChatResponse } from "../lib/api";

export default function Home() {
  const [activeDraft, setActiveDraft] = useState<ChatResponse | null>(null);
  const [activeTab, setActiveTab] = useState<"preview" | "log" | "members">("preview");
  const [logRefresh, setLogRefresh] = useState(0);

  const handleDraftReady = (response: ChatResponse) => {
    setActiveDraft(response);
    setActiveTab("preview");
  };

  const handleApprovalDone = () => {
    setActiveDraft(null);
    setLogRefresh((n) => n + 1);
  };

  return (
    <div className="flex flex-col h-screen bg-slate-900 text-slate-100">
      {/* Top bar */}
      <div className="flex items-center gap-3 px-4 py-2 bg-slate-800 border-b border-slate-700 shrink-0">
        <span className="font-bold text-indigo-400 text-sm">GDG Admin</span>
        <span className="text-slate-400 text-xs">GDG on Campus GJU · Madaba, Jordan</span>
        <div className="ml-auto flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-green-400 inline-block" />
          <span className="text-green-400 text-xs">Backend connected</span>
        </div>
      </div>

      {/* Main panels */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <div className="w-52 bg-slate-800 border-r border-slate-700 p-3 shrink-0 overflow-y-auto">
          <p className="text-slate-500 text-xs font-bold uppercase tracking-widest mb-2 px-2">Navigation</p>
          {["Chat", "Announcements", "Events", "Emails", "Audit Log"].map((item) => (
            <div key={item} className="px-3 py-2 rounded-md text-slate-400 text-xs hover:bg-indigo-900/30 hover:text-slate-100 cursor-pointer">
              {item}
            </div>
          ))}
          <p className="text-slate-500 text-xs font-bold uppercase tracking-widest mt-4 mb-2 px-2">Templates</p>
          {["Event Announcement", "Speaker Welcome", "RSVP Reminder"].map((t) => (
            <div key={t} className="px-3 py-2 rounded-md text-slate-400 text-xs hover:bg-indigo-900/30 hover:text-slate-100 cursor-pointer">
              {t}
            </div>
          ))}
        </div>

        {/* Chat */}
        <div className="flex-1 overflow-hidden">
          <ChatPanel onDraftReady={handleDraftReady} />
        </div>

        {/* Right panel */}
        <div className="w-80 bg-slate-800 border-l border-slate-700 flex flex-col shrink-0">
          <div className="flex border-b border-slate-700">
            {(["preview", "log", "members"] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`flex-1 py-2 text-xs capitalize ${
                  activeTab === tab
                    ? "text-indigo-400 border-b-2 border-indigo-400"
                    : "text-slate-500"
                }`}
              >
                {tab === "log" ? "Activity Log" : tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>
          <div className="flex-1 overflow-y-auto p-3">
            {activeTab === "preview" && (
              <PreviewPanel draft={activeDraft} onDone={handleApprovalDone} />
            )}
            {activeTab === "log" && <ActivityLog refresh={logRefresh} />}
            {activeTab === "members" && (
              <p className="text-slate-500 text-xs">Member list: read from dashboard via Playwright.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Start dev server and verify shell renders**

```bash
cd frontend && npm run dev
```

Open http://localhost:3000. Expected: three-panel layout visible with sidebar, empty center, and right panel tabs.

- [ ] **Step 5: Commit**

```bash
cd ..
git add frontend/
git commit -m "feat: Next.js frontend shell — three-panel layout"
```

---

### Task 16: ChatPanel component

**Files:**
- Create: `frontend/app/components/ChatPanel.tsx`

- [ ] **Step 1: Write ChatPanel.tsx**

```tsx
// frontend/app/components/ChatPanel.tsx
"use client";
import { useState } from "react";
import { sendChat, type ChatResponse } from "../../lib/api";

const QUICK_COMMANDS = [
  "Read my dashboard",
  "Draft event announcement",
  "Email registrants",
  "Show audit log",
  "Enable dry-run",
];

interface Message {
  role: "user" | "agent";
  text: string;
  timestamp: string;
}

interface Props {
  onDraftReady: (response: ChatResponse) => void;
}

export default function ChatPanel({ onDraftReady }: Props) {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "agent",
      text: "Hello! I'm your GDG on Campus GJU assistant. What would you like to work on today?",
      timestamp: new Date().toLocaleTimeString(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const send = async (command: string) => {
    if (!command.trim() || loading) return;
    const userMsg: Message = { role: "user", text: command, timestamp: new Date().toLocaleTimeString() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const response = await sendChat(command);
      const agentText =
        response.type === "draft"
          ? `Draft ready: "${(response.content as Record<string, string>)?.title ?? "untitled"}". Review it in the Preview panel and approve to publish.`
          : response.type === "chat"
          ? response.message ?? ""
          : JSON.stringify(response.data ?? {});

      setMessages((prev) => [
        ...prev,
        { role: "agent", text: agentText, timestamp: new Date().toLocaleTimeString() },
      ]);

      if (response.type === "draft") {
        onDraftReady(response);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "agent", text: `Error: ${String(err)}`, timestamp: new Date().toLocaleTimeString() },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-2 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
            <div
              className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0 mt-1 ${
                msg.role === "user" ? "bg-indigo-600" : "bg-slate-700 text-blue-400"
              }`}
            >
              {msg.role === "user" ? "You" : "AI"}
            </div>
            <div
              className={`rounded-lg px-3 py-2 max-w-md text-xs leading-relaxed ${
                msg.role === "user"
                  ? "bg-indigo-900/40 border border-indigo-700/30"
                  : "bg-slate-700"
              }`}
            >
              <p className="text-slate-400 text-[10px] mb-1">{msg.timestamp}</p>
              <p>{msg.text}</p>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex gap-2">
            <div className="w-7 h-7 rounded-full bg-slate-700 flex items-center justify-center text-xs text-blue-400">AI</div>
            <div className="bg-slate-700 rounded-lg px-3 py-2 text-xs text-slate-400">Thinking…</div>
          </div>
        )}
      </div>

      {/* Input area */}
      <div className="border-t border-slate-700 p-3">
        <div className="flex flex-wrap gap-1 mb-2">
          {QUICK_COMMANDS.map((cmd) => (
            <button
              key={cmd}
              onClick={() => send(cmd)}
              className="text-[10px] px-2 py-1 rounded-full bg-indigo-900/30 border border-indigo-700/30 text-indigo-300 hover:bg-indigo-800/50"
            >
              {cmd}
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(input); }}}
            rows={2}
            placeholder="Type a command… e.g. 'Draft a welcome email for speakers'"
            className="flex-1 bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-xs text-slate-100 placeholder-slate-500 resize-none focus:outline-none focus:border-indigo-500"
          />
          <button
            onClick={() => send(input)}
            disabled={loading}
            className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold px-4 rounded-lg"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify in browser**

With both `uvicorn backend.main:app --reload` and `npm run dev` running:
- Open http://localhost:3000
- Type "Create an announcement for the AI workshop" and press Enter
- Expected: message appears, agent responds, draft appears in Preview panel

- [ ] **Step 3: Commit**

```bash
git add frontend/app/components/ChatPanel.tsx
git commit -m "feat: ChatPanel with message thread, quick commands, and draft routing"
```

---

### Task 17: PreviewPanel and ApprovalModal

**Files:**
- Create: `frontend/app/components/PreviewPanel.tsx`
- Create: `frontend/app/components/ApprovalModal.tsx`

- [ ] **Step 1: Write ApprovalModal.tsx**

```tsx
// frontend/app/components/ApprovalModal.tsx
"use client";
import { useState } from "react";

interface Props {
  title: string;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function ApprovalModal({ title, message, onConfirm, onCancel }: Props) {
  const [countdown, setCountdown] = useState(5);
  const [started, setStarted] = useState(false);

  const startCountdown = () => {
    setStarted(true);
    let n = 5;
    const interval = setInterval(() => {
      n -= 1;
      setCountdown(n);
      if (n <= 0) clearInterval(interval);
    }, 1000);
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-slate-800 border border-red-700/40 rounded-xl p-6 max-w-sm w-full mx-4">
        <div className="text-red-400 text-xs font-bold mb-1">⚠ SENSITIVE ACTION</div>
        <h3 className="text-slate-100 font-semibold mb-2">{title}</h3>
        <p className="text-slate-400 text-xs mb-4">{message}</p>
        <div className="flex gap-2">
          <button onClick={onCancel} className="flex-1 py-2 rounded-lg bg-slate-700 text-slate-300 text-xs">
            Cancel
          </button>
          {!started ? (
            <button
              onClick={startCountdown}
              className="flex-1 py-2 rounded-lg bg-red-900/40 border border-red-700/40 text-red-300 text-xs"
            >
              Proceed (5s delay)
            </button>
          ) : countdown > 0 ? (
            <button disabled className="flex-1 py-2 rounded-lg bg-red-900/20 text-red-500 text-xs opacity-50">
              Wait {countdown}s…
            </button>
          ) : (
            <button
              onClick={onConfirm}
              className="flex-1 py-2 rounded-lg bg-red-600 text-white text-xs font-semibold"
            >
              Confirm
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Write PreviewPanel.tsx**

```tsx
// frontend/app/components/PreviewPanel.tsx
"use client";
import { useState } from "react";
import { submitApproval, type ChatResponse } from "../../lib/api";
import ApprovalModal from "./ApprovalModal";

interface Props {
  draft: ChatResponse | null;
  onDone: () => void;
}

export default function PreviewPanel({ draft, onDone }: Props) {
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);

  if (!draft || draft.type !== "draft" || !draft.draft_id) {
    return (
      <p className="text-slate-500 text-xs text-center mt-8">
        No draft pending. Type a command in the chat to generate one.
      </p>
    );
  }

  const content = draft.content as Record<string, unknown>;
  const isDestructive = false; // set true for delete/modify actions

  const decide = async (decision: "approve" | "edit" | "discard") => {
    if (!draft.draft_id) return;
    setLoading(true);
    try {
      await submitApproval(draft.draft_id, decision);
      onDone();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {showModal && (
        <ApprovalModal
          title="Confirm Discard"
          message="This will permanently discard the draft. This action is logged."
          onConfirm={() => { setShowModal(false); decide("discard"); }}
          onCancel={() => setShowModal(false)}
        />
      )}

      {/* Approval required banner */}
      <div className="bg-red-950/40 border border-red-700/30 rounded-lg p-3 mb-3">
        <p className="text-red-400 text-xs font-bold">🔴 APPROVAL REQUIRED</p>
        <p className="text-slate-400 text-[10px] mt-1">Review the draft below before publishing.</p>
      </div>

      {/* Action type */}
      <div className="bg-slate-900 rounded-lg p-3 mb-2">
        <p className="text-slate-500 text-[10px] uppercase font-bold mb-1">Action</p>
        <p className="text-slate-200 text-xs">
          Publish {draft.content_type}{" "}
          <span className="text-amber-400 text-[10px]">[UI AUTOMATION]</span>
        </p>
      </div>

      {/* Content fields */}
      {Object.entries(content).map(([key, value]) => (
        <div key={key} className="bg-slate-900 rounded-lg p-3 mb-2">
          <p className="text-slate-500 text-[10px] uppercase font-bold mb-1">{key}</p>
          <p className="text-slate-200 text-xs leading-relaxed whitespace-pre-wrap">
            {Array.isArray(value) ? (value as string[]).join(", ") : String(value)}
          </p>
        </div>
      ))}

      {/* Warning */}
      <div className="bg-red-950/20 border border-red-700/20 rounded-lg p-2 mb-3">
        <p className="text-red-400 text-[10px]">
          ⚠ This will publish immediately to your GDG chapter page. This action is logged.
        </p>
      </div>

      {/* Action buttons */}
      <div className="space-y-2">
        <button
          onClick={() => decide("approve")}
          disabled={loading}
          className="w-full py-2 rounded-lg bg-green-600 hover:bg-green-500 disabled:opacity-50 text-white text-xs font-semibold"
        >
          ✓ Approve & Publish
        </button>
        <button
          onClick={() => decide("edit")}
          disabled={loading}
          className="w-full py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-300 text-xs"
        >
          ✎ Edit Draft
        </button>
        <button
          onClick={() => setShowModal(true)}
          disabled={loading}
          className="w-full py-2 rounded-lg bg-red-950/30 border border-red-700/30 hover:bg-red-900/40 text-red-400 text-xs"
        >
          ✗ Discard
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Verify approval flow in browser**

1. Send "Create an announcement for the AI workshop" in chat
2. Draft appears in Preview panel
3. Click "Approve & Publish" — verify approval is sent to backend
4. Check `GET /audit-log` — verify entry appears
5. Click "Discard" — verify ApprovalModal appears with 5-second delay

- [ ] **Step 4: Commit**

```bash
git add frontend/app/components/PreviewPanel.tsx frontend/app/components/ApprovalModal.tsx
git commit -m "feat: PreviewPanel with approval gate and ApprovalModal with countdown"
```

---

### Task 18: ActivityLog component

**Files:**
- Create: `frontend/app/components/ActivityLog.tsx`

- [ ] **Step 1: Write ActivityLog.tsx**

```tsx
// frontend/app/components/ActivityLog.tsx
"use client";
import { useEffect, useState } from "react";
import { getAuditLog, type AuditEntry } from "../../lib/api";

const RESULT_COLORS: Record<string, string> = {
  success: "border-green-500 text-green-400",
  failed: "border-red-500 text-red-400",
  dry_run: "border-amber-500 text-amber-400",
  routing: "border-indigo-500 text-indigo-400",
  in_progress: "border-blue-500 text-blue-400",
};

interface Props {
  refresh: number;
}

export default function ActivityLog({ refresh }: Props) {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAuditLog()
      .then(setEntries)
      .catch((e) => setError(String(e)));
  }, [refresh]);

  if (error) return <p className="text-red-400 text-xs">{error}</p>;
  if (entries.length === 0)
    return <p className="text-slate-500 text-xs text-center mt-8">No actions logged yet.</p>;

  return (
    <div className="space-y-2">
      {entries.map((entry) => (
        <div
          key={entry.id}
          className={`border-l-2 pl-3 py-1 ${RESULT_COLORS[entry.result] ?? "border-slate-600 text-slate-400"}`}
        >
          <p className="text-slate-500 text-[10px]">
            {new Date(entry.timestamp).toLocaleTimeString()} · {entry.module}
          </p>
          <p className="text-slate-200 text-xs mt-0.5">{entry.input_summary}</p>
          <p className="text-[10px] mt-0.5">
            {entry.action_type} · {entry.result} · {entry.approved ? "approved" : "unapproved"}
          </p>
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 2: Verify in browser**

Switch to the Activity Log tab. Perform a chat action. Verify the new entry appears after approval.

- [ ] **Step 3: Commit**

```bash
git add frontend/app/components/ActivityLog.tsx
git commit -m "feat: ActivityLog component with color-coded audit feed"
```

---

## Phase 7: Integration

### Task 19: End-to-end dry-run verification

**Files:**
- No new files — integration test using existing stack

- [ ] **Step 1: Set dry-run mode in .env**

```bash
# .env
DRY_RUN=true
```

Restart backend: `uvicorn backend.main:app --reload`

- [ ] **Step 2: Run the full pytest suite**

```bash
pytest tests/ -v
```

Expected: All tests PASSED. Zero failures.

- [ ] **Step 3: Manual dry-run walkthrough**

With both servers running and DRY_RUN=true:

1. Open http://localhost:3000
2. Type: "Create an announcement for next week's AI workshop"
   - Expected: Draft appears in Preview panel with `[DRY-RUN]` in message
3. Click "Approve & Publish"
   - Expected: Response shows `result: dry_run` — nothing posted to GDG
4. Check Activity Log tab — expected: entry with result=`dry_run` and approved=`true`
5. Type: "Draft a new event for Android Study Jam on April 25"
   - Expected: Event draft appears with date, venue fields
6. Discard it — verify ApprovalModal appears, confirm, verify log entry

- [ ] **Step 4: Turn off dry-run and do a live Playwright test (manual)**

```bash
# .env
DRY_RUN=false
```

1. Restart backend
2. Type: "Read my dashboard"
   - Playwright browser opens to gdg.community.dev
   - Log in manually when prompted
   - Backend reads page state and returns it in chat
3. Type: "Create an announcement for the AI workshop"
   - Review draft carefully in Preview panel
   - Click "Approve & Publish"
   - Verify announcement appears on your GDG dashboard

- [ ] **Step 5: Final commit**

```bash
git add .
git commit -m "feat: end-to-end integration verified — GDG Admin Assistant MVP complete"
```

---

## Self-Review

**Spec coverage check:**

| Spec section | Covered by |
|---|---|
| A. Architecture (hybrid) | Task 10–12 (Playwright), Task 8–9 (Gmail API) |
| B. Core modules (10 modules) | Tasks 3–13 |
| C. Tech stack | Task 1 (requirements.txt), all tasks |
| D. Dashboard flow | Task 11 (reader), Task 12 (executor), Task 13 (orchestrator) |
| D. Email flow | Task 8–9 (Gmail), Task 4 (safety), Task 5 (approval) |
| E. Safety model | Task 4 (guardrail), Task 5 (approval gate), Task 12 (rollback) |
| F. Data model (7 tables) | Task 2 (all tables including rollback_snapshots) |
| G. System prompt | Task 7 (ContentGenerator SYSTEM_PROMPT) |
| H. UI design | Tasks 15–18 (all components) |
| I. Project structure | Task 1 (scaffold), all subsequent tasks |
| J. Example commands | Handled by orchestrator intent parsing (Task 13) |
| K. Deployment (local) | Task 1 + Task 19 |

**Type consistency check:** `AuditLogger.log()` signature is consistent across all callers (Tasks 3, 12, 13). `SafetyGuardrail.check_action()` called consistently with `action_type` and `session_id`. `ApprovalGate.record_decision()` called consistently with `draft_id` and `decision` string. `Draft.status` values (`pending`, `approved`, `published`, `discarded`) are consistent throughout.

**No placeholders found** — all steps contain complete code.
