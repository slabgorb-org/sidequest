---
story_id: "67-6"
jira_key: ""
epic: "67"
workflow: "tdd"
---
# Story 67-6: Authenticated player identity via Cloudflare Access — separate player-identity from character-name key (ADR-037)

## Story Details
- **ID:** 67-6
- **Jira Key:** (none — SideQuest is personal, no Jira)
- **Workflow:** tdd
- **Type:** feature
- **Points:** 5
- **Priority:** p2
- **Repos:** sidequest-server, sidequest-ui
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd (executed via the superpowers brainstorm → spec → plan → subagent-driven-development flow, not the pf phased lane)
**Phase:** review
**Status:** in_review — both PRs open against `develop`, awaiting external review + merge.

### Execution shape
This story was designed and implemented in a single SM-coordinated session using the superpowers track:
1. **brainstorming** → settled three design decisions (local-dev identity = per-player Host names; storage = room-only ephemeral; cleanup = seam+repoint, keep `sd.player_name`).
2. **writing-plans** → 8 TDD tasks grounded in exact code anchors.
3. **subagent-driven-development** → fresh implementer per task + two-stage review (spec compliance, then code quality) per task, then a holistic final review.

## Artifacts
- **Spec:** `docs/superpowers/specs/2026-05-31-67-6-player-identity-design.md`
- **Plan:** `docs/superpowers/plans/2026-05-31-67-6-player-identity.md`
- **ADR:** ADR-119 (`docs/adr/119-authenticated-player-identity.md`) — under the ADR-037 umbrella. Live on `main`.
- **Server PR:** https://github.com/slabgorb/sidequest-server/pull/553 → `develop`
- **UI PR:** https://github.com/slabgorb/sidequest-ui/pull/310 → `develop`
- **Branch:** `feat/67-6-player-identity` (both subrepos, off `origin/develop`)

## Story Context
**Title:** Authenticated player identity via Cloudflare Access email — separate player-identity from character-name key (ADR-037)

**Problem:** Player display identity was derived from a user-typed `payload.player_name`, which in MP equals the character name — so `_SessionData.player_name` was overloaded as both display identity and the seated-character POV key. PARTY_STATUS fabricated peer identity as `char.core.name`, producing the doubled "X — X" header (67-4 patched only the UI symptom). The app sits behind Cloudflare Zero Trust, which injects `Cf-Access-Authenticated-User-Email`, but it was never read.

**Solution (three named concepts):** `player_id` (per-socket key), **player_identity** (authenticated email, `Cf-Access-Authenticated-User-Email` → `Host` (port-stripped) → raise), **character perspective** (`snapshot.player_seats[player_id]`). Identity is room-only/ephemeral (`SessionRoom._player_identities` behind a locked accessor), never persisted; resolved once per socket at the WS boundary (close 1008 if unresolvable); PARTY_STATUS carries a nullable `player_identity`; UI renders the suffix from it; `player_identity_resolved` watcher event emits source only (no PII).

## Delivery Summary

**8 tasks, all per-task spec + quality reviewed; holistic final review = MERGE-READY.**

Server (`feat/67-6-player-identity`, commits `12ef4ce`..`48c473d`):
- `sidequest/server/player_identity.py` — resolver (`resolve_player_identity`, `identity_source`, `MissingPlayerIdentityError`); port-stripping + IPv6-safe.
- `sidequest/server/session_room.py` — `_player_identities` private store + locked `get_player_identity` + last-socket-gone cleanup (survives transient multi-socket disconnect).
- `sidequest/server/websocket.py` — `resolve_identity_or_close` + pre-accept gate (fail-loud 1008).
- `sidequest/server/websocket_session_handler.py` — `attach_room_context` identity params; `perspective_character_name` accessor + repoint of the lone `sd.player_name` perspective abuse (wssh ~2590).
- `sidequest/handlers/connect.py` — `bind_player_identity` + `player_identity_resolved` watcher (source only, no PII).
- `sidequest/protocol/models.py` — `PartyMember.player_identity` (nullable).
- `sidequest/server/views.py` — PARTY_STATUS threads identity per member via the accessor; no more character-name fabrication.

UI (`feat/67-6-player-identity`, commits `fe1f2d6`, `ebd52a7`):
- `player_identity?` through `PartyMemberPayload` → `CharacterSummary` → `CharacterSheetData`.
- `src/lib/partyStatusMapping.ts` (new, extracted + unit-tested pure mappers) — and **invoked** in `App.tsx` (review caught the first cut declaring the field but never populating it — fixed).
- `CharacterPanel` suffix sourced from `player_identity || player_id`, suppressed when equal to the character name or single-player; disconnected peer → no suffix.

## Test Status
- All 67-6 tests green: `test_player_identity.py`, `test_player_identity_wiring.py`, `test_multiplayer_party_status.py` (server); `partyStatusMapping.test.ts`, `CharacterPanel.test.tsx` (UI). Wiring tests mutation-verified (connect→room, views→field, App.tsx→field).
- Full server suite: **9364 passed**. **6 failures are pre-existing/environmental in unrelated subsystems** (`test_71_31_space_opera_culture_doctrine` + pack validators) — content↔server version skew, **zero overlap with this diff** (confirmed via `git diff origin/develop...HEAD --name-only`). Expected to clear in content-synced CI. Also 2 ruff I001 nits in an unrelated lore test (not this diff).
- PII verified excluded from telemetry/logs/saves; No Silent Fallbacks honored (1008 close on unresolvable).

## Delivery Findings
- **Process (non-blocking):** a subagent force-pushed `origin/feat/67-6-player-identity` (amend + `--force-with-lease`) during the lint-fix loop without explicit auth — flagged to the operator; contained (isolated feature branch, develop/main untouched). Remaining implementers were instructed to commit locally only.
- **Review catch (resolved):** the UI's first cut declared `player_identity` across all types but App.tsx never populated it (feature would have shipped inert) — caught by code-quality review, fixed by extracting + invoking pure mappers, mutation-verified.
- **Cross-task seam (verified):** connected-peer identity display hinges on `slot_to_player_id()` inverse == bind-time `player_id`; final review traced + a test now pins it.

## Out of scope (deferred)
- Making `player_id` stable across reconnects (epic-67 presence work).
- Persisting identity to saves.
- Full rename/retire of `sd.player_name`.
- Local MP requires per-player Host names (`player1.local`, etc.) in `/etc/hosts` — dev-setup note, not engine work.

## Next steps for finish
1. External review + merge of PR #553 (server) and #310 (UI) into `develop`.
2. Confirm the 6 environmental suite failures are green in content-synced CI (they belong to 71-31 / pack-validator, not this story).
3. Run `pf sprint story finish 67-6` to archive this session + mark done after both PRs merge.
