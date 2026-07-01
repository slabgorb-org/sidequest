# In-App Bug Reporter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A global player-facing 🐞 button that files a GitHub issue enriched with user-attached files (→ R2), a scrubbed server-log tail, and a scrubbed OTEL summary of the active session.

**Architecture:** The React client POSTs `multipart/form-data` to a new `POST /api/bug-report` endpoint. The server uploads attachments to the R2 `bug-reports/` prefix, gathers + scrubs a server-log tail and the session's OTEL ring buffer, creates the issue via the GitHub REST API using the server-side PAT, emits a `bug_report.created` watcher event, and returns the issue URL. GitHub token and R2 creds never leave the server.

**Tech Stack:** Python/FastAPI (uv, pytest, ruff), boto3 (R2/S3), httpx (GitHub API); React/TypeScript (Vite, vitest, testing-library, Tailwind).

## Global Constraints

- **Repos are separate git clones.** Server tasks (1–8) edit + commit in `sidequest-server/`; UI tasks (9–12) edit + commit in `sidequest-ui/`. Run each commit from that subrepo's directory. Suggested branch in each: `feat/in-app-bug-reporter`.
- **No Silent Fallbacks (CLAUDE.md).** Hard dependencies — **R2 upload and GitHub issue creation** — abort with HTTP `502` on failure; never post a partial issue. Best-effort enrichment — **server-log tail and OTEL summary** — records its *absence* explicitly in the issue body; never aborts, never substitutes.
- **Target repo is PUBLIC** (`slabgorb-org/sidequest`). All log/OTEL text is `scrub()`-ed before it leaves the server.
- **OTEL principle (CLAUDE.md).** The endpoint emits `bug_report.created` (component `bug_report`) so the GM panel confirms the subsystem fired.
- **Wiring rule (CLAUDE.md).** The server suite includes a `TestClient` test hitting the registered route; the UI suite includes a test that the button opens the modal and POSTs.
- Constants (exact): GitHub owner `slabgorb-org`, repo `sidequest`, labels `["bug", "in-app-report"]`. R2 bucket `sidequest`, prefix `bug-reports`, CDN default `https://cdn.slabgorb.com`. Log path `$SIDEQUEST_SERVER_LOG` default `~/.sidequest/logs/sidequest-server.log`. `LOG_TAIL_LINES = 200`, `OTEL_EVENT_LIMIT = 150`, `GITHUB_BODY_LIMIT = 65536`. File caps: **10 MB/file, ≤ 6 files**, types `image/*` + `.log/.txt/.json`.
- TDD, DRY, YAGNI, frequent commits.

---

### Task 1: `WatcherHub.buffered_events` — read accessor for the OTEL summary

**Files:**
- Modify: `sidequest-server/sidequest/telemetry/watcher_hub.py` (add a method to `WatcherHub`, immediately after the `replay` method)
- Test: `sidequest-server/tests/server/test_bug_report_buffered_events.py`

**Interfaces:**
- Produces: `async WatcherHub.buffered_events(self, slug: str | None) -> list[dict[str, Any]]` — the events buffered for `slug` merged with the global infra (`None`) bucket, ordered by publish seq. Read-only.

- [ ] **Step 1: Write the failing test**

```python
# sidequest-server/tests/server/test_bug_report_buffered_events.py
"""Task 1 — WatcherHub.buffered_events read accessor (RED)."""
from __future__ import annotations

import asyncio

import pytest

from sidequest.telemetry.watcher_hub import WatcherHub, watcher_hub


@pytest.fixture
async def bound_hub() -> WatcherHub:
    watcher_hub.bind_loop(asyncio.get_running_loop())
    async with watcher_hub._lock:  # noqa: SLF001
        watcher_hub._subscribers.clear()  # noqa: SLF001
        watcher_hub._session_buffers.clear()  # noqa: SLF001
        watcher_hub._seq = 0  # noqa: SLF001
    return watcher_hub


def _event(session_slug, event_type):
    return {
        "timestamp": "2026-07-01T00:00:00+00:00",
        "component": "test",
        "event_type": event_type,
        "severity": "info",
        "session_slug": session_slug,
        "fields": {"n": event_type},
    }


@pytest.mark.asyncio
async def test_buffered_events_merges_slug_and_infra_in_seq_order(bound_hub: WatcherHub) -> None:
    bound_hub.publish(_event(None, "infra-a"))
    bound_hub.publish(_event("s1", "s1-a"))
    bound_hub.publish(_event("s2", "s2-a"))
    bound_hub.publish(_event("s1", "s1-b"))
    await asyncio.sleep(0.05)

    events = await bound_hub.buffered_events("s1")
    names = [e["event_type"] for e in events]
    # s1's two events plus the global infra event, in publish order; no s2.
    assert names == ["infra-a", "s1-a", "s1-b"], names


@pytest.mark.asyncio
async def test_buffered_events_unknown_slug_returns_infra_only(bound_hub: WatcherHub) -> None:
    bound_hub.publish(_event(None, "infra-a"))
    bound_hub.publish(_event("s1", "s1-a"))
    await asyncio.sleep(0.05)

    events = await bound_hub.buffered_events("nope")
    assert [e["event_type"] for e in events] == ["infra-a"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/server/test_bug_report_buffered_events.py -v`
Expected: FAIL — `AttributeError: 'WatcherHub' object has no attribute 'buffered_events'`

- [ ] **Step 3: Add the method (immediately after `WatcherHub.replay`)**

```python
    async def buffered_events(self, slug: str | None) -> list[dict[str, Any]]:
        """Return buffered events for ``slug`` merged with the global infra
        (``None``) bucket, ordered by the monotonic publish seq.

        Read-only: never mutates hub state (mirrors :meth:`replay`). Used by the
        in-app bug reporter to attach an OTEL summary scoped to the reporting
        session.
        """
        async with self._lock:
            merged: list[tuple[int, dict[str, Any]]] = []
            for key in {None, slug}:
                bucket = self._session_buffers.get(key)
                if bucket is not None:
                    merged.extend(bucket)
        merged.sort(key=lambda pair: pair[0])
        return [event for _seq, event in merged]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/server/test_bug_report_buffered_events.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
cd sidequest-server
git add sidequest/telemetry/watcher_hub.py tests/server/test_bug_report_buffered_events.py
git commit -m "feat(watcher): add buffered_events read accessor for bug-report OTEL summary"
```

---

### Task 2: `scrub()` — secret + home-path redaction

**Files:**
- Create: `sidequest-server/sidequest/server/bug_report_enrich.py`
- Test: `sidequest-server/tests/server/test_bug_report_enrich.py`

**Interfaces:**
- Produces: `scrub(text: str) -> str` — redacts secret-shaped tokens, known secret env-var literals, and rewrites the absolute home dir to `~`.

- [ ] **Step 1: Write the failing test**

```python
# sidequest-server/tests/server/test_bug_report_enrich.py
"""Tasks 2–5 — bug_report_enrich (RED)."""
from __future__ import annotations

from pathlib import Path

import pytest

from sidequest.server.bug_report_enrich import scrub


def test_scrub_redacts_token_shapes() -> None:
    text = (
        "pat=github_pat_11ABCDEF0123456789 gho=gho_abcdefghijklmnopqrstuvwxyz012345 "
        "anth=sk-ant-api03-abcDEF_-123 auth: Bearer eyJhbGciOiJIUzI1NiJ9.payload.sig "
        "akia=AKIA1234567890ABCDEF"
    )
    out = scrub(text)
    assert "github_pat_11ABCDEF0123456789" not in out
    assert "gho_abcdefghijklmnopqrstuvwxyz012345" not in out
    assert "sk-ant-api03-abcDEF_-123" not in out
    assert "AKIA1234567890ABCDEF" not in out
    assert "Bearer eyJhbGciOiJIUzI1NiJ9" not in out


def test_scrub_redacts_known_env_secret_literal(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SIDEQUEST_CI_TOKEN", "supersecretvalue12345")
    out = scrub("the token is supersecretvalue12345 ok")
    assert "supersecretvalue12345" not in out


def test_scrub_rewrites_home_path() -> None:
    home = str(Path.home())
    out = scrub(f"reading {home}/.sidequest/logs/x.log")
    assert home not in out
    assert "~/.sidequest/logs/x.log" in out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/server/test_bug_report_enrich.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'sidequest.server.bug_report_enrich'`

- [ ] **Step 3: Create the module with `scrub` (and the shared constants)**

```python
# sidequest-server/sidequest/server/bug_report_enrich.py
"""Enrichment helpers for the in-app bug reporter: secret scrubbing, server-log
tail, OTEL summary, and Markdown issue-body composition.

The target repo is PUBLIC, so every log/OTEL string passes through ``scrub``
before it is embedded in an issue. ``scrub`` only *removes* — it never rewrites
meaning — so applying it defensively is always safe.
"""
from __future__ import annotations

import json
import os
import re
from collections import deque
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

LOG_TAIL_LINES = 200
OTEL_EVENT_LIMIT = 150
GITHUB_BODY_LIMIT = 65536
_LOG_BLOCK_MAX = 16000
_OTEL_BLOCK_MAX = 16000
_TRUNC = "\n…(truncated)"
_REDACTED = "«redacted»"

_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"github_pat_[A-Za-z0-9_]+"),
    re.compile(r"gh[posru]_[A-Za-z0-9]{20,}"),
    re.compile(r"sk-ant-[A-Za-z0-9\-_]+"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9\-._~+/]+=*"),
)
_ENV_SECRET_VARS = (
    "SIDEQUEST_CI_TOKEN",
    "R2_SECRET_ACCESS_KEY",
    "R2_ACCESS_KEY_ID",
    "ANTHROPIC_API_KEY",
)


def scrub(text: str) -> str:
    """Redact secret-shaped tokens, known secret env-var literals, and rewrite
    the absolute home dir to ``~``. Removal-only; safe to over-apply."""
    if not text:
        return text
    out = text
    for var in _ENV_SECRET_VARS:
        val = os.environ.get(var)
        if val and len(val) >= 8:
            out = out.replace(val, _REDACTED)
    for pat in _SECRET_PATTERNS:
        out = pat.sub(_REDACTED, out)
    home = str(Path.home())
    if home and home != "/":
        out = out.replace(home, "~")
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/server/test_bug_report_enrich.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
cd sidequest-server
git add sidequest/server/bug_report_enrich.py tests/server/test_bug_report_enrich.py
git commit -m "feat(bug-report): secret/home-path scrub for public-issue enrichment"
```

---

### Task 2b… note

Tasks 3, 4, and 5 append functions to the **same** `bug_report_enrich.py` and **same** test file created in Task 2. Add to the files; don't recreate them.

### Task 3: `tail_server_log()` — bounded server-log tail

**Files:**
- Modify: `sidequest-server/sidequest/server/bug_report_enrich.py`
- Test: `sidequest-server/tests/server/test_bug_report_enrich.py`

**Interfaces:**
- Produces: `tail_server_log(n_lines: int = LOG_TAIL_LINES) -> str | None` — last N lines of `$SIDEQUEST_SERVER_LOG` (default `~/.sidequest/logs/sidequest-server.log`); `None` if absent/unreadable. `server_log_path() -> Path`.

- [ ] **Step 1: Write the failing test (append)**

```python
def test_tail_server_log_returns_last_n_lines(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    from sidequest.server.bug_report_enrich import tail_server_log

    log = tmp_path / "server.log"
    log.write_text("".join(f"line {i}\n" for i in range(500)), encoding="utf-8")
    monkeypatch.setenv("SIDEQUEST_SERVER_LOG", str(log))

    out = tail_server_log(n_lines=10)
    assert out is not None
    lines = out.splitlines()
    assert len(lines) == 10
    assert lines[-1] == "line 499"
    assert lines[0] == "line 490"


def test_tail_server_log_missing_file_returns_none(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    from sidequest.server.bug_report_enrich import tail_server_log

    monkeypatch.setenv("SIDEQUEST_SERVER_LOG", str(tmp_path / "does-not-exist.log"))
    assert tail_server_log() is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/server/test_bug_report_enrich.py -k tail_server_log -v`
Expected: FAIL — `ImportError: cannot import name 'tail_server_log'`

- [ ] **Step 3: Append the implementation**

```python
def server_log_path() -> Path:
    override = os.environ.get("SIDEQUEST_SERVER_LOG")
    if override:
        return Path(override)
    return Path.home() / ".sidequest" / "logs" / "sidequest-server.log"


def tail_server_log(n_lines: int = LOG_TAIL_LINES) -> str | None:
    """Last ``n_lines`` of the server log, or ``None`` when the file is absent
    or unreadable. Absence is recorded loudly by the caller — never faked."""
    path = server_log_path()
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            lines = deque(fh, maxlen=n_lines)
    except OSError:
        return None
    return "".join(lines)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/server/test_bug_report_enrich.py -k tail_server_log -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
cd sidequest-server
git add sidequest/server/bug_report_enrich.py tests/server/test_bug_report_enrich.py
git commit -m "feat(bug-report): bounded server-log tail with explicit-absence contract"
```

---

### Task 4: `otel_summary()` — formatted session OTEL

**Files:**
- Modify: `sidequest-server/sidequest/server/bug_report_enrich.py`
- Test: `sidequest-server/tests/server/test_bug_report_enrich.py`

**Interfaces:**
- Consumes: `WatcherHub.buffered_events` (Task 1) via the `watcher_hub` singleton.
- Produces: `async otel_summary(slug: str, limit: int = OTEL_EVENT_LIMIT) -> str | None` — one line per event (`ts [sev] component :: event_type {fields}`), last `limit`; `None` when `slug` is empty or the buffer is empty.

- [ ] **Step 1: Write the failing test (append)**

```python
@pytest.mark.asyncio
async def test_otel_summary_formats_events(monkeypatch: pytest.MonkeyPatch) -> None:
    import sidequest.server.bug_report_enrich as enrich

    async def fake_buffered(slug):  # noqa: ARG001
        return [
            {"timestamp": "T1", "severity": "info", "component": "turn",
             "event_type": "turn_complete", "fields": {"round": 3}},
        ]

    monkeypatch.setattr(enrich.watcher_hub, "buffered_events", fake_buffered)
    out = await enrich.otel_summary("s1")
    assert out is not None
    assert "turn_complete" in out
    assert "turn" in out
    assert '"round": 3' in out or "'round': 3" in out


@pytest.mark.asyncio
async def test_otel_summary_empty_slug_returns_none() -> None:
    from sidequest.server.bug_report_enrich import otel_summary

    assert await otel_summary("") is None


@pytest.mark.asyncio
async def test_otel_summary_empty_buffer_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    import sidequest.server.bug_report_enrich as enrich

    async def fake_buffered(slug):  # noqa: ARG001
        return []

    monkeypatch.setattr(enrich.watcher_hub, "buffered_events", fake_buffered)
    assert await enrich.otel_summary("s1") is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/server/test_bug_report_enrich.py -k otel_summary -v`
Expected: FAIL — `ImportError: cannot import name 'otel_summary'` (or `AttributeError` on `watcher_hub`)

- [ ] **Step 3: Append the implementation (and the import at the top of the module)**

Add to the imports block at the top of `bug_report_enrich.py`:

```python
from sidequest.telemetry.watcher_hub import watcher_hub
```

Append the function:

```python
async def otel_summary(slug: str, limit: int = OTEL_EVENT_LIMIT) -> str | None:
    """Compact one-line-per-event OTEL summary for ``slug`` (last ``limit``
    events), or ``None`` when there is no active session or nothing buffered."""
    if not slug:
        return None
    events = await watcher_hub.buffered_events(slug)
    if not events:
        return None
    lines: list[str] = []
    for e in events[-limit:]:
        ts = e.get("timestamp", "")
        sev = e.get("severity", "info")
        comp = e.get("component", "")
        et = e.get("event_type", "")
        try:
            fstr = json.dumps(e.get("fields", {}), default=str)
        except (TypeError, ValueError):
            fstr = str(e.get("fields", {}))
        if len(fstr) > 240:
            fstr = fstr[:240] + "…"
        lines.append(f"{ts} [{sev}] {comp} :: {et} {fstr}")
    return "\n".join(lines)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/server/test_bug_report_enrich.py -k otel_summary -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
cd sidequest-server
git add sidequest/server/bug_report_enrich.py tests/server/test_bug_report_enrich.py
git commit -m "feat(bug-report): session OTEL summary from watcher buffer"
```

---

### Task 5: `compose_body()` — Markdown issue body

**Files:**
- Modify: `sidequest-server/sidequest/server/bug_report_enrich.py`
- Test: `sidequest-server/tests/server/test_bug_report_enrich.py`

**Interfaces:**
- Produces: `compose_body(*, description: str, context: dict[str, Any], attachments: list[tuple[str, str, bool]], log_text: str | None, otel_text: str | None, report_id: str, session_slug: str) -> str`. `attachments` items are `(name, url, is_image)`. Result never exceeds `GITHUB_BODY_LIMIT`.

- [ ] **Step 1: Write the failing test (append)**

```python
def test_compose_body_embeds_images_and_links() -> None:
    from sidequest.server.bug_report_enrich import compose_body

    body = compose_body(
        description="It broke.",
        context={"genre": "space_opera", "world": "perseus_cloud", "screen": "game"},
        attachments=[("shot.png", "https://cdn.slabgorb.com/bug-reports/x/0-shot.png", True),
                     ("log.txt", "https://cdn.slabgorb.com/bug-reports/x/1-log.txt", False)],
        log_text="line one\nline two",
        otel_text="T [info] turn :: turn_complete {}",
        report_id="abc123",
        session_slug="2026-slug",
    )
    assert "It broke." in body
    assert "![shot.png](https://cdn.slabgorb.com/bug-reports/x/0-shot.png)" in body
    assert "[log.txt](https://cdn.slabgorb.com/bug-reports/x/1-log.txt)" in body
    assert "space_opera" in body and "perseus_cloud" in body
    assert "<details><summary>Server log" in body
    assert "turn_complete" in body
    assert "abc123" in body


def test_compose_body_notes_missing_enrichment() -> None:
    from sidequest.server.bug_report_enrich import compose_body

    body = compose_body(
        description="d", context={}, attachments=[],
        log_text=None, otel_text=None, report_id="r", session_slug="",
    )
    assert "server log not found" in body
    assert "no active session" in body


def test_compose_body_respects_github_limit() -> None:
    from sidequest.server.bug_report_enrich import GITHUB_BODY_LIMIT, compose_body

    body = compose_body(
        description="d", context={}, attachments=[],
        log_text="x" * 100_000, otel_text="y" * 100_000,
        report_id="r", session_slug="s",
    )
    assert len(body) <= GITHUB_BODY_LIMIT
    assert "…(truncated)" in body
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/server/test_bug_report_enrich.py -k compose_body -v`
Expected: FAIL — `ImportError: cannot import name 'compose_body'`

- [ ] **Step 3: Append the implementation**

```python
def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max(0, max_chars - len(_TRUNC))] + _TRUNC


def _context_table(session_slug: str, context: dict[str, Any]) -> str:
    rows = [
        ("Session", session_slug or "—"),
        ("Genre", context.get("genre") or "—"),
        ("World", context.get("world") or "—"),
        ("Screen", context.get("screen") or "—"),
        ("Build", context.get("appBuild") or context.get("build") or "—"),
        ("Viewport", context.get("viewport") or "—"),
        ("Path", context.get("pathname") or "—"),
        ("User agent", context.get("userAgent") or "—"),
        ("Filed at", datetime.now(UTC).isoformat()),
    ]
    out = "| Field | Value |\n| --- | --- |\n"
    for key, val in rows:
        safe = str(val).replace("|", "\\|")
        out += f"| {key} | {safe} |\n"
    return out


def compose_body(
    *,
    description: str,
    context: dict[str, Any],
    attachments: list[tuple[str, str, bool]],
    log_text: str | None,
    otel_text: str | None,
    report_id: str,
    session_slug: str,
) -> str:
    """Assemble the Markdown issue body. Enrichment absence is written
    explicitly; the whole body is bounded to ``GITHUB_BODY_LIMIT`` with a loud
    truncation marker."""
    parts: list[str] = [description.strip(), "\n\n## Context\n\n" + _context_table(session_slug, context)]

    if attachments:
        parts.append("\n## Attachments\n")
        for name, url, is_image in attachments:
            parts.append(f"![{name}]({url})" if is_image else f"[{name}]({url})")

    parts.append("\n\n## Server log\n")
    if log_text is None:
        parts.append(f"_server log not found at `{server_log_path()}`_")
    else:
        parts.append(
            f"<details><summary>Server log (scrubbed, last {LOG_TAIL_LINES} lines)</summary>\n\n"
            f"```\n{_truncate(log_text, _LOG_BLOCK_MAX)}\n```\n</details>"
        )

    parts.append("\n\n## OTEL\n")
    if otel_text is None:
        parts.append("_no active session — no OTEL captured_")
    else:
        parts.append(
            f"<details><summary>OTEL — session {session_slug} (scrubbed, last {OTEL_EVENT_LIMIT} events)</summary>\n\n"
            f"```\n{_truncate(otel_text, _OTEL_BLOCK_MAX)}\n```\n</details>"
        )

    parts.append(f"\n\n---\n_report_id: `{report_id}` · Filed from the in-app bug reporter._")

    body = "\n".join(parts)
    if len(body) > GITHUB_BODY_LIMIT:
        body = _truncate(body, GITHUB_BODY_LIMIT)
    return body
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/server/test_bug_report_enrich.py -v`
Expected: PASS (all enrich tests)

- [ ] **Step 5: Commit**

```bash
cd sidequest-server
git add sidequest/server/bug_report_enrich.py tests/server/test_bug_report_enrich.py
git commit -m "feat(bug-report): compose Markdown issue body with bounded enrichment"
```

---

### Task 6: `r2_upload` — attachment upload to R2

**Files:**
- Create: `sidequest-server/sidequest/server/r2_upload.py`
- Modify: `sidequest-server/pyproject.toml` (add `boto3`)
- Test: `sidequest-server/tests/server/test_bug_report_r2_upload.py`

**Interfaces:**
- Produces: `upload_bytes(key: str, data: bytes, content_type: str) -> str` (returns public CDN URL); `object_key(report_id: str, index: int, filename: str) -> str`; `safe_filename(name: str) -> str`; `cdn_base() -> str`; `class R2UploadError(RuntimeError)`.

- [ ] **Step 1: Add the dependency**

Run: `cd sidequest-server && uv add boto3`
Expected: `pyproject.toml` gains `boto3`; `uv.lock` updated; `boto3` importable.

- [ ] **Step 2: Write the failing test**

```python
# sidequest-server/tests/server/test_bug_report_r2_upload.py
"""Task 6 — R2 attachment upload (RED)."""
from __future__ import annotations

import pytest

from sidequest.server import r2_upload
from sidequest.server.r2_upload import R2UploadError, object_key, safe_filename


def test_safe_filename_sanitizes() -> None:
    assert safe_filename("my shot!.png") == "my_shot_.png"
    assert safe_filename("../../etc/passwd") == "etc_passwd"
    assert safe_filename("") == "file"


def test_object_key_layout() -> None:
    assert object_key("abc123", 2, "shot.png") == "bug-reports/abc123/2-shot.png"


def test_upload_bytes_returns_cdn_url(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {}

    class FakeClient:
        def put_object(self, **kwargs):
            calls.update(kwargs)

    monkeypatch.setenv("SIDEQUEST_ASSET_BASE_URL", "https://cdn.slabgorb.com")
    monkeypatch.setattr(r2_upload, "_build_client", lambda: FakeClient())

    url = r2_upload.upload_bytes("bug-reports/x/0-shot.png", b"data", "image/png")
    assert url == "https://cdn.slabgorb.com/bug-reports/x/0-shot.png"
    assert calls["Bucket"] == "sidequest"
    assert calls["Key"] == "bug-reports/x/0-shot.png"
    assert calls["ContentType"] == "image/png"


def test_upload_bytes_wraps_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeClient:
        def put_object(self, **kwargs):
            raise RuntimeError("boom")

    monkeypatch.setattr(r2_upload, "_build_client", lambda: FakeClient())
    with pytest.raises(R2UploadError):
        r2_upload.upload_bytes("k", b"d", "image/png")
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/server/test_bug_report_r2_upload.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'sidequest.server.r2_upload'`

- [ ] **Step 4: Create the module**

```python
# sidequest-server/sidequest/server/r2_upload.py
"""Upload bug-report attachments to the R2 ``bug-reports/`` prefix.

The server holds the R2 creds; the client never does. Objects are served
publicly at ``https://cdn.slabgorb.com/<key>`` (the same CDN the pack assets
use), so the returned URL embeds directly in a GitHub issue. Because the object
physically lives in R2, the CDN URL is correct even when the UI runs in local
asset mode — so ``cdn_base`` ignores the ``local``/empty override.
"""
from __future__ import annotations

import os
import re

BUCKET = "sidequest"
BUG_REPORT_PREFIX = "bug-reports"
_DEFAULT_CDN = "https://cdn.slabgorb.com"


class R2UploadError(RuntimeError):
    """R2 put_object failed — a hard-dependency failure; the endpoint maps it to 502."""


def _build_client():
    import boto3

    return boto3.client(
        "s3",
        endpoint_url=os.environ["R2_S3_ENDPOINT"],
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
    )


def cdn_base() -> str:
    base = os.environ.get("SIDEQUEST_ASSET_BASE_URL", _DEFAULT_CDN)
    if base in ("", "local"):
        base = _DEFAULT_CDN
    return base.rstrip("/")


def safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name or "").strip("._")
    return (cleaned or "file")[:80]


def object_key(report_id: str, index: int, filename: str) -> str:
    return f"{BUG_REPORT_PREFIX}/{report_id}/{index}-{safe_filename(filename)}"


def upload_bytes(key: str, data: bytes, content_type: str) -> str:
    """Put ``data`` at ``key`` in the R2 bucket; return the public CDN URL.
    Any boto/botocore failure is re-raised as ``R2UploadError`` (loud)."""
    try:
        client = _build_client()
        client.put_object(Bucket=BUCKET, Key=key, Body=data, ContentType=content_type)
    except Exception as exc:  # noqa: BLE001 — translate boto/botocore errors to a typed, loud failure
        raise R2UploadError(str(exc)) from exc
    return f"{cdn_base()}/{key}"
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/server/test_bug_report_r2_upload.py -v`
Expected: PASS (4 passed)

- [ ] **Step 6: Commit**

```bash
cd sidequest-server
git add pyproject.toml uv.lock sidequest/server/r2_upload.py tests/server/test_bug_report_r2_upload.py
git commit -m "feat(bug-report): R2 attachment upload seam (adds boto3)"
```

---

### Task 7: `github_issue` — create the issue via the REST API

**Files:**
- Create: `sidequest-server/sidequest/server/github_issue.py`
- Test: `sidequest-server/tests/server/test_bug_report_github_issue.py`

**Interfaces:**
- Produces: `async create_issue(title: str, body: str, labels: list[str] | None = None, *, transport: httpx.BaseTransport | None = None) -> dict[str, Any]` → `{"url": str, "number": int}`; `class GitHubIssueError(RuntimeError)`; `DEFAULT_LABELS: list[str]`.

- [ ] **Step 1: Write the failing test**

```python
# sidequest-server/tests/server/test_bug_report_github_issue.py
"""Task 7 — GitHub issue creation (RED)."""
from __future__ import annotations

import httpx
import pytest

from sidequest.server.github_issue import GitHubIssueError, create_issue


@pytest.mark.asyncio
async def test_create_issue_returns_url_and_number(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SIDEQUEST_CI_TOKEN", "tok")
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["auth"] = request.headers.get("authorization")
        return httpx.Response(201, json={"html_url": "https://github.com/o/r/issues/7", "number": 7})

    out = await create_issue("T", "B", ["bug"], transport=httpx.MockTransport(handler))
    assert out == {"url": "https://github.com/o/r/issues/7", "number": 7}
    assert captured["url"] == "https://api.github.com/repos/slabgorb-org/sidequest/issues"
    assert captured["auth"] == "Bearer tok"


@pytest.mark.asyncio
async def test_create_issue_non_2xx_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SIDEQUEST_CI_TOKEN", "tok")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, text="forbidden")

    with pytest.raises(GitHubIssueError):
        await create_issue("T", "B", transport=httpx.MockTransport(handler))


@pytest.mark.asyncio
async def test_create_issue_missing_token_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SIDEQUEST_CI_TOKEN", raising=False)
    with pytest.raises(GitHubIssueError):
        await create_issue("T", "B")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/server/test_bug_report_github_issue.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'sidequest.server.github_issue'`

- [ ] **Step 3: Create the module**

```python
# sidequest-server/sidequest/server/github_issue.py
"""Create a GitHub issue on the public tracker via the REST API.

The PAT (``SIDEQUEST_CI_TOKEN``) stays server-side. Issue creation is a hard
dependency: any failure raises ``GitHubIssueError`` and the endpoint maps it to
HTTP 502 — we never silently drop a filed report.
"""
from __future__ import annotations

import os
from typing import Any

import httpx

GITHUB_OWNER = "slabgorb-org"
GITHUB_REPO = "sidequest"
DEFAULT_LABELS: list[str] = ["bug", "in-app-report"]


class GitHubIssueError(RuntimeError):
    """Issue creation failed (missing token, network error, or non-2xx)."""


async def create_issue(
    title: str,
    body: str,
    labels: list[str] | None = None,
    *,
    transport: httpx.BaseTransport | None = None,
) -> dict[str, Any]:
    token = os.environ.get("SIDEQUEST_CI_TOKEN")
    if not token:
        raise GitHubIssueError("SIDEQUEST_CI_TOKEN is not set")

    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/issues"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    payload = {"title": title, "body": body, "labels": labels or list(DEFAULT_LABELS)}
    try:
        async with httpx.AsyncClient(timeout=30.0, transport=transport) as client:
            resp = await client.post(url, headers=headers, json=payload)
    except httpx.HTTPError as exc:
        raise GitHubIssueError(f"request failed: {exc}") from exc

    if resp.status_code not in (200, 201):
        raise GitHubIssueError(f"{resp.status_code}: {resp.text[:500]}")
    data = resp.json()
    return {"url": data["html_url"], "number": data["number"]}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/server/test_bug_report_github_issue.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
cd sidequest-server
git add sidequest/server/github_issue.py tests/server/test_bug_report_github_issue.py
git commit -m "feat(bug-report): GitHub issue creation via REST API"
```

---

### Task 8: `POST /api/bug-report` — endpoint orchestration + wiring

**Files:**
- Create: `sidequest-server/sidequest/server/bug_report.py`
- Modify: `sidequest-server/sidequest/server/rest.py` (register routes just before `return router` in `create_rest_router()`)
- Test: `sidequest-server/tests/server/test_bug_report_endpoint.py`

**Interfaces:**
- Consumes: `upload_bytes`, `object_key`, `R2UploadError` (Task 6); `create_issue`, `GitHubIssueError`, `DEFAULT_LABELS` (Task 7); `compose_body`, `otel_summary`, `scrub`, `tail_server_log` (Tasks 2–5); `publish_event` (existing).
- Produces: `register_bug_report_routes(router: APIRouter) -> None`; endpoint returns `{"issue_url": str, "issue_number": int, "report_id": str}`.

- [ ] **Step 1: Write the failing wiring test**

```python
# sidequest-server/tests/server/test_bug_report_endpoint.py
"""Task 8 — POST /api/bug-report wiring (RED)."""
from __future__ import annotations

import asyncio
from typing import Any

import pytest
from fastapi.testclient import TestClient

from sidequest.telemetry.watcher_hub import WatcherHub, watcher_hub
from tests._helpers.doubles import FakeSocket


@pytest.fixture
def app_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("SIDEQUEST_DATABASE_URL", "postgresql://localhost/test_notreal")
    from sidequest.server.app import create_app

    return TestClient(create_app(), raise_server_exceptions=True)


@pytest.fixture
async def bound_hub() -> WatcherHub:
    watcher_hub.bind_loop(asyncio.get_running_loop())
    async with watcher_hub._lock:  # noqa: SLF001
        watcher_hub._subscribers.clear()  # noqa: SLF001
    return watcher_hub


def _patch_backends(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    import sidequest.server.bug_report as bug_report

    captured: dict[str, Any] = {"uploads": []}

    def fake_upload(key: str, data: bytes, content_type: str) -> str:
        captured["uploads"].append((key, content_type))
        return f"https://cdn.slabgorb.com/{key}"

    async def fake_create_issue(title, body, labels=None, **kw):  # noqa: ANN001, ARG001
        captured["title"] = title
        captured["body"] = body
        return {"url": "https://github.com/slabgorb-org/sidequest/issues/99", "number": 99}

    monkeypatch.setattr(bug_report, "upload_bytes", fake_upload)
    monkeypatch.setattr(bug_report, "create_issue", fake_create_issue)
    return captured


def test_bug_report_route_is_registered(app_client: TestClient) -> None:
    # Missing required fields → 422, proving the route exists (not 404).
    resp = app_client.post("/api/bug-report", data={})
    assert resp.status_code == 422, f"route must be registered; got {resp.status_code}"


def test_bug_report_happy_path_returns_issue_url(
    app_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured = _patch_backends(monkeypatch)
    resp = app_client.post(
        "/api/bug-report",
        data={"title": "Broken dice", "description": "Dice never settle", "session_slug": ""},
        files=[("files", ("shot.png", b"\x89PNG\r\n", "image/png"))],
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["issue_url"] == "https://github.com/slabgorb-org/sidequest/issues/99"
    assert body["issue_number"] == 99
    assert "report_id" in body
    assert len(captured["uploads"]) == 1
    assert "![shot.png]" in captured["body"]


@pytest.mark.asyncio
async def test_bug_report_emits_watcher_event(
    monkeypatch: pytest.MonkeyPatch, bound_hub: WatcherHub
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("SIDEQUEST_DATABASE_URL", "postgresql://localhost/test_notreal")
    _patch_backends(monkeypatch)
    from sidequest.server.app import create_app

    sock = FakeSocket()
    await bound_hub.subscribe(sock)  # type: ignore[arg-type]

    client = TestClient(create_app(), raise_server_exceptions=True)
    resp = client.post(
        "/api/bug-report",
        data={"title": "t", "description": "d", "session_slug": "s1"},
    )
    assert resp.status_code == 201, resp.text
    await asyncio.sleep(0.05)

    created = [e for e in sock.events if e.get("event_type") == "bug_report.created"]
    assert created, f"expected bug_report.created; got {[e.get('event_type') for e in sock.events]}"
    assert created[0]["fields"]["issue_number"] == 99
    assert created[0]["component"] == "bug_report"


def test_bug_report_too_many_files_rejected(
    app_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_backends(monkeypatch)
    files = [("files", (f"s{i}.png", b"x", "image/png")) for i in range(7)]
    resp = app_client.post(
        "/api/bug-report",
        data={"title": "t", "description": "d"},
        files=files,
    )
    assert resp.status_code == 400
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/server/test_bug_report_endpoint.py -v`
Expected: FAIL — route returns 404 / `ModuleNotFoundError: sidequest.server.bug_report`

- [ ] **Step 3: Create the endpoint module**

```python
# sidequest-server/sidequest/server/bug_report.py
"""POST /api/bug-report — the in-app bug reporter's server endpoint.

Flow: validate → upload attachments to R2 (hard dep) → scrub + gather log/OTEL
(best-effort, absence recorded) → compose Markdown → create GitHub issue (hard
dep) → emit ``bug_report.created`` → return the issue URL.
"""
from __future__ import annotations

import json
import logging
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from sidequest.server.bug_report_enrich import compose_body, otel_summary, scrub, tail_server_log
from sidequest.server.github_issue import DEFAULT_LABELS, GitHubIssueError, create_issue
from sidequest.server.r2_upload import R2UploadError, object_key, upload_bytes
from sidequest.telemetry.watcher_hub import publish_event

logger = logging.getLogger(__name__)

MAX_FILES = 6
MAX_FILE_MB = 10
MAX_FILE_BYTES = MAX_FILE_MB * 1024 * 1024
_ALLOWED_EXT = (".log", ".txt", ".json")


def _allowed(f: UploadFile) -> bool:
    if (f.content_type or "").startswith("image/"):
        return True
    return (f.filename or "").lower().endswith(_ALLOWED_EXT)


def register_bug_report_routes(router: APIRouter) -> None:
    @router.post("/api/bug-report", status_code=201)
    async def create_bug_report(  # noqa: PLR0913
        request: Request,
        title: str = Form(...),
        description: str = Form(...),
        session_slug: str = Form(""),
        context_json: str = Form("{}"),
        files: list[UploadFile] = File(default=[]),
    ) -> dict[str, Any]:
        if not title.strip() or not description.strip():
            raise HTTPException(status_code=400, detail="title and description are required")
        if len(files) > MAX_FILES:
            raise HTTPException(status_code=400, detail=f"at most {MAX_FILES} files")

        report_id = uuid4().hex
        attachments: list[tuple[str, str, bool]] = []
        for i, f in enumerate(files):
            data = await f.read()
            if len(data) > MAX_FILE_BYTES:
                raise HTTPException(status_code=400, detail=f"{f.filename or 'file'} exceeds {MAX_FILE_MB} MB")
            if not _allowed(f):
                raise HTTPException(status_code=400, detail=f"{f.filename or 'file'}: unsupported type")
            key = object_key(report_id, i, f.filename or "file")
            try:
                url = upload_bytes(key, data, f.content_type or "application/octet-stream")
            except R2UploadError as exc:
                raise HTTPException(status_code=502, detail=f"attachment upload failed: {exc}") from exc
            attachments.append((f.filename or key, url, (f.content_type or "").startswith("image/")))

        try:
            context = json.loads(context_json) if context_json else {}
            if not isinstance(context, dict):
                context = {}
        except json.JSONDecodeError:
            context = {}

        raw_log = tail_server_log()
        log_text = scrub(raw_log) if raw_log is not None else None
        raw_otel = await otel_summary(session_slug)
        otel_text = scrub(raw_otel) if raw_otel is not None else None

        body = compose_body(
            description=description,
            context=context,
            attachments=attachments,
            log_text=log_text,
            otel_text=otel_text,
            report_id=report_id,
            session_slug=session_slug,
        )

        try:
            issue = await create_issue(title.strip(), body, list(DEFAULT_LABELS))
        except GitHubIssueError as exc:
            raise HTTPException(status_code=502, detail=f"GitHub issue creation failed: {exc}") from exc

        publish_event(
            "bug_report.created",
            {
                "report_id": report_id,
                "issue_number": issue["number"],
                "file_count": len(attachments),
                "session_slug": session_slug,
            },
            component="bug_report",
        )
        logger.info(
            "bug_report.created report_id=%s issue=%s files=%d",
            report_id,
            issue["number"],
            len(attachments),
        )
        return {"issue_url": issue["url"], "issue_number": issue["number"], "report_id": report_id}
```

- [ ] **Step 4: Register the route in `rest.py`**

In `sidequest/server/rest.py`, inside `create_rest_router()`, immediately before the final `return router` statement, add:

```python
    from sidequest.server.bug_report import register_bug_report_routes

    register_bug_report_routes(router)

    return router
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/server/test_bug_report_endpoint.py -v`
Expected: PASS (4 passed)

- [ ] **Step 6: Lint + full-file sanity, then commit**

Run: `cd sidequest-server && uv run ruff check sidequest/server/bug_report.py sidequest/server/bug_report_enrich.py sidequest/server/r2_upload.py sidequest/server/github_issue.py`
Expected: no errors.

```bash
cd sidequest-server
git add sidequest/server/bug_report.py sidequest/server/rest.py tests/server/test_bug_report_endpoint.py
git commit -m "feat(bug-report): POST /api/bug-report endpoint + route wiring + OTEL event"
```

---

### Task 9: UI types

**Files:**
- Create: `sidequest-ui/src/types/bugReport.ts`

**Interfaces:**
- Produces: `BugReportContext` (`{ sessionSlug?, genre?, world?, screen? }`), `BugReportResponse` (`{ issue_url, issue_number, report_id }`).

- [ ] **Step 1: Create the types (no separate test — consumed + compiled by Tasks 10–12)**

```typescript
// sidequest-ui/src/types/bugReport.ts
export interface BugReportContext {
  sessionSlug?: string;
  genre?: string;
  world?: string;
  /** connect | creation | game */
  screen?: string;
}

export interface BugReportResponse {
  issue_url: string;
  issue_number: number;
  report_id: string;
}
```

- [ ] **Step 2: Typecheck**

Run: `cd sidequest-ui && npx tsc --noEmit`
Expected: no new errors.

- [ ] **Step 3: Commit**

```bash
cd sidequest-ui
git add src/types/bugReport.ts
git commit -m "feat(bug-report): UI types for context + response"
```

---

### Task 10: `useBugReport` hook

**Files:**
- Create: `sidequest-ui/src/hooks/useBugReport.ts`
- Test: `sidequest-ui/src/hooks/__tests__/useBugReport.test.ts`

**Interfaces:**
- Consumes: `BugReportContext`, `BugReportResponse` (Task 9).
- Produces: `useBugReport()` → `{ submit(input), status, issueUrl, error, reset }` where `input = { title: string; description: string; files: File[]; context: BugReportContext }` and `status ∈ "idle"|"submitting"|"success"|"error"`. `submit` POSTs `multipart/form-data` to `/api/bug-report`.

- [ ] **Step 1: Write the failing test**

```typescript
// sidequest-ui/src/hooks/__tests__/useBugReport.test.ts
import { renderHook, act, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { useBugReport } from "../useBugReport";

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("useBugReport", () => {
  it("posts multipart to /api/bug-report and exposes the issue url", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ issue_url: "https://github.com/o/r/issues/5", issue_number: 5, report_id: "abc" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => useBugReport());
    await act(async () => {
      await result.current.submit({
        title: "T",
        description: "D",
        files: [new File([new Uint8Array([1, 2])], "shot.png", { type: "image/png" })],
        context: { sessionSlug: "s1", genre: "space_opera", screen: "game" },
      });
    });

    await waitFor(() => expect(result.current.status).toBe("success"));
    expect(result.current.issueUrl).toBe("https://github.com/o/r/issues/5");

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/bug-report");
    expect(init.method).toBe("POST");
    const fd = init.body as FormData;
    expect(fd.get("title")).toBe("T");
    expect(fd.get("session_slug")).toBe("s1");
    expect(fd.getAll("files").length).toBe(1);
    expect(JSON.parse(fd.get("context_json") as string).genre).toBe("space_opera");
  });

  it("surfaces an error when the server responds non-ok", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 502, text: async () => "bad" }));
    const { result } = renderHook(() => useBugReport());
    await act(async () => {
      await result.current.submit({ title: "T", description: "D", files: [], context: {} });
    });
    await waitFor(() => expect(result.current.status).toBe("error"));
    expect(result.current.error).toContain("502");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-ui && npx vitest run src/hooks/__tests__/useBugReport.test.ts`
Expected: FAIL — cannot resolve `../useBugReport`

- [ ] **Step 3: Create the hook**

```typescript
// sidequest-ui/src/hooks/useBugReport.ts
import { useCallback, useState } from "react";
import type { BugReportContext, BugReportResponse } from "@/types/bugReport";

export type BugReportStatus = "idle" | "submitting" | "success" | "error";

export interface BugReportInput {
  title: string;
  description: string;
  files: File[];
  context: BugReportContext;
}

export interface UseBugReportResult {
  submit: (input: BugReportInput) => Promise<void>;
  status: BugReportStatus;
  issueUrl: string | null;
  error: string | null;
  reset: () => void;
}

export function useBugReport(): UseBugReportResult {
  const [status, setStatus] = useState<BugReportStatus>("idle");
  const [issueUrl, setIssueUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const reset = useCallback(() => {
    setStatus("idle");
    setIssueUrl(null);
    setError(null);
  }, []);

  const submit = useCallback(async (input: BugReportInput) => {
    setStatus("submitting");
    setError(null);
    const form = new FormData();
    form.set("title", input.title);
    form.set("description", input.description);
    form.set("session_slug", input.context.sessionSlug ?? "");
    form.set(
      "context_json",
      JSON.stringify({
        ...input.context,
        userAgent: navigator.userAgent,
        viewport: `${window.innerWidth}x${window.innerHeight}`,
        pathname: window.location.pathname,
        appBuild: import.meta.env.MODE,
      }),
    );
    for (const file of input.files) form.append("files", file);

    try {
      const res = await fetch("/api/bug-report", { method: "POST", body: form });
      if (!res.ok) {
        const text = await res.text().catch(() => "");
        setError(`Report failed (${res.status}). ${text}`.trim());
        setStatus("error");
        return;
      }
      const data = (await res.json()) as BugReportResponse;
      setIssueUrl(data.issue_url);
      setStatus("success");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setStatus("error");
    }
  }, []);

  return { submit, status, issueUrl, error, reset };
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-ui && npx vitest run src/hooks/__tests__/useBugReport.test.ts`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
cd sidequest-ui
git add src/hooks/useBugReport.ts src/hooks/__tests__/useBugReport.test.ts
git commit -m "feat(bug-report): useBugReport hook (multipart POST)"
```

---

### Task 11: `BugReportModal` component

**Files:**
- Create: `sidequest-ui/src/components/BugReportModal.tsx`
- Test: `sidequest-ui/src/components/__tests__/BugReportModal.test.tsx`

**Interfaces:**
- Consumes: `useBugReport` (Task 10), `BugReportContext` (Task 9), `Button` from `@/components/ui/button`.
- Produces: `BugReportModal({ open, onClose, context }: { open: boolean; onClose: () => void; context: BugReportContext })`. Enforces ≤ 6 files / 10 MB each; disables submit until title+description present and while submitting; shows the issue link on success.

- [ ] **Step 1: Write the failing test**

```typescript
// sidequest-ui/src/components/__tests__/BugReportModal.test.tsx
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { BugReportModal } from "../BugReportModal";

beforeEach(() => vi.restoreAllMocks());

function open() {
  return render(<BugReportModal open onClose={vi.fn()} context={{ sessionSlug: "s1", screen: "game" }} />);
}

describe("BugReportModal", () => {
  it("disables submit until title and description are filled", async () => {
    open();
    const submit = screen.getByRole("button", { name: /file bug report/i });
    expect(submit).toBeDisabled();
    await userEvent.type(screen.getByLabelText(/title/i), "Broken dice");
    await userEvent.type(screen.getByLabelText(/description/i), "Never settle");
    expect(submit).toBeEnabled();
  });

  it("submits and shows the issue link on success", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ issue_url: "https://github.com/o/r/issues/8", issue_number: 8, report_id: "z" }),
      }),
    );
    open();
    await userEvent.type(screen.getByLabelText(/title/i), "T");
    await userEvent.type(screen.getByLabelText(/description/i), "D");
    await userEvent.click(screen.getByRole("button", { name: /file bug report/i }));
    await waitFor(() => expect(screen.getByRole("link", { name: /view issue/i })).toHaveAttribute(
      "href",
      "https://github.com/o/r/issues/8",
    ));
  });

  it("rejects more than six files", async () => {
    open();
    const input = screen.getByLabelText(/attach files/i) as HTMLInputElement;
    const files = Array.from({ length: 7 }, (_, i) => new File([new Uint8Array([1])], `s${i}.png`, { type: "image/png" }));
    await userEvent.upload(input, files);
    expect(screen.getByText(/at most 6 files/i)).toBeInTheDocument();
  });

  it("does not render when closed", () => {
    render(<BugReportModal open={false} onClose={vi.fn()} context={{}} />);
    expect(screen.queryByLabelText(/title/i)).not.toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-ui && npx vitest run src/components/__tests__/BugReportModal.test.tsx`
Expected: FAIL — cannot resolve `../BugReportModal`

- [ ] **Step 3: Create the component**

```tsx
// sidequest-ui/src/components/BugReportModal.tsx
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { useBugReport } from "@/hooks/useBugReport";
import type { BugReportContext } from "@/types/bugReport";

const MAX_FILES = 6;
const MAX_FILE_BYTES = 10 * 1024 * 1024;

export interface BugReportModalProps {
  open: boolean;
  onClose: () => void;
  context: BugReportContext;
}

export function BugReportModal({ open, onClose, context }: BugReportModalProps) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [fileError, setFileError] = useState<string | null>(null);
  const { submit, status, issueUrl, error, reset } = useBugReport();

  useEffect(() => {
    if (!open) {
      setTitle("");
      setDescription("");
      setFiles([]);
      setFileError(null);
      reset();
    }
  }, [open, reset]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && status !== "submitting") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, status, onClose]);

  if (!open) return null;

  const addFiles = (incoming: FileList | null) => {
    if (!incoming) return;
    const next = [...files, ...Array.from(incoming)];
    if (next.length > MAX_FILES) {
      setFileError(`Attach at most ${MAX_FILES} files.`);
      return;
    }
    const tooBig = next.find((f) => f.size > MAX_FILE_BYTES);
    if (tooBig) {
      setFileError(`${tooBig.name} exceeds 10 MB.`);
      return;
    }
    setFileError(null);
    setFiles(next);
  };

  const canSubmit = title.trim().length > 0 && description.trim().length > 0 && status !== "submitting";

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Report a bug"
      className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget && status !== "submitting") onClose();
      }}
    >
      <div className="w-full max-w-lg rounded-xl bg-background p-5 shadow-xl">
        <h2 className="mb-3 text-lg font-semibold">Report a bug</h2>

        {status === "success" ? (
          <div className="space-y-3">
            <p>Thanks — your report was filed.</p>
            <a
              className="text-primary underline"
              href={issueUrl ?? "#"}
              target="_blank"
              rel="noreferrer"
            >
              View issue
            </a>
            <div className="flex justify-end">
              <Button onClick={onClose}>Close</Button>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            <label className="block text-sm">
              <span className="mb-1 block">Title</span>
              <input
                className="w-full rounded-md border px-2 py-1"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                maxLength={120}
              />
            </label>

            <label className="block text-sm">
              <span className="mb-1 block">Description</span>
              <textarea
                className="min-h-24 w-full rounded-md border px-2 py-1"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </label>

            <label className="block text-sm">
              <span className="mb-1 block">Attach files</span>
              <input
                type="file"
                multiple
                accept="image/*,.log,.txt,.json"
                onChange={(e) => addFiles(e.target.files)}
              />
            </label>
            {files.length > 0 && (
              <ul className="text-xs text-muted-foreground">
                {files.map((f, i) => (
                  <li key={`${f.name}-${i}`} className="flex items-center justify-between">
                    <span>{f.name}</span>
                    <button
                      type="button"
                      className="underline"
                      onClick={() => setFiles(files.filter((_, j) => j !== i))}
                    >
                      remove
                    </button>
                  </li>
                ))}
              </ul>
            )}
            {fileError && <p className="text-xs text-destructive">{fileError}</p>}

            <div className="rounded-md bg-muted p-2 text-xs text-muted-foreground">
              <div className="mb-1 font-medium">Attached automatically</div>
              <div>session: {context.sessionSlug || "—"}</div>
              <div>genre/world: {context.genre || "—"} / {context.world || "—"}</div>
              <div>screen: {context.screen || "—"}</div>
              <div>+ scrubbed server log &amp; OTEL for this session</div>
            </div>

            {error && <p className="text-xs text-destructive">{error}</p>}

            <div className="flex justify-end gap-2">
              <Button variant="ghost" onClick={onClose} disabled={status === "submitting"}>
                Cancel
              </Button>
              <Button
                onClick={() => submit({ title, description, files, context })}
                disabled={!canSubmit}
              >
                {status === "submitting" ? "Filing…" : "File bug report"}
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-ui && npx vitest run src/components/__tests__/BugReportModal.test.tsx`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
cd sidequest-ui
git add src/components/BugReportModal.tsx src/components/__tests__/BugReportModal.test.tsx
git commit -m "feat(bug-report): BugReportModal (form, file caps, success link)"
```

---

### Task 12: `BugReportButton` + mount in `App` (UI wiring)

**Files:**
- Create: `sidequest-ui/src/components/BugReportButton.tsx`
- Modify: `sidequest-ui/src/App.tsx` (import + mount alongside the global banners)
- Test: `sidequest-ui/src/components/__tests__/BugReportButton.test.tsx`

**Interfaces:**
- Consumes: `BugReportModal` (Task 11), `BugReportContext` (Task 9).
- Produces: `BugReportButton({ context }: { context: BugReportContext })` — a fixed 🐞 trigger that toggles the modal.

- [ ] **Step 1: Write the failing wiring test**

```typescript
// sidequest-ui/src/components/__tests__/BugReportButton.test.tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect } from "vitest";
import { BugReportButton } from "../BugReportButton";

describe("BugReportButton", () => {
  it("opens the modal when clicked", async () => {
    render(<BugReportButton context={{ sessionSlug: "s1", screen: "game" }} />);
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /report a bug/i }));
    expect(screen.getByRole("dialog", { name: /report a bug/i })).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-ui && npx vitest run src/components/__tests__/BugReportButton.test.tsx`
Expected: FAIL — cannot resolve `../BugReportButton`

- [ ] **Step 3: Create the button**

```tsx
// sidequest-ui/src/components/BugReportButton.tsx
import { useState } from "react";
import { BugReportModal } from "@/components/BugReportModal";
import type { BugReportContext } from "@/types/bugReport";

export interface BugReportButtonProps {
  context: BugReportContext;
}

export function BugReportButton({ context }: BugReportButtonProps) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button
        type="button"
        aria-label="Report a bug"
        title="Report a bug"
        onClick={() => setOpen(true)}
        className="fixed bottom-3 right-3 z-[9998] flex size-9 items-center justify-center rounded-full border bg-background/90 shadow-md hover:bg-muted"
      >
        <span aria-hidden>🐞</span>
      </button>
      <BugReportModal open={open} onClose={() => setOpen(false)} context={context} />
    </>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-ui && npx vitest run src/components/__tests__/BugReportButton.test.tsx`
Expected: PASS (1 passed)

- [ ] **Step 5: Mount in `App.tsx`**

Add the import near the other component imports at the top of `sidequest-ui/src/App.tsx`:

```tsx
import { BugReportButton } from "@/components/BugReportButton";
```

Then render it once at the top level of the component's returned JSX — alongside the always-present global banners (search for `<ReconnectBanner` / `<OfflineBanner` in the returned tree and place it next to them so it shows on every `SessionPhase`):

```tsx
<BugReportButton
  context={{
    sessionSlug: slug,
    genre: currentGenreRef.current ?? undefined,
    world: currentWorldRef.current ?? undefined,
    screen: phase,
  }}
/>
```

Notes for the implementer: `slug` comes from `useParams()` (already destructured near the top of the component); `currentGenreRef` / `currentWorldRef` are the existing refs used elsewhere in `App.tsx`; `phase` is the `SessionPhase` state. If any identifier name differs in the current file, use the in-scope equivalent — the button only needs best-effort context.

- [ ] **Step 6: Typecheck + run the UI wiring test again**

Run: `cd sidequest-ui && npx tsc --noEmit && npx vitest run src/components/__tests__/BugReportButton.test.tsx`
Expected: no type errors; PASS.

- [ ] **Step 7: Commit**

```bash
cd sidequest-ui
git add src/components/BugReportButton.tsx src/components/__tests__/BugReportButton.test.tsx src/App.tsx
git commit -m "feat(bug-report): global BugReportButton mounted in App chrome"
```

---

### Task 13: Final verification (both repos)

**Files:** none (verification only).

- [ ] **Step 1: Server suite + lint**

Run: `cd sidequest-server && uv run pytest tests/server/test_bug_report_buffered_events.py tests/server/test_bug_report_enrich.py tests/server/test_bug_report_r2_upload.py tests/server/test_bug_report_github_issue.py tests/server/test_bug_report_endpoint.py -v && uv run ruff check sidequest/server/bug_report.py sidequest/server/bug_report_enrich.py sidequest/server/r2_upload.py sidequest/server/github_issue.py sidequest/telemetry/watcher_hub.py`
Expected: all pass; ruff clean.

- [ ] **Step 2: UI suite + build**

Run: `cd sidequest-ui && npx vitest run src/hooks/__tests__/useBugReport.test.ts src/components/__tests__/BugReportModal.test.tsx src/components/__tests__/BugReportButton.test.tsx && npx tsc --noEmit`
Expected: all pass; no type errors.

- [ ] **Step 3: Manual end-to-end (optional, files a real issue)**

With server + client + a live session running, click 🐞, attach a screenshot, submit. Confirm a new issue on `slabgorb-org/sidequest` with the embedded screenshot and scrubbed `<details>` logs, then **close the test issue**. (No dry-run mode by design — the automated tests above cover the mocked path.)

---

## Self-Review

**Spec coverage:**
- File upload → R2 dedicated folder → Tasks 6, 8. ✓
- Scrub + inline collapsed log/OTEL tail → Tasks 2, 3, 4, 5. ✓
- Hard-dep abort (R2/GitHub) vs best-effort enrichment absence → Task 8 (502 paths) + Task 5 (absence notes). ✓
- GitHub issue via server-side PAT → Task 7. ✓
- `bug_report.created` OTEL event → Task 8 + wiring test. ✓
- Global button, every screen → Task 12 (mount next to global banners). ✓
- Wiring tests (server route reachable; UI button opens modal + POST) → Task 8, Tasks 10–12. ✓
- No dry-run mode → omitted by design (Task 13 note). ✓
- Public-repo image hosting via CDN → Task 6 `cdn_base` (ignores local mode because the object is really in R2). ✓

**Placeholder scan:** No TBD/TODO; every code step contains full content; run commands have expected output. ✓

**Type consistency:** `upload_bytes(key, data, content_type)`, `object_key(report_id, index, filename)`, `create_issue(title, body, labels, *, transport)`, `compose_body(*, description, context, attachments, log_text, otel_text, report_id, session_slug)`, `otel_summary(slug, limit)`, `tail_server_log(n_lines)`, `buffered_events(slug)`, and the endpoint response `{issue_url, issue_number, report_id}` are used identically across the endpoint (Task 8), the UI hook (Task 10), and their tests. ✓
