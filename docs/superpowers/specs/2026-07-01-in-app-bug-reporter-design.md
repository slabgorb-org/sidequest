# In-App Bug Reporter — Design

- **Date:** 2026-07-01
- **Status:** Approved (design), pending implementation plan
- **Repos touched:** `sidequest-ui`, `sidequest-server`

## Summary

A player-facing bug reporter. A global 🐞 button, present on every screen, opens a
modal where the player writes a title + description and attaches their own screenshot
files (no programmatic pixel capture). On submit the client POSTs a multipart request
to the server, which:

1. uploads the attached files to a dedicated R2 folder (`bug-reports/<report_id>/`),
2. enriches the report with a scrubbed tail of the server log and a scrubbed OTEL
   summary for the active session,
3. creates a GitHub issue on `slabgorb-org/sidequest` embedding the screenshots and
   the collapsed logs, and
4. returns the issue URL to the client.

The GitHub token and R2 credentials stay server-side. The server already has every
dependency this needs except `boto3` (added).

## Context / prior art

- **Target repo is PUBLIC** (`slabgorb-org/sidequest`, issues enabled). Everything
  attached — screenshots, logs, OTEL — is world-readable, and the R2 CDN is public.
  This is why enrichment is **scrubbed** before it leaves the server.
- **Client→server incident precedent:** `handlers/client_error.py` already sends a
  `CLIENT_ERROR` over the WebSocket when a render subtree crashes. The bug reporter is
  the *deliberate, user-initiated* sibling — but it uses a REST endpoint, not the
  socket, because it carries file uploads.
- **OTEL is already buffered server-side:** `telemetry/watcher_hub.py` keeps a
  per-session ring buffer (`_session_buffers`, ~2000 events/slug) plus a global infra
  bucket keyed `None`. That is the OTEL enrichment source — no new capture needed, only
  a public read accessor.
- **R2:** bucket `sidequest`, S3-compatible via boto3 using `R2_ACCESS_KEY_ID` /
  `R2_SECRET_ACCESS_KEY` / `R2_S3_ENDPOINT` (all in the server env). Objects are served
  publicly at `https://cdn.slabgorb.com/<key>` (`SIDEQUEST_ASSET_BASE_URL` default).
  Upload pattern mirrors `scripts/r2_sync_packs.py::_build_client`.
- **GitHub:** `SIDEQUEST_CI_TOKEN` (a fine-grained PAT) is in the env; the server uses
  `httpx` (already a dependency) to hit the GitHub REST API.
- **Server log:** written by a shell tee, not the app — convention path
  `~/.sidequest/logs/sidequest-server.log`, overridable via `SIDEQUEST_SERVER_LOG`.

## The hard-dependency vs best-effort line (load-bearing decision)

Per CLAUDE.md "No Silent Fallbacks," failures never silently degrade. We distinguish:

- **Hard dependencies — R2 upload and GitHub issue creation.** If either fails, the
  request **aborts** with HTTP `502` and a message the client surfaces. We never post a
  half-formed issue or swallow the error. R2 being unreachable is itself a larger
  incident, and aborting makes that loud.
- **Best-effort enrichment — server-log tail and OTEL summary.** Their *absence* is
  **recorded explicitly in the issue body** ("no active session — no OTEL captured";
  "server log not found at `<path>`"). This is not a fallback: nothing alternative is
  substituted, and nothing is hidden. Missing enrichment must never lose a bug report,
  because a description + screenshots filed from a pre-session screen is still valuable.

## Architecture & data flow

```
[Player clicks 🐞 (global)]
  → BugReportModal (title, description, file dropzone, read-only context preview)
  → POST /api/bug-report   (multipart/form-data)
      server pipeline (sidequest/server/bug_report.py):
        1. validate fields + files; mint report_id = uuid4().hex
        2. upload each file → R2 key  bug-reports/<report_id>/<sanitized_name>
             → public url  https://cdn.slabgorb.com/bug-reports/<report_id>/<name>
             (any failure → abort 502)
        3. enrich:
             scrub(tail_server_log(N))        [best-effort; absence noted]
             scrub(otel_summary(session_slug)) [best-effort; absence noted]
             client context (from context_json)
        4. compose Markdown issue body (image embeds + collapsed <details> logs,
             budgeted to GitHub's 65536-char limit, loud truncation marker)
        5. create GitHub issue (httpx + SIDEQUEST_CI_TOKEN)  (failure → abort 502)
        6. emit watcher event  bug_report.created  (component "bug_report")
        7. return { issue_url, issue_number, report_id }
  → modal shows success toast w/ clickable issue link (or the loud error)
```

## Component design

### UI (`sidequest-ui`)

- **`src/components/BugReportButton.tsx`** — the global 🐞 affordance, mounted in the
  top-level app layout (root, not `GameBoard`) so it is present on the Connect,
  Character Creation, and in-session screens alike. Unobtrusive, keyboard-accessible,
  no time pressure (Alex-friendly). Opens the modal.
- **`src/components/BugReportModal.tsx`** — form:
  - *Title* (required, ≤ 120 chars), *Description* (required, textarea).
  - *File dropzone* — drag/drop + click; accepts `image/*`, `.log`, `.txt`, `.json`;
    shows thumbnails/filenames with remove buttons; per-file cap **10 MB**, **≤ 6
    files** (enforced client- and server-side).
  - *Read-only "what we'll attach" context preview* — session slug, genre/world,
    round/interaction, current screen — so the player sees exactly what's collected.
  - Submit / Cancel; inline `submitting` / `success` (issue link) / `error` states.
- **`src/hooks/useBugReport.ts`** — builds `FormData`, does the multipart POST to
  `/api/bug-report`, tracks `submitting|success|error`, exposes `{ issueUrl }`.
- **Context collection** — from existing game state (session_slug, genre, world,
  round/interaction, route/screen) plus `navigator.userAgent`, viewport, and app build;
  serialized into a `context_json` form field.
- No new dependencies — plain `fetch` + `FormData`.
- **Types:** `src/types/bugReport.ts` — `BugReportContext`, request/response shapes.

### Server (`sidequest-server`)

- **`sidequest/server/bug_report.py`** — `register(router)` mounts
  `POST /api/bug-report`. Form fields: `title: str`, `description: str`,
  `session_slug: str = ""`, `context_json: str = "{}"`, `files: list[UploadFile] = []`.
  Orchestrates the pipeline; emits the `bug_report.created` watcher event. Called from
  `create_rest_router()` in `rest.py` (keeps `rest.py` from growing).
- **`sidequest/server/r2_upload.py`** — `_build_client()` (from `R2_*` env, mirrors the
  scripts helper) + `upload_bytes(key, data, content_type) -> public_url`. Public URL is
  `f"{base}/{key}"` where `base = SIDEQUEST_ASSET_BASE_URL or https://cdn.slabgorb.com`.
  Adds `boto3` to server `pyproject.toml`. (Routing the upload through the daemon was
  rejected: the reporter must work even when media services are down.)
- **`sidequest/server/bug_report_enrich.py`**:
  - `tail_server_log(n_lines=200) -> str | None` — last N lines (default
    `LOG_TAIL_LINES = 200`) of `$SIDEQUEST_SERVER_LOG` (default
    `~/.sidequest/logs/sidequest-server.log`); `None` if the file is absent.
  - `otel_summary(slug, limit=150) -> str | None` — `watcher_hub.buffered_events(slug)`,
    compact one-line-per-event format (ts, component, event name, key fields), last
    `OTEL_EVENT_LIMIT = 150` events; `None` when `slug == ""` or the buffer is empty.
  - `scrub(text) -> str` — regex-strips secret shapes (`github_pat_…`, `gho_/ghp_/ghs_`,
    `sk-ant-…`, `sk-…`, `AKIA…`, `Bearer …`) **and** replaces the literal values of
    known secret env vars (`SIDEQUEST_CI_TOKEN`, `R2_SECRET_ACCESS_KEY`,
    `R2_ACCESS_KEY_ID`, `ANTHROPIC_API_KEY`) if they appear verbatim; rewrites
    `str(Path.home())` → `~`.
  - `compose_body(...)` — assembles the Markdown (see below), budgeting the log/OTEL
    tails against the 65536-char limit with a loud `…(truncated)` marker.
- **`sidequest/telemetry/watcher_hub.py`** — add public
  `buffered_events(slug: str | None) -> list[dict]`: the slug's bucket merged with the
  global `None` infra bucket, ordered by the monotonic `_seq`; read-only.
- **`sidequest/server/github_issue.py`** — `create_issue(title, body, labels) ->
  {url, number}` via httpx `POST https://api.github.com/repos/slabgorb-org/sidequest/issues`
  with `Authorization: Bearer $SIDEQUEST_CI_TOKEN`, `Accept: application/vnd.github+json`.
  Owner/repo/labels are module constants. Non-2xx → raise (pipeline maps to 502).

### Issue body format

- **Title:** the user's title verbatim. **Labels:** `bug`, `in-app-report`.
- **Body (in order):**
  1. Description (verbatim user text).
  2. **Context** table — session slug, genre/world, round/interaction, screen, app
     build, userAgent, timestamp.
  3. **Attachments** — `![name](cdn-url)` for image files, `[name](cdn-url)` links
     otherwise.
  4. `<details><summary>Server log (last N lines, scrubbed)</summary>` fenced block —
     or the explicit "server log not found at `<path>`" note.
  5. `<details><summary>OTEL — session &lt;slug&gt; (last M events, scrubbed)</summary>`
     — or the explicit "no active session — no OTEL captured" note.
  6. Footer: `report_id`, "Filed from the in-app bug reporter."

## Error handling & edge cases

| Situation | Behavior |
|---|---|
| R2 upload fails (any file) | Abort `502`, clear message; no issue created. |
| GitHub API fails | Abort `502` surfacing GitHub's error. (R2 objects already uploaded are left as orphans — cheap; acceptable.) |
| No active session (`slug == ""`) | OTEL section records "no active session — no OTEL captured." Succeeds. |
| Server log missing/unreadable | Log section records "server log not found at `<path>`." Succeeds. |
| File too large / too many / wrong type | Rejected loudly, client- **and** server-side (`400`). |
| Body exceeds 65536 chars | Log/OTEL tails budgeted + truncated with a loud `…(truncated)` marker. |
| Local asset mode (no public CDN) | Known limitation: embedded image URLs won't resolve for GitHub. The reporter targets the CDN-backed deployment. Noted, not worked around. |

- **Auth:** the endpoint is unauthenticated like the other `/api/*` routes (ADR-119
  identity is partial) — acceptable for the small-group deployment; documented as a
  known limitation.

## OTEL (CLAUDE.md observability principle)

The pipeline emits a `bug_report.created` watcher event (component `bug_report`) with
`report_id`, `issue_number`, `file_count`, and `session_slug`, so the GM panel shows the
reporter firing end-to-end — the lie detector confirms the subsystem is engaged.

## Testing (CLAUDE.md: every suite needs a wiring test)

### Server (pytest)
- `scrub()` strips each secret shape and each known literal env value; rewrites home path.
- `otel_summary()` formats buffered events; `slug == ""` → `None`; empty buffer → `None`.
- `tail_server_log()` returns the last N lines; missing file → `None`.
- `compose_body()` embeds images vs links correctly; respects the char budget and emits
  the loud truncation marker.
- `github_issue.create_issue()` with httpx mocked (no live call); non-2xx raises.
- `r2_upload.upload_bytes()` with boto3 mocked; returns the expected public URL.
- **Wiring test:** `POST /api/bug-report` is registered and reachable via FastAPI
  `TestClient`; a happy path (R2 + GitHub mocked) returns `issue_url` **and** emits the
  `bug_report.created` watcher event.

### UI (vitest)
- `BugReportModal` renders, validates required fields, adds/removes files, disables
  submit while sending, shows the success link and the error state.
- `useBugReport` posts `FormData` and surfaces success/error.
- **Wiring test:** `BugReportButton` is mounted in the app chrome and opens the modal.

### Manual
- File one real report against a running server; confirm the issue appears on
  `slabgorb-org/sidequest` with embedded screenshot and scrubbed logs; close the test
  issue afterward. (No dry-run mode — mocked tests cover the automated path.)

## Out of scope (YAGNI)

- Programmatic pixel/screen capture (`getDisplayMedia`, `html2canvas`).
- Presigned direct-to-R2 upload / CORS plumbing.
- Rate limiting / abuse controls.
- Routing bug reports to per-subrepo trackers (single tracker: this repo).
- A dry-run mode.

## New / modified files

**sidequest-server**
- `sidequest/server/bug_report.py` (new)
- `sidequest/server/r2_upload.py` (new)
- `sidequest/server/bug_report_enrich.py` (new)
- `sidequest/server/github_issue.py` (new)
- `sidequest/server/rest.py` (modified — call `bug_report.register(router)`)
- `sidequest/telemetry/watcher_hub.py` (modified — add `buffered_events`)
- `pyproject.toml` (modified — add `boto3`)
- `tests/server/test_bug_report_*.py` (new)

**sidequest-ui**
- `src/components/BugReportButton.tsx` (new)
- `src/components/BugReportModal.tsx` (new)
- `src/hooks/useBugReport.ts` (new)
- `src/types/bugReport.ts` (new)
- top-level app layout (modified — mount `BugReportButton`)
- `src/**/__tests__/BugReport*.test.tsx` (new)
