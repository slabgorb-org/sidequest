# Narrative

## Problem Statement
**Problem:** The developer quick-reference guide (CLAUDE.md) contained a dead link. The `just otel` command description said it opened an "OTEL dashboard" at a server route (`/dashboard`) that no longer exists — it was deleted in PR #859. The real observability panel lives inside the React Inspector at `localhost:5173/#/dashboard`. **Why it matters:** When a developer types `just otel` and then goes looking in the wrong place, they waste time and may conclude the observability tooling is broken. During the quest-blindness investigation (the live playtest that revealed quests weren't being tracked), this stale comment was a small but concrete friction point discovered along the way.

---

## What Changed
One line in the developer guide was updated. Previously, it told developers that `just otel` opened an "OTEL GM panel in the server dashboard" — a page that was torn down months ago. Now it correctly says `just otel` opens the **React Inspector** at `localhost:5173/#/dashboard`, which is the actual live observability surface the team uses. That's it: one comment, one correct URL, no code changes.

---

## Why This Approach
Documentation drift is cheap to fix and expensive to leave. The correct URL was already in the `justfile` recipe (the script that runs the command) — it was just missing from the human-readable summary above it. The fix aligned the two. No design decision was required; the answer was already authoritative in the code. Making this a standalone 1-point story rather than a footnote on a bigger story keeps it traceable — if this comment drifts again, there's a clear before/after in the git history.

---

## Before/After
| | Old behavior | New behavior |
|---|---|---|
| **CLAUDE.md line 190** | `just otel  # Opens the OTEL GM panel in the server HTML dashboard` (dead route, deleted in #859) | `just otel  # Opens the OTEL GM panel in the React Inspector (localhost:5173/#/dashboard)` |
| **Developer experience** | Types `just otel`, sees the browser open, doesn't know where to look; may try navigating the server at `:8765/dashboard` and hit a 404 | Types `just otel`, browser opens the React Inspector directly; OTEL spans are visible immediately |
| **Trustworthiness of the guide** | Guide says one thing, running system does another | Guide matches the justfile recipe and the live system |
| **Verification during incidents** | Extra friction — developer has to remember or rediscover the correct URL | Zero friction — one command, correct destination, no tribal knowledge required |
