---
story_id: "118-8"
jira_key: ""
epic: "118"
workflow: "tdd"
---
# Story 118-8: Fate FATE_ACTION auth-bypass: drive seat resolution from authenticated identity, not msg.player_id (ADR-119) + sanitize skill field

## Story Details
- **ID:** 118-8
- **Jira Key:** (no Jira integration)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-15T14:17:42Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-15T13:53:26Z | 2026-06-15T13:55:15Z | 1m 49s |
| red | 2026-06-15T13:55:15Z | 2026-06-15T14:04:25Z | 9m 10s |
| green | 2026-06-15T14:04:25Z | 2026-06-15T14:09:01Z | 4m 36s |
| review | 2026-06-15T14:09:01Z | 2026-06-15T14:17:42Z | 8m 41s |
| finish | 2026-06-15T14:17:42Z | - | - |

## Sm Assessment

**Story:** 118-8 — Fate FATE_ACTION auth-bypass. HIGH-severity security finding surfaced during the 118-3 (F3c) review by reviewer-security (high confidence). The bug is PRE-EXISTING (the seat-resolution lines are unchanged by the 118-3 diff) but 118-3 amplified the impact: a spoofer now receives the victim's roll result. Filed p1 so it isn't lost. Relates to ADR-119 (Authenticated Player Identity, partial) and ADR-047 (Prompt Injection Sanitization).

**Scope (server-only, tdd, 3pt):**
- Drive `FATE_ACTION` seat resolution from authenticated identity (`sd.player_id` / connection-bound PC), never from `msg.player_id` in the inbound payload.
- Regression coverage: a spoofed `msg.player_id` must fail loudly or resolve to the authenticated PC — never act as another seat.
- Sanitize the `FateActionPayload.skill` field at the seal site per ADR-047 (latent injection vector in a player-controlled string).

**Routing:** tdd / phased → next phase `red`, owner **tea**. TEA writes the failing tests for the three ACs above (auth-bound seat resolution, anti-spoof regression, skill-field sanitization) before any implementation.

**Notes for downstream:** No Jira — YAML-driven sprint only. Branch `feat/118-8-fate-action-auth-bypass` is live in sidequest-server off `develop`. Honor SOUL "No Silent Fallbacks" — a spoof attempt should fail loudly, not silently degrade to the authenticated seat unless that's the deliberate, tested behavior. Confirm whether the ADR-047 sanitizer is already applied elsewhere on this path before adding a second pass (avoid double-sanitization).

## TEA Assessment

### Red Phase (test writing)

**Tests Required:** Yes
**Reason:** Security regression — needs failing tests that prove the auth-bypass and the latent skill-injection before Dev touches code.

**Test Files:**
- `tests/server/test_fate_action_auth_bypass.py` — drives the REAL registered `FateActionHandler` and asserts on the sealed-commit ledger (the barrier is held OPEN by a second un-acting PC so the commit persists for inspection). No source-text wiring asserts (server CLAUDE.md).

**Tests Written:** 6 tests covering 3 ACs (3 RED bug-provers + 3 GREEN regression guards)
**Status:** RED (3 failing, ready for Dev) — verified `3 failed, 3 passed` via `uv run pytest -n0`

RED (must go green after the fix):
- `test_spoofed_player_id_acts_as_authenticated_pc_not_victim` — AC#1: spoofed `msg.player_id=p2` must seal as the authenticated PC (Hero), `sd.player_id` sole source. Fails today: `assert 'Rival' == 'Hero'`.
- `test_spoofed_player_id_never_seats_the_victim` — AC#2: security invariant — a spoof must never attribute an action to the victim seat. Robust to either fix shape (act-as-authenticated OR reject-loud). Fails today.
- `test_malicious_skill_is_sanitized_at_seal_site` — AC#3: `commit.skill == sanitize_player_text(skill)` (ADR-047). Fails today: raw `<system>..</system>Fight` sealed verbatim.

GREEN guards (must STAY green — catch over-correction):
- `test_authenticated_player_acts_as_own_seat_not_characters_zero` — legit p2 acts as Rival, not a lazy `characters[0]` fallback.
- `test_empty_inbound_player_id_resolves_to_authenticated_seat` — empty inbound player_id → authenticated seat (the common client case).
- `test_clean_skill_name_is_preserved_unmangled` — sanitization is idempotent on clean skill names.

### Rule Coverage

| Rule (.pennyfarthing/gates/lang-review/python.md) | Test(s) | Status |
|------|---------|--------|
| #11 Security: input validation at boundaries (untrusted identity) | `test_spoofed_player_id_acts_as_authenticated_pc_not_victim`, `test_spoofed_player_id_never_seats_the_victim` | failing |
| #11 Security: input validation at boundaries (free-text injection) | `test_malicious_skill_is_sanitized_at_seal_site` | failing |
| #6 Test quality (no vacuous assertions) | `assert expected != malicious` self-guard in the sanitize test | passing |

**Rules checked:** #11 (the load-bearing boundary-validation rule for this story) and #6 have direct test coverage. #1–#5, #7–#10, #12–#13 are Dev-implementation-side concerns not assertable from the test file for this change.
**Self-check:** 0 vacuous tests — every test asserts a specific value; the sanitize test guards against a vacuous pass by asserting the input genuinely differs from its sanitized form.

**Handoff:** To Dev (Agent Smith) for the GREEN implementation.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest/handlers/fate_action.py` — seat resolution now uses `sd.player_id` as the SOLE identity source (was `getattr(msg, "player_id", "") or sd.player_id`). A non-empty inbound `msg.player_id` that disagrees with the authenticated id is logged (`warning`) and surfaced to the GM panel as a `fate_action_player_id_spoof_rejected` watcher event (OTEL principle), then the action proceeds as the authenticated PC.
- `sidequest/server/dispatch/fate_conflict.py` — `dispatch_fate_action` now seals `skill=sanitize_player_text(payload.skill)` (ADR-047). The skill-rating lookup still keys on the raw value (dict-key match); only the value stored on `FateSealedCommit` is sanitized.

**Tests:** 6/6 target tests passing (GREEN); broader Fate handler/conflict/dispatch suite 43/43 passing (no regressions). Changed files clean on `ruff check`, `ruff format --check`, and `pyright` (0 errors).

**ACs:**
- AC#1 (sole-source seat resolution) — met; `sd.player_id` is the only identity source.
- AC#2 (anti-spoof regression) — met; spoofed inbound id never seats the victim.
- AC#3 (ADR-047 skill sanitization at seal site) — met.

**Branch:** `feat/118-8-fate-action-auth-bypass` (pushed)

**Handoff:** To Reviewer (The Merovingian) for the review phase.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (2 structural questions) | both questions verified resolved by Reviewer |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings (assessed by Reviewer) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings (assessed by Reviewer) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings (assessed by Reviewer) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings (assessed by Reviewer) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings (assessed by Reviewer) |
| 7 | reviewer-security | Yes | findings | 2 (target HIGH→MEDIUM, aspect_text MEDIUM) | confirmed 2, both downgraded w/ evidence + filed as out-of-scope follow-ups; 0 blocking |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings (assessed by Reviewer) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings (assessed by Reviewer) |

**All received:** Yes (2 enabled returned; 7 disabled via `workflow.reviewer_subagents` and assessed directly by the Reviewer)
**Total findings:** 2 confirmed (both downgraded with line-level evidence and filed as out-of-scope, pre-existing follow-ups), 0 dismissed, 0 blocking

## Reviewer Assessment

**Verdict:** APPROVED

The story delivers all three scoped ACs correctly with zero regressions; the security
specialist confirms the headline auth-bypass (ADR-119) is **clean — `sd.player_id` is
the sole identity source end-to-end**. The two security findings concern *pre-existing,
out-of-scope* sibling fields (`target`, `aspect_text`) that are already defended at every
active narrator boundary; both are filed as follow-ups, neither blocks (see severity table
+ Devil's Advocate).

**Data flow traced:**
- *Identity:* inbound `msg.player_id` → (118-8) read ONLY for the spoof telemetry branch, NEVER for attribution → `acting_player_id = sd.player_id` (server-authenticated) → `player_seats[acting_player_id]` → PC → `dispatch_fate_action(actor_name=...)`. `dispatch_fate_action` has no `player_id` param/reference. Spoof is structurally impossible. Safe.
- *Skill text:* `payload.skill` → raw value drives the skill-rating dict lookup (`fate_conflict.py:753`, correct key match) → `sanitize_player_text(payload.skill)` stored on `FateSealedCommit.skill` (`:776`). Sanitize lands AFTER the lookup; legit skills unaffected, injection neutralized in the stored value. Safe.

**Observations (≥5, tagged by domain — disabled specialists assessed by Reviewer):**
- `[SEC]` **Auth-bypass fix is correct and complete.** `fate_action.py:67` `acting_player_id = sd.player_id`; inbound id used only in the spoof branch. reviewer-security: "ADR-119 clean … sd.player_id truly the sole identity source." CONFIRMED clean.
- `[SEC]` **`commit.target` unsanitized into `_resolve_attack` hints** (`fate_conflict.py:521-547`). Specialist rated HIGH. **Downgraded to MEDIUM** — evidence: `_resolve_attack` raises `FateConflictError` at `find_creature_core(commit.target)` (~line 503) BEFORE any hint interpolates `commit.target`; a free-text injection target never matches a seated creature, so it raises → client error → never reaches the narrator. Active exploit requires a pre-existing maliciously-*named* actor (a chargen-surface issue). Pre-existing + out of scope (story AC scopes to `skill`). Filed as follow-up. Not dismissed — documented.
- `[SEC]` **Raw `aspect_text` on the commit/struct** (`fate_conflict.py:781`). Specialist MEDIUM/latent. Confirmed **latent**: sanitized at the hint producer (`_resolve_create_advantage` 590/606) AND at the narrator-prompt projection (`fate_projection.py:65`, "sanitize at this single source of truth"); raw persists only on the F3a display-only projection (client UI, not the LLM). Pre-existing + out of scope. Filed as follow-up.
- `[SILENT]` **No silent fallback introduced.** The spoof branch is loud by design — `logger.warning` + `fate_action_player_id_spoof_rejected` watcher event — then proceeds deliberately as the authenticated PC (documented, tested). No swallowed exceptions. VERIFIED — `fate_action.py:69-90`.
- `[EDGE]` **Empty `sd.player_id` edge is non-regressive.** If `sd.player_id == ""`, `player_seats.get("")` → None → `characters[0]` fallback — identical to pre-fix behavior when `msg.player_id` was also empty. No new failure mode. VERIFIED.
- `[TEST]` **Strong test net.** Drives the real registered `FateActionHandler`, asserts on the observable sealed-commit ledger (no source-text wiring), barrier held open for inspection, and the sanitize test guards against vacuity (`assert expected != malicious`). 6/6 green; 43 broader Fate tests green. Minor optional gaps (no test for empty `sd.player_id` or spoof-at-nonseated-id) — LOW, non-blocking.
- `[DOC]` **Watcher op name nuance.** `fate_action_player_id_spoof_rejected` says "rejected" though the *action* proceeds — it is the spoofed *identity* that is rejected. The adjacent comment + `recovery: auth_identity_enforced` clarify. LOW nit, not worth a change.
- `[TYPE]` **No new types; defensive read is fine.** `inbound_player_id = getattr(msg, "player_id", "") or ""` is belt-and-suspenders on an already-`str` field, consistent with the handler's existing `getattr` style. pyright clean. VERIFIED.
- `[SIMPLE]` **Proportionate, not over-engineered.** The ~20-line spoof-detection block is observability mandated by the OTEL principle (Dev logged it as a deviation). Reasonable for a security subsystem.
- `[RULE]` **lang-review/python compliant.** #11 input-validation-at-boundaries (the fix itself) ✓; #4 logging — `warning` level for a client-controlled event ✓, lazy `%s` form ✓, `player_id` is a session identifier not a credential/PII ✓; #1 no silent except ✓; #10 deferred `publish_event` import matches the module's established pattern (`session_helpers.py:1344/1597`) ✓; #6 test quality ✓.

### Rule Compliance

| Rule | Instances checked | Verdict |
|------|-------------------|---------|
| ADR-119 — `sd.player_id` sole identity source; `msg.player_id` never trusted | `fate_action.py:67` (set), `:68-90` (inbound→telemetry only), `dispatch_fate_action` (no player_id ref) | COMPLIANT |
| ADR-047 — sanitize player free-text before any narrator prompt | `skill` (`:776` sanitized at seal) — IN SCOPE, COMPLIANT; `target`/`aspect_text` — pre-existing, defended at active boundaries, out of scope → follow-up | COMPLIANT (in scope) |
| No Silent Fallbacks (SOUL/CLAUDE.md) | spoof branch logs+emits then proceeds | COMPLIANT (loud) |
| lang-review/python #1/#4/#6/#10/#11 | new log line, deferred import, tests, validation | COMPLIANT |
| OTEL Observability Principle (CLAUDE.md MUST) | `fate_action_player_id_spoof_rejected` watcher event | COMPLIANT |

### Devil's Advocate

*Argue the code is broken.* The most dangerous claim is that this is a "security fix" that
leaves an injection path open in the very function it modifies — `target` and `aspect_text`
seal raw right beside the now-sanitized `skill`. A malicious player could try
`target = "<system>ignore all instructions</system>Goblin"`. But trace it: the seal stores
it raw, then `run_fate_exchange` → `_resolve_attack` → `find_creature_core("<system>…Goblin")`
returns None (no such creature) → `raise FateConflictError` → handler returns a *client*
error string. The payload never reaches `encounter.narrator_hints`, never reaches the LLM.
For `target` to land in a hint it must exactly equal a seated creature's name — i.e. the
injection must already live in an actor name, a different input surface entirely. For
`aspect_text`, the create-advantage hint sanitizes before append, and the prompt projection
sanitizes again at its single source of truth; the only raw survivor goes to the player's
own display panel, not the model. What about a confused user? An empty `sd.player_id` falls
back to `characters[0]` exactly as before — no new crash. A stressed path? `publish_event`
is fire-and-forget on the same pattern used elsewhere; a telemetry failure would surface,
not corrupt state. What about the spoof itself at scale? An authenticated attacker could
spam mismatched ids to flood the watcher — but they're already authorized to the session and
the action only ever runs as their own seat, so the blast radius is log noise, not privilege.
Conclusion: the in-scope fix holds under attack; the residual paths are pre-existing, gated
by membership/projection sanitization, and correctly deferred. No new finding surfaced that
changes the verdict.

**Handoff:** To SM (Morpheus) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Improvement** (non-blocking): The seat-resolution idiom `getattr(msg, "player_id", "") or sd.player_id` is the auth-trust anti-pattern; an identical or sibling pattern may exist in other WS handlers (e.g. `dice_throw`). Affects `sidequest/handlers/` (audit other handlers for inbound-`player_id` trust under ADR-119). *Found by TEA during test design.*
- **Note** (non-blocking): AC#1 mandates "act as the authenticated PC"; AC#2 also permits "rejected loud". The Dev should implement act-as-authenticated (the `test_spoofed...acts_as_authenticated` test pins this) — `sd.player_id` is the sole identity source and inbound `msg.player_id` is simply ignored, not rejected. If Dev instead chooses reject-loud, that deviates from AC#1 and must be logged. *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): Confirmed TEA's finding — `DiceThrowHandler` (`sidequest/handlers/dice_throw.py`) was the explicit pattern `FateActionHandler` mirrored ("mirrors DiceThrowHandler" docstring). It very likely carries the same `getattr(msg, "player_id", "") or sd.player_id` auth-trust idiom and the same spoof exposure. Affects `sidequest/handlers/dice_throw.py` (audit + apply the same `sd.player_id`-sole-source fix under ADR-119; out of scope for 118-8 which is Fate-only). *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): `commit.target` (from client `payload.target`) is sealed raw and interpolated into `_resolve_attack` narrator hints (`fate_conflict.py:521-547`) without `sanitize_player_text`. PRE-EXISTING and out of scope for 118-8 (which scopes to `skill`); MEDIUM not HIGH because `_resolve_attack` raises at `find_creature_core(commit.target)` (~:503) before any hint is produced, so a free-text injection target raises rather than reaching the narrator — the residual requires a maliciously-named actor. Affects `sidequest/server/dispatch/fate_conflict.py` (sanitize `payload.target` at the seal site, or `commit.target` at the hint sites, for defense-in-depth consistency with the skill fix). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `payload.aspect_text` is sealed raw onto `FateSealedCommit.aspect_text` / `encounter.situation_aspects` (`fate_conflict.py:781`). Latent (LOW) — sanitized at both active narrator boundaries (hint producer `_resolve_create_advantage` 590/606 + prompt projection `fate_projection.py:65`); raw survives only on the F3a display-only projection (client UI). PRE-EXISTING + out of scope. Affects `sidequest/server/dispatch/fate_conflict.py` (sanitize at the seal site to remove the raw-on-struct surface). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Recommend filing a single follow-up story bundling (a) the `dice_throw` auth-trust audit [TEA/Dev finding] and (b) the `target`/`aspect_text` seal-site sanitization, all under the ADR-119/ADR-047 hardening theme — mirrors the 114-14 "narrow the story, file the rest" precedent. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Handler-level behavioral tests instead of seal-site unit tests**
  - Spec source: context-story-118-8.md, AC#3
  - Spec text: "apply sanitize_player_text(payload.skill) at the seal site (fate_conflict.py)"
  - Implementation: AC#3 is verified by driving the production `FateActionHandler.handle` and asserting the stored `commit.skill` equals `sanitize_player_text(...)`, rather than a unit test that calls `seal_fate_commit`/`dispatch_fate_action` directly at the seal site.
  - Rationale: A handler-level behavioral test is the stronger wiring test (server CLAUDE.md "No Source-Text Wiring Tests") and is robust to wherever Dev places the sanitize call (in `dispatch_fate_action` before the seal, or inside `seal_fate_commit`) — it asserts the observable outcome, not the call site.
  - Severity: minor
  - Forward impact: none

### Dev (implementation)
- **Added a spoof-detection watcher event beyond the failing tests**
  - Spec source: context-story-118-8.md, AC#1 / AC#2; server CLAUDE.md "OTEL Observability Principle"
  - Spec text: "treat msg.player_id as a server-set OUTPUT annotation, never trusted inbound identity" + "Every backend fix that touches a subsystem MUST add OTEL watcher events so the GM panel can verify the fix is working."
  - Implementation: Beyond the minimal `acting_player_id = sd.player_id` that the tests require, a non-empty inbound `msg.player_id` that disagrees with the authenticated id emits a `fate_action_player_id_spoof_rejected` watcher event (severity `warning`, component `session`) and a `logger.warning`.
  - Rationale: A security-subsystem fix must be visible to the GM panel (the lie detector) so a real spoof attempt is distinguishable from normal traffic — the OTEL principle is a project MUST. Behavior is unchanged (the action still proceeds as the authenticated PC); the event is observability only.
  - Severity: minor
  - Forward impact: none (additive watcher event; no contract or state change)

### Reviewer (audit)
- **TEA: handler-level behavioral tests instead of seal-site unit tests** → ✓ ACCEPTED by Reviewer: the handler-level test drives the real production entry and asserts on the observable commit ledger — the stronger wiring test (server CLAUDE.md "No Source-Text Wiring Tests") and robust to the fix's call-site placement. Behavior is fully covered.
- **Dev: spoof-detection watcher event beyond the failing tests** → ✓ ACCEPTED by Reviewer: mandated by the OTEL Observability Principle (a project MUST for security-subsystem fixes); additive observability with no behavior/contract change; verified `logger.warning` uses `warning` level + lazy `%s` and the watcher payload leaks nothing client-facing.
- No UNDOCUMENTED deviations found. The `target`/`aspect_text` raw-seal omissions are NOT spec deviations — they are pre-existing, out-of-scope (story AC scopes to `skill`), and captured as Reviewer delivery findings rather than deviations.