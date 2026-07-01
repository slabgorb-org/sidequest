---
story_id: "160-4"
jira_key: ""
epic: "160"
workflow: "tdd"
---
# Story 160-4: Animal companion cannot join a SOLO session — SoloSlotConflict rejects the companion_of/pet connect; resolve doc-vs-engine design fork + make the understudy run loop fail loud on a rejected connect (unblocks 160-3 dogfood)

## Story Details
- **ID:** 160-4
- **Jira Key:** (not in use for this story)
- **Epic:** 160 (Companion playtest follow-up: animal companions)
- **Workflow:** tdd
- **Type:** bug
- **Points:** 3
- **Priority:** p2
- **Stack Parent:** none

## Technical Approach

### Design Fork Resolution: Path (b) — ENGINE

Keith has chosen **path (b): ENGINE**. A bonded animal companion is NOT a competing solo player and must be exempted from the SOLO-slot guard.

**Primary change (sidequest-server):** `sidequest/server/session_room.py` `SessionRoom.connect()` (~lines 500-505).

**Current behavior:** When `self.mode == GameMode.SOLO`, ANY other connected `player_id` raises `SoloSlotConflict("solo game … already occupied by …")`.

**Updated behavior:** Exempt connects that carry a `companion_of` bond from the guard, so the connect proceeds to `bind_companion_bond` / the chargen gate instead of being rejected. The existing guard's purpose (prevent two parallel solo games on one slug — playtest 2026-04-26) must be PRESERVED for genuine second-human connects; only bonded pets are exempted.

**OTEL instrumentation:** Per the OTEL Observability Principle (CLAUDE.md), this touches the connect/seating subsystem. The fix MUST emit an OTEL watcher event on the companion-exemption decision (e.g. `companion.solo_exempt` or similar) so the GM panel can verify a bonded pet was seated rather than rejected.

### Independent Hardening: Loud Failure on Rejected Connect (sidequest-understudy)

The understudy run loop only handles `SESSION_EVENT-ended` / `CHARACTER_CREATION` / `prompt` / `TURN_STATUS`. On an unhandled `type=ERROR` connect rejection it silently loops back to `recv()` and HANGS FOREVER. This is a **No Silent Fallbacks defect**.

**Fix:** The run loop MUST surface a rejected connect loudly — log the ERROR payload and exit non-zero instead of hanging at `recv()`.

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-07-01T12:16:46Z
**Round-Trip Count:** 2

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-01T09:22:17Z | 2026-07-01T09:25:05Z | 2m 48s |
| red | 2026-07-01T09:25:05Z | 2026-07-01T09:42:05Z | 17m |
| green | 2026-07-01T09:42:05Z | 2026-07-01T11:22:06Z | 1h 40m |
| review | 2026-07-01T11:22:06Z | 2026-07-01T11:36:30Z | 14m 24s |
| green | 2026-07-01T11:36:30Z | 2026-07-01T11:52:02Z | 15m 32s |
| review | 2026-07-01T11:52:02Z | 2026-07-01T12:03:38Z | 11m 36s |
| green | 2026-07-01T12:03:38Z | 2026-07-01T12:11:08Z | 7m 30s |
| review | 2026-07-01T12:11:08Z | 2026-07-01T12:16:46Z | 5m 38s |
| finish | 2026-07-01T12:16:46Z | - | - |

## Sm Assessment

**Repos:** sidequest-server, sidequest-understudy
**Branches:** `feat/160-4-companion-solo-seat` (both repos, off `develop` — gitflow)
**Next phase:** RED (TEA / Igor)

### Routing rationale
3-point bug, `tdd` workflow. The design fork that gated implementation is **resolved** — Keith chose **path (b) ENGINE** (exempt bonded companions from the SOLO-slot guard). No open decisions remain; the RED phase can proceed straight to failing tests.

### What TEA must cover (acceptance criteria → tests)
1. **Companion admitted to SOLO** — a connect carrying `companion_of` joins a SOLO session without `SoloSlotConflict`; it reaches `bind_companion_bond` / the chargen gate rather than getting an ERROR frame.
2. **Guard preserved for humans** — a genuine second-human connect (no `companion_of`) to a SOLO session STILL raises `SoloSlotConflict`. This is the regression guard; the 2026-04-26 "two parallel solo games on one slug" bug must stay fixed.
3. **OTEL emit** — the companion-exemption decision emits a watcher event (e.g. `companion.solo_exempt`) so the GM panel can verify a pet was seated, not rejected. OTEL Observability Principle is mandatory here — the connect/seating subsystem is touched.
4. **Understudy fails loud** — on a `type=ERROR` connect rejection the understudy run loop logs the ERROR payload and exits non-zero instead of looping back to `recv()` and hanging forever (No Silent Fallbacks). This half stands independent of the fork.

### Scope notes for the pipeline
- Two repos, two concerns: `sidequest-server` owns AC1–3 (guard exemption + OTEL); `sidequest-understudy` owns AC4 (loud-fail hardening). They can be tested/implemented in parallel but land as one story.
- Success unblocks **160-3** (the solo companion dogfood path).
- Both repos are gitflow — target `develop`, not `main`, for branches/PRs (confirm against repos.yaml at PR time).

## TEA Assessment

**Tests Required:** Yes
**Status:** RED (verified by direct run — see evidence below)
**Tests Written:** 8 (7 RED + 1 green preservation guard) across 4 ACs, two repos

**Test Files:**
- `sidequest-server/tests/server/test_companion_solo_seat.py` — AC1/AC2/AC3 unit tests on `SessionRoom.connect` (DB-free, fast).
- `sidequest-server/tests/server/test_companion_solo_seat_wiring.py` — AC1 **end-to-end handler wiring** test (DB-gated; the fixture-driven-behavior-through-the-real-handler pattern CLAUDE.md sanctions). Reproduces the exact production ERROR frame.
- `sidequest-understudy/tests/companion/test_solo_connect_rejection.py` — AC4 loud-fail tests on `run_companion`.

**AC → test map:**
- **AC1 (companion admitted to SOLO):** `test_solo_room_admits_bonded_companion` (unit) + `test_bonded_companion_admitted_to_solo_room_through_handler` (wiring).
- **AC2 (second human still blocked):** `test_solo_room_still_rejects_second_human` (green guard) + `test_solo_room_rejects_connect_with_blank_companion_of[""/"   "]` (paranoid — blank `companion_of` ≠ companion).
- **AC3 (OTEL emit):** `test_companion_solo_exemption_emits_otel_span` — asserts a `companion.solo_exempt` watcher span discloses pet player_id + owner.
- **AC4 (understudy loud-fail):** `test_error_connect_rejection_raises_loud` + `test_error_rejection_does_not_loop_back_to_recv_and_hang`.

**Implementation contract for Dev (Ponder):**
1. `SessionRoom.connect(player_id, *, socket_id, companion_of: str | None = None)` — add the kwarg. In the SOLO branch, when another player is present AND `companion_of` is non-blank (`.strip()`), **exempt** (do not raise) and emit a `companion.solo_exempt` watcher span (component `companion`; payload includes `player_id` + the owner identity). A blank/whitespace `companion_of` is an ordinary player → still raise `SoloSlotConflict`.
2. `handlers/connect.py` (~line 514) must pass `companion_of=payload.companion_of` into `room.connect(...)` — the wiring test fails until this second site is edited.
3. `run_companion` must fail loud on a `type=="ERROR"` frame: raise a RuntimeError-family exception (module precedent: `ChargenStepUnsupported(RuntimeError)`) carrying the server message AND log it (warning/error), instead of looping back to `recv()`. The CLI (`cli.py`) leaves it uncaught → non-zero exit (only `ManifestError` is caught) — do not add a broad `except` that swallows it.

### Rule Coverage

| Rule (python lang-review / CLAUDE.md) | Test(s) | Status |
|------|---------|--------|
| #1 Silent exception swallowing (No Silent Fallbacks) | `test_error_connect_rejection_raises_loud`, `test_error_rejection_does_not_loop_back_to_recv_and_hang` | RED |
| #4 Logging coverage (rejection must be logged) | `test_error_connect_rejection_raises_loud` (caplog assertion) | RED |
| OTEL Observability Principle (span on subsystem decision) | `test_companion_solo_exemption_emits_otel_span` | RED |
| Wiring test (component reachable from production path) | `test_bonded_companion_admitted_to_solo_room_through_handler` | RED |
| #6 Test quality (self-check) | own tests — meaningful assertions; parametrize cases hit distinct branches (`""` falsy vs `"   "` truthy-but-strips-empty) | pass |

**Rules checked:** 3 applicable lang-review rules + OTEL + wiring mandate covered.
**Self-check:** 0 vacuous tests.

**Verified RED evidence (direct run):**
- Server (`-n0`, `SIDEQUEST_TEST_DATABASE_URL` set): `5 failed, 1 passed`. The 1 pass is the AC2 human-rejection preservation guard. The wiring test failed with the real bug: `ErrorMessage(... "solo game …-solo-wiring already occupied by curly-pid")`.
- Understudy: `2 failed` — the anti-hang test's failure output shows the loop calling `recv()` a **second time** (the production hang), tripping the sentinel.
- Both new files: `ruff check` clean.

**Handoff:** To Dev (Ponder Stibbons) for GREEN.

## Delivery Findings

No upstream findings at setup.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Improvement** (non-blocking): The understudy CLI's "exit non-zero" on a rejected connect relies on the loud raise from `run_companion` propagating uncaught through `cli.py:play_cmd` (only `ManifestError` is caught today). Affects `sidequest-understudy/src/companion/cli.py` (Dev must not wrap `run_companion`/`asyncio.run(play(...))` in a broad `except` that would swallow the new loud failure). *Found by TEA during test design.*
- **Question** (non-blocking): The four-signal end-to-end companion seating (`chargen.complete` + `companion.bond_resolved` + `routed_as_pet` + distinct per-species voice) named in the story's last AC is the **160-3 dogfood validation**, not asserted here — 160-4's deliverable is unblocking the connect. Affects the 160-3 story (should confirm the four signals fire against a SOLO room once this lands). *Found by TEA during test design.*

### GM (content architecture — during option-C full-suite-green scoping)
- **Improvement** (non-blocking): The two remaining beneath_sunden content failures are NOT a content gap — they expose a render-pipeline architecture smell. Creature portraits exist for only 2 of 22 WN worlds because `scripts/generate_creature_images.py::collect_creatures` hard-rglobs `creatures.yaml` and never reads `bestiary.yaml`, yet the bestiary already carries the render fields (name/description/level→threat); `creatures.yaml`'s only load-bearing add is a non-proper-noun CLIP name for "nothing is named" worlds. Hand-authoring ~900 plates across 22 worlds does not scale. **Keith decided (2026-07-01): derive from bestiary; demote `creatures.yaml` to an optional naming-override.** Filed as **story 158-52** (epic 158, 5pts, ADR + render-pipeline + test-invariant retune). Affects `scripts/generate_creature_images.py`, `scripts/render_common.py`, `sidequest-server/tests/genre/test_beneath_sunden_creature_images_107_2.py`. *Found by GM while scoping the 160-4 full-suite-green push.*
- **Gap** (non-blocking): `test_beneath_sunden_room_binding_107_2.py::test_distinct_rooms_bind_distinct_creatures` is also red — only `entrance.yaml` declares `encounter_creatures`; needs ≥2 distinct per-room bindings + the server resolver/OTEL (`tests/server/dispatch/test_room_creature_binding_107_2.py`). Independent story-107-2 content+wiring debt, noted under 158-52 to scope alongside or split. Affects `sidequest-content/genre_packs/caverns_and_claudes/worlds/beneath_sunden/rooms/*.yaml`. *Found by GM during the same scoping.*
- **Note** (non-blocking): Both beneath_sunden failures are pre-existing story-107-2 debt, unrelated to 160-4. Per Keith, **160-4 lands without the beneath_sunden content half** — the earlier option-C content authoring is retired in favor of 158-52. The engine-bug half of option C (magic cast-spend, awn.mutation) remains a Dev call, not GM content. *Found by GM.*

### Dev (implementation)
- **Improvement** (non-blocking): WWN magic cast does not decrement remaining charges (cinder_lance before=2 after=2). Filed as **158-53**. Affects `sidequest-server` magic-cast path (decrement + OTEL spend span). *Found by Dev while scoping the full suite for 160-4.*
- **Improvement** (non-blocking): `awn.mutation.used` OTEL span never fires for mutant_wasteland mutations. Filed as **158-54**. Affects `sidequest-server` AWN mutation-use path (emit span; confirm effect applies). *Found by Dev.*
- **Improvement** (non-blocking): Full-suite non-determinism from a shared DB-pool leak (rotating PoolClosed) + a flickering_reach test-fixture pack with no tier-1 WWN encounter (~7 chargen-commit tests). Filed as **158-55** (with R2/dogfight triage noted). Affects `sidequest-server` test infra + the stripped test-fixture content pack. *Found by Dev.*
- **Note** (non-blocking): All 8 of 160-4's own tests are GREEN and the branch is landed tightly scoped; the above are pre-existing debt filed, not fixed, per Keith's "file it all; land 160-4 now" decision. *Found by Dev.*

### Reviewer (code review)
- **Gap** (blocking): The understudy loud-fail was implemented as a blanket `if kind == "ERROR": raise` — it aborts on EVERY ERROR frame, but the server emits `code="session_unbound"` (resend-connect recovery), empty-action bounces, and dice retries mid-session. Affects `sidequest-understudy/src/companion/run.py:78` (classify ERROR frames per the `sidequest-ui/src/App.tsx` `FATAL_ERROR_CODES` + `reconnect_required` precedent — fatal-abort only for the connect rejection, recover/continue otherwise). *Found by Reviewer during code review.*
- **Gap** (blocking): The SOLO-slot exemption trusts an unauthenticated, client-asserted `companion_of` string — any Cf-Access identity holding a victim's SOLO slug can seat a second player. Affects `sidequest-server/sidequest/server/session_room.py:513` (cross-check `companion_of` against the seated occupant's server-resolved ADR-119 identity, as `pets_of()` at :775-786 already does, before granting the exemption). *Found by Reviewer during code review.*
- **Improvement** (blocking): `companion.solo_exempt` publishes the raw `companion_of` Cf-Access email into the retained + OTLP-exportable + `#/dashboard`-visible watcher stream, contradicting the no-PII-in-telemetry convention documented in the sibling `bind_companion_bond` (connect.py:303-307) + lang-review #4. Affects `sidequest-server/sidequest/server/session_room.py:533` (drop `companion_of`; the server-minted `occupied_by` already in the payload correlates the exemption without PII). *Found by Reviewer during code review.*
- **Question** (non-blocking): The legacy SOLO-resume branch comment (connect.py:745) asserts "SoloSlotConflict already guarded the second connect" — an invariant this diff removes for companion-exempted connects; a companion connect on a pre-`player_seats` save or a chargen race can reach `has_character=True` with no seat binding. Affects `sidequest-server/sidequest/handlers/connect.py:745` (confirm unreachable given live save population, or backfill `player_seats` like the MP legacy branch). *Found by Reviewer during code review.*

### Reviewer (code review) — Re-review of Rework 1
- **Gap** (blocking): In-session ERROR handling silently hangs on `code="session_unbound"` — the companion never resends `SESSION_EVENT{connect}` (`connect_frame` is sent once) and there is no wall-clock guard, so a mid-session unbind (realistic on `uvicorn --reload`) blocks `recv()` forever — the story's own silent-hang anti-pattern, relocated. Affects `sidequest-understudy/src/companion/run.py:94` (branch on `payload["code"]`: session_unbound → resend `connect_frame` or fail loud; genuinely-transient → continue; correct the overclaiming comment; add a session_unbound test). *Found by Reviewer during re-review.*
- **Improvement** (non-blocking): The SOLO exemption matches `companion_of` against an occupant's resolved identity but does not bind it to the connecting socket's own auth — someone knowing a target's Cf-Access email + SOLO slug could self-declare as a companion. Accepted companion-process design and a strict improvement over the prior "any string" bypass; harden with a server-minted invite token if PvP/multi-tenant ever matters. Affects `sidequest-server/sidequest/server/session_room.py:519`. *Found by Reviewer during re-review.*
- **Note** (non-blocking): Round-1 findings — auth-bypass (High), PII-in-telemetry (Medium), legacy-resume routing — all independently re-verified RESOLVED at root cause (security subagent + new tests); no assertions gutted, no fail-loud guard weakened. *Found by Reviewer during re-review.*

### Reviewer (code review) — Re-review 2 (APPROVED)
- **Note** (non-blocking): Round-2 finding (session_unbound silent hang) RESOLVED — the in-session ERROR classification now resends connect on session_unbound/reconnect_required, raises FatalServerError on fatal codes, log+continues transient (silent-failure hunter, high confidence; test-covered). All three review rounds' findings resolved. *Found by Reviewer during re-review 2.*
- **Improvement** (non-blocking): The session_unbound resend has no retry cap and `connected` is not rolled back on a rejected re-connect — a misbehaving server could drive an unbounded (but logged, not silent, network-bounded) resend loop, matching the shipped UI's own non-rollback behavior. Covered by the deferred wall-clock guard (Design Deviations, Rework 2). Affects `sidequest-understudy/src/companion/run.py:111` (add a retry cap / wall-clock deadline if the harness ever faces an untrusted or flapping server). *Found by Reviewer during re-review 2.*

## Design Deviations

No deviations at setup.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **AC4 tested at `run_companion` (the raise), not via a subprocess exit-code check**
  - Spec source: context-story-160-4.md, AC "The understudy run loop fails loud … exits non-zero"
  - Spec text: "logs the server message and exits non-zero instead of hanging at recv()"
  - Implementation: tests assert `run_companion` raises a RuntimeError-family exception (+ logs the message) at the defect locus; the CLI's non-zero exit follows from the uncaught raise (documented as a Delivery Finding, not separately asserted).
  - Rationale: the defect is in the run loop; testing there is precise and fast, and a subprocess exit-code test would couple to `websockets.connect` mocking without adding signal.
  - Severity: minor
  - Forward impact: none
- **Wiring test uses `space_opera/coyote_star`, not the story's `caverns_and_claudes/beneath_sunden`**
  - Spec source: context-story-160-4.md, Problem (repro world `beneath_sunden`)
  - Spec text: "against a SOLO beneath_sunden session"
  - Implementation: the DB-backed handler wiring test seeds a SOLO `space_opera/coyote_star` room (the proven-loadable pack used by the sibling connect-handler harness).
  - Rationale: the `SoloSlotConflict` guard is genre/world-agnostic; reusing the known-good pack minimizes flake risk unrelated to the fix. The repro fidelity lives in the unit tests' slug naming, not the pack.
  - Severity: minor
  - Forward impact: none
- **Full four-signal 160-3 seating not asserted (scope boundary)**
  - Spec source: context-story-160-4.md, AC "A companion seats end-to-end … the four 160-3 dogfood signals … with an OTEL/wiring assertion"
  - Spec text: "chargen.complete + companion.bond_resolved + routed_as_pet + a distinct per-species voice all fire"
  - Implementation: 160-4 tests cover connect-admission + the `companion.solo_exempt` span; the four downstream seating signals are left to 160-3 (the dogfood story that surfaced this blocker).
  - Rationale: those signals require a full seating/chargen run and are 160-3's validation surface; 160-4's charter is to unblock the connect. Logged as a Delivery Finding for 160-3.
  - Severity: minor
  - Forward impact: 160-3 must confirm the four signals fire against a SOLO room once 160-4 lands.

### Dev (implementation)
- **Added `effective_bestiary` mock to the shared `session_fixture` (tests/server/conftest.py) — beyond the story's three-file contract**
  - Spec source: TEA Implementation contract (this session file) — names `session_room.py`, `handlers/connect.py`, `run.py`
  - Spec text: contract lists exactly those three edit sites for GREEN
  - Implementation: also pinned `genre_pack=MagicMock(..., effective_bestiary=MagicMock(return_value=(None, "")))` on `session_fixture`. Story 158-33's cross-world bestiary purge (`monster_manual_inject.py`) unpacks a 2-tuple from `pack.effective_bestiary(world)`; the bare MagicMock returned an auto-mock that unpacks to `ValueError`, failing 45 tests including 160-4's own DB-backed wiring test (which uses `session_fixture`).
  - Rationale: the 160-4 wiring test could not go green until the shared fixture matched the current `effective_bestiary` 2-tuple contract; `(None, "")` is the realistic "pack has no world-scoped bestiary" value and makes `purge_foreign_bestiary_encounters` a clean no-op. Intentional in-scope shared-test-infra fix, not scope creep — a precondition for verifying this story.
  - Severity: minor
  - Forward impact: none — brings the shared fixture up to the 158-33 contract; benefits all suites using it.
- **Added `husk_reaped_this_turn` to `_EXCLUDED_FROM_DUMP` (sidequest/server/session_helpers.py) — beyond the three-file contract**
  - Spec source: TEA Implementation contract (this session file)
  - Spec text: contract lists three edit sites
  - Implementation: added the transient per-turn `husk_reaped_this_turn` field (already `exclude=True`) to the snapshot-governance `_EXCLUDED_FROM_DUMP` allowlist, clearing 1 pre-existing snapshot-governance failure.
  - Rationale: same transient-exclude shape as the sibling `pending_magic_*` entries already in the list; the field re-derives from encounter state next turn and is never persisted. In-scope hygiene fix surfaced while getting the suite verifiable.
  - Severity: minor
  - Forward impact: none.
- **(Rework 1) Companion SOLO exemption fails CLOSED when the occupant's identity is unresolved**
  - Spec source: context-story-160-4.md, AC1 ("a companion connect joins a SOLO session") + Reviewer finding 2 (auth-bypass)
  - Spec text: AC1 "a connect carrying `companion_of` joins a SOLO session without SoloSlotConflict"
  - Implementation: the exemption now requires `companion_of` to equal the SERVER-RESOLVED identity (`_player_identities`) of a connected occupant; if no occupant has a resolved identity, or none matches, the connect fails closed to `SoloSlotConflict`.
  - Rationale: closes the Reviewer's HIGH auth-bypass (a bare client string could seat a stranger). In real play the owner's identity is always resolved (Cf-Access email / dev Host, ADR-119; the understudy sets a per-seat Host identity), so the happy path is unaffected; an unresolved-identity room is a misconfiguration and fails loud (No Silent Fallbacks) rather than silently admitting an unverifiable second seat.
  - Severity: minor
  - Forward impact: a deployment that runs with NO identity resolution cannot seat companions — acceptable (identity is the ADR-119 auth boundary and is always present behind Cf-Access/Host).
- **(Rework 2) Wall-clock guard deferred (Reviewer's non-blocking recommendation)**
  - Spec source: Reviewer re-review (Rework 1) — recommendation marked non-blocking
  - Spec text: "wrap run_companion / asyncio.run(play) with a wall-clock guard so an un-recovered stall exits non-zero rather than hanging"
  - Implementation: NOT added this round. The blocking hang (`session_unbound`) is fixed by re-sending connect; `reconnect_required` and fatal codes are now handled explicitly; a truly dead socket already surfaces LOUD via the `websockets` keepalive (`ping_interval`/`ping_timeout` → connection close → exception propagates through `asyncio.run(play)` → non-zero exit).
  - Rationale: a wall-clock guard needs a new `CompanionDef` field + wrapping the run, which changes the deliberately event-driven / not-turn-capped contract (`run.py` module docstring) — a design change beyond the blocking fix and beyond minimalist scope. The residual un-recovered-stall risk is an alive-but-silent server (answers pings, sends no frames), a narrow edge.
  - Severity: minor
  - Forward impact: if an alive-but-silent-server stall is ever observed, add a wall-clock deadline to `CompanionDef` + `play()` — the understudy `orchestrate/` path already has the reusable pattern (`run.py:82` deadline, `seat.py:107` check).

### Reviewer (audit)
- **TEA-1 (AC4 tested at `run_companion` raise, not subprocess exit-code)** → ✓ ACCEPTED: testing at the defect locus is sound. BUT see the UNDOCUMENTED entry below — the deviation covered *where* the raise is tested, not that the raise fires on *every* ERROR kind.
- **TEA-2 (wiring test uses `space_opera/coyote_star`, not `beneath_sunden`)** → ✓ ACCEPTED: the `SoloSlotConflict` guard is world-agnostic; reusing the known-good pack is a reasonable flake-avoidance choice.
- **TEA-3 (four-signal 160-3 seating not asserted)** → ✓ ACCEPTED: a legitimate scope boundary; those signals are 160-3's validation surface.
- **Dev-1 (conftest `effective_bestiary` 2-tuple fix)** → ✓ ACCEPTED: in-scope shared-fixture fix; 160-4's own DB-backed wiring test rides `session_fixture` and could not go green until it matched the 158-33 contract. `(None, "")` is the correct realistic value.
- **Dev-2 (`husk_reaped_this_turn` snapshot-exclude)** → ✓ ACCEPTED: mirrors the sibling `pending_magic_*` transient-exclude shape; correct.
- **UNDOCUMENTED (Reviewer-found), blanket ERROR-abort:** Spec (AC4 / SM: "on a `type=ERROR` **connect rejection**") scoped the loud-fail to the rejected connect; the code (`run.py:78`) fails loud on ANY ERROR frame, over-catching the server's recoverable `session_unbound`/validation/dice-retry frames. Neither TEA nor Dev logged this broadening. Severity: **High** (defeats the 160-3 dogfood — see Delivery Findings). → FLAGGED.
- **UNDOCUMENTED (Reviewer-found), PII in the exemption span:** AC3 required "the owner identity" in the span; the code satisfied it by publishing the raw Cf-Access email (`companion_of`), contradicting the no-PII-in-telemetry convention the sibling `bind_companion_bond` documents (connect.py:303-307). The AC3-vs-convention conflict was not logged as a deviation. Severity: **Medium**. → FLAGGED (reconcile AC3 to the server-minted `occupied_by`).

## Dev Assessment

**Implementation Complete:** Yes
**Design Fork:** Path (b) ENGINE — implemented exactly per the TEA contract (companion-of exemption in the SOLO branch; guard preserved for genuine second humans; `companion.solo_exempt` watcher span).

**Files Changed:**
- `sidequest-server/sidequest/server/session_room.py` — `connect()` gains `companion_of: str | None = None`; SOLO branch exempts a non-blank `companion_of` (blank/whitespace still raises `SoloSlotConflict`), emits `companion.solo_exempt` watcher span (component `companion`; payload has slug + player_id + companion_of + occupied_by).
- `sidequest-server/sidequest/handlers/connect.py` — passes `companion_of=payload.companion_of` into `room.connect(...)` (the wiring site).
- `sidequest-understudy/src/companion/run.py` — adds `ConnectRejected(RuntimeError)` + an ERROR-frame branch that logs the server message and raises (CLI leaves it uncaught → non-zero exit; No Silent Fallbacks).
- `sidequest-server/tests/server/conftest.py` — shared-fixture `effective_bestiary` 2-tuple fix (see Deviations; intentional in-scope).
- `sidequest-server/sidequest/server/session_helpers.py` — `husk_reaped_this_turn` snapshot-exclude (see Deviations; intentional in-scope).

**Tests:** 8/8 passing (GREEN) — server 6 (incl. the DB-backed handler wiring test), understudy 2. Re-verified fresh this session via testing-runner: `6 passed` / `2 passed`, ruff clean on all 5 changed files.
**Branch:** `feat/160-4-companion-solo-seat` (both repos; off `develop`, gitflow) — pushed.

**Scope note (pre-existing full-suite debt, filed not fixed):** Per Keith, 160-4 lands tightly scoped. The remaining ~23 pre-existing failures (unrelated to the companion-solo-seat feature) were filed as their own stories with diagnoses: **158-52** (creature-portrait render architecture — derive from bestiary), **158-53** (WWN magic cast-spend), **158-54** (awn.mutation.used span), **158-55** (test-suite hygiene: DB-pool leak + flickering_reach fixture + R2/dogfight triage). Full trail in Delivery Findings.

**Handoff:** To Reviewer (Granny Weatherwax).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (6 passed / 2 passed, ruff clean, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 2 | confirmed 2, dismissed 0, deferred 0 |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | findings | 3 (+1 clean) | confirmed 3, dismissed 0, deferred 0 |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (3 enabled subagents returned; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 4 confirmed (2 High, 2 Medium), 0 dismissed, 0 deferred. (The silent-failure hunter's 2nd finding — exemption seats an unverified/unbonded second participant — folds into the security auth-bypass finding; same root cause.)

## Reviewer Assessment

**Verdict:** REJECTED

The companion-solo-seat feature works for the happy path (8/8 green), but adversarial review found **two High-severity defects that ship broken behavior**, plus two Medium correctness/privacy defects. Notably, the primary High finding *defeats the story's own purpose*: the understudy loud-fail was over-broadened so the companion now crashes on the recoverable mid-session errors the 160-3 dogfood will routinely hit.

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] | Blanket `if kind == "ERROR": raise` aborts the companion on EVERY ERROR frame; the server sends recoverable `session_unbound`/empty-action/dice-retry ERRORs mid-session, so the bot crashes mid-run and can't dogfood (the exact thing 160-4 unblocks). | `sidequest-understudy/src/companion/run.py:78` | Classify ERROR frames per the `sidequest-ui/src/App.tsx:99-103,1428` precedent (`FATAL_ERROR_CODES` allowlist + `reconnect_required` gate) — fatal-abort the connect rejection, recover/continue the rest. |
| [HIGH] | SOLO-slot exemption is granted on any non-blank client-asserted `companion_of`; no cross-check against the seated occupant's server-resolved identity. Any Cf-Access identity with the slug seats a second (or Nth — no count cap) player in a private SOLO game. | `sidequest-server/sidequest/server/session_room.py:513` | Cross-check `companion_of` against the occupant's resolved ADR-119 identity the way `pets_of()` (:775-786) already does, or gate on an explicit owner-side bond/approval, before exempting. |
| [MEDIUM] | `companion.solo_exempt` publishes the raw `companion_of` Cf-Access email (PII) into a retained + OTLP-exportable + `#/dashboard`-visible watcher stream — contradicts the no-PII-in-telemetry convention documented in the sibling `bind_companion_bond` (connect.py:303-307) and lang-review #4. | `sidequest-server/sidequest/server/session_room.py:533` | Drop `companion_of`; the server-minted `occupied_by` already in the payload correlates the exemption without PII. Reconcile AC3 + its assertion in `test_companion_solo_seat.py`. |
| [MEDIUM] | Legacy SOLO-resume branch's safety comment ("SoloSlotConflict already guarded the second connect") is now false for companion-exempted connects; on a pre-`player_seats` save / chargen race a companion connect reaches `has_character=True` with no seat binding, skipping chargen. | `sidequest-server/sidequest/handlers/connect.py:745` | Confirm unreachable given live save population, or backfill `player_seats` like the MP legacy branch just below it. |

**Data flow traced:** client `SESSION_EVENT{connect}.companion_of` → `handlers/connect.py:520` → `SessionRoom.connect(companion_of=...)` → SOLO branch admits on `bool((companion_of or "").strip())` — a client-asserted string reaches a security-relevant admission decision unvalidated (unsafe; [SEC] finding 2). Second flow: server `ERROR` frame → `run.py:78` unconditional raise (unsafe over-abort; [SILENT] finding 1).

**Dispatch-tag roll-up (3 subagents enabled; 6 disabled → assessed manually):**
- `[SILENT]` — CONFIRMED High: `run.py:78` blanket ERROR-abort (finding 1). Verified against server handlers (`session_unbound` is recoverable across 6+ handlers) and the `App.tsx` classification precedent.
- `[SEC]` — CONFIRMED 2×High/Medium: auth-bypass (`session_room.py:513`) + PII-in-telemetry (`:533`) + legacy-resume invariant (`connect.py:745`).
- `[RULE]` — rule-checker disabled; manual Rule Compliance below: lang-review #4 (PII) and #11 (input validation) + ADR-119 all VIOLATED at the two `session_room.py` sites.
- `[EDGE]` — edge-hunter disabled; manual: blank/whitespace `companion_of` is covered by tests; empty-room-first-connect and same-pet reconnect are benign; the uncovered edge is the recoverable mid-session ERROR (finding 1) and the multi-companion / Nth-seat case (no cap — reinforces finding 2).
- `[TEST]` — test-analyzer disabled; manual: assertions are meaningful (non-vacuous), but the tests *encode the two defects* — `test_error_connect_rejection_raises_loud` asserts the blanket abort, and the AC3 test asserts the raw PII in the payload; the rework must update both.
- `[DOC]` — comment-analyzer disabled; manual: `connect.py:745` comment is now stale (finding 4); other new comments are accurate and unusually thorough.
- `[TYPE]` — type-design disabled; manual: `companion_of: str | None = None`, `occupied_by: str | None`, `ConnectRejected(RuntimeError)` all correctly typed; no type-design issue.
- `[SIMPLE]` — simplifier disabled; manual: no over-engineering; the diff is minimal and idiomatic.

**Handoff:** Back to TEA (Igor) for RED rework — all four findings are testable behavior changes (and two require updating the tests that currently encode the defects).

### Rule Compliance

Enumerated the lang-review Python checklist + SOUL/ADR rules against every changed symbol:

- **#1 Silent exception swallowing** — `connect.py:522` `except SoloSlotConflict → _error_msg` converts to a loud ERROR frame (compliant). `run.py:78` raises loud (compliant on *swallowing*, but over-broad — a separate class, finding 1). PASS (no swallowing).
- **#2 Mutable default args** — `connect(..., companion_of: str | None = None)` — immutable default. PASS.
- **#3 Type annotations at boundaries** — `connect()` params + `ConnectRejected` annotated. PASS.
- **#4 Logging: never log PII** — `session_room.py:533` publishes `companion_of` (Cf-Access email) into a watcher event. **VIOLATION** (finding 3).
- **#6 Test quality** — assertions non-vacuous and branch-distinct (`""` vs `"   "`). PASS on vacuity; but the tests encode two defects (noted under `[TEST]`).
- **#11 Input validation at boundaries** — `companion_of` is shape-validated (`max_length=254`, messages.py:367) but the SOLO-*admission* decision it drives is not authorization-validated. **VIOLATION** (finding 2).
- **ADR-119 (server-resolved identity)** — the admission trusts the client-asserted `companion_of` rather than the room's server-resolved `_player_identities`, which `pets_of()` correctly uses. **VIOLATION** (finding 2).
- **#5 path / #7 resource leaks / #8 deserialization / #9 async / #10 imports / #12 deps** — N/A or clean for this diff.

### Devil's Advocate

Assume this code is broken and hunt for the proof. The strongest case: **160-4 exists to unblock the 160-3 companion dogfood, and as written it makes that dogfood impossible.** A companion bot that survives the connect will still die the first time the server emits a routine recoverable `ERROR` — an empty-action bounce after the LLM over-sanitizes, a `session_unbound` "please resend connect" on a reload race, a "Dice throw failed, resync" — because `run.py:78` treats every ERROR as fatal. The human UI shrugs these off via `FATAL_ERROR_CODES`; the bot crashes the whole `companion play` process and the multi-turn playtest is lost. So the feature ships a regression against its own reason to exist.

The second attack: **SOLO isn't SOLO anymore.** The pre-diff guard was the *only* enforcement of one-occupant SOLO. The new exemption fires on any truthy `companion_of`, with no cap and no identity check — so a confused client with a stray non-empty default, or a second Cf-Access identity who was ever shown the `/play/<slug>` link, can seat themselves (or several "companions") into someone's private game, build characters, act, and read broadcast narration. The owner is never asked and never told. The one saving grace is that the *private* view is still gated by the real-identity `pets_of()` check — which is exactly the check the admission gate should have used and didn't.

The privacy attack: the `companion.solo_exempt` span puts a real email into a replay buffer that any authenticated player can pull up at `#/dashboard` and that exports to OTLP — in a codebase that documents "no PII in telemetry" three times, one of them in the sibling function of the same story. A confused user misreads nothing here; a curious one reads a housemate's email off the dashboard.

Finally, the stressed-state attack: on an old pre-`player_seats` save, a companion connect rides the legacy resume branch to `has_character=True` with no seat of its own, silently skipping chargen — an unaudited state the comment swears can't happen. Four independent ways to be broken; the review holds. REJECT.

## Dev Assessment (Rework 1)

**Implementation Complete:** Yes — all 4 Reviewer findings fixed at root cause (no gutted assertions, no weakened fail-loud guards).

**Fixes:**
- **[HIGH finding 1]** `sidequest-understudy/src/companion/run.py` — replaced the blanket `if kind == "ERROR": raise` with a phase gate: a `connected` flag flips true on the first non-ERROR frame; an ERROR *before* connect is fatal (`ConnectRejected`, exits non-zero — the 160-4 hang fix stands), an ERROR *after* connect is a recoverable in-session hiccup (logged + continue), mirroring the `sidequest-ui` `FATAL_ERROR_CODES` precedent. The companion no longer crashes mid-run on `session_unbound`/empty-action/dice-retry.
- **[HIGH finding 2]** `sidequest-server/sidequest/server/session_room.py:connect` — the SOLO exemption now requires `companion_of` to match the SERVER-RESOLVED identity (`_player_identities`) of a connected occupant, the same authenticated cross-check `pets_of()` uses. A stranger's non-blank string, or an unresolved-identity room, fails closed to `SoloSlotConflict`.
- **[MED finding 3]** `session_room.py` — the `companion.solo_exempt` span drops `companion_of` (PII); it now correlates via the server-minted `occupied_by` player_id (the matched owner). No Cf-Access identity in telemetry.
- **[MED finding 4]** `sidequest-server/sidequest/handlers/connect.py` — the legacy-SOLO resume branch routes a companion connect (`companion_of` set) to chargen (`has_character = bool(characters) and not _is_companion`) so it builds its own seat instead of auto-claiming the human's PC; the stale invariant comment is corrected.

**Tests (all reworked to the corrected behavior — the two that encoded the defects were retargeted, not gutted):**
- `test_companion_solo_seat.py` — admits/OTEL tests now set the occupant's resolved identity; the OTEL test asserts `occupied_by` (server id) AND asserts the owner PII is absent; ADDED `test_solo_room_rejects_companion_with_mismatched_owner` (spoof) + `test_solo_room_rejects_companion_when_owner_identity_unresolved` (fail-closed). 7 unit tests.
- `test_companion_solo_seat_wiring.py` — records the human's resolved identity before the companion connects (models the Host/Cf-Access boundary). 1 wiring test.
- `test_solo_connect_rejection.py` — kept the connect-rejection-raises + anti-hang cases; ADDED `test_recoverable_in_session_error_does_not_crash`. 3 tests.

**Verified (testing-runner, RUN_ID 160-4-dev-green-rework1):** server 8 passed, understudy 3 passed, ruff clean both repos. Broad regression (connect/session_room/companion/multiplayer/player_identity/seat/reconnect): 402 passed; the sole failure — `test_45_2_chargen_to_playing_wire` — is the pre-existing `flickering_reach` `EncounterSeedError` (filed as 158-55), unrelated to this diff (my changes touch nothing in the bestiary/encountergen/pregen path).

**Branch:** `feat/160-4-companion-solo-seat` (both repos) — committing the rework.
**Handoff:** Back to Reviewer (Granny Weatherwax) for re-review.

## Subagent Results

_(Re-review of Rework 1. Same 3 enabled subagents; 6 disabled via settings.)_

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (8 passed / 3 passed, ruff clean, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 1 | confirmed 1 (session_unbound silent hang, High) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | findings | 1 residual (+2 prior RESOLVED) | confirmed 1 (residual LOW, accepted design); 2 prior findings RESOLVED |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (3 enabled returned; 6 disabled)
**Total findings:** 1 confirmed High (new), 1 confirmed residual Low (accepted, non-blocking); round-1 HIGH auth-bypass + MEDIUM PII both independently re-verified RESOLVED (security subagent, test-covered).

## Reviewer Assessment

**Verdict:** REJECTED (Re-review of Rework 1)

Credit where due: the two round-1 High/Medium findings are **genuinely fixed at root cause** — the SOLO exemption now gates on the server-resolved identity (auth-bypass closed, security-confirmed, `test_solo_room_rejects_companion_with_mismatched_owner` + `..._when_owner_identity_unresolved`), and the span carries only server-minted ids (PII gone, `_OWNER not in payload.values()` asserted). No assertions were gutted; no fail-loud guard was weakened. The legacy-SOLO companion→chargen fix and the phase-gate's connect-rejection loud-fail are both correct.

But the rework's in-session ERROR handling introduced a **new silent hang** — the exact anti-pattern this story exists to kill, relocated from connect to mid-session.

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] | `log + continue` treats ALL in-session ERROR frames identically, never inspecting `payload["code"]`. `code="session_unbound"` (emitted by dice_throw/fate_action/fate_throw/orbital_intent/player_action/journal_request) recovers ONLY by the client **resending `SESSION_EVENT{connect}`** (App.tsx:1428-1441); the companion never resends (`connect_frame` is sent once at `run.py:67`), so it re-enters `recv()` and hangs **silently, unbounded** (`cli.py:48` `asyncio.run(play)` has no wall-clock guard; the per-decision timeout doesn't bound `recv()`). Realistic today: `just server` runs `uvicorn --reload`, so a code edit mid-dogfood fires `session_unbound`. The comment even names "session_unbound resend-connect" while the code doesn't resend. | `sidequest-understudy/src/companion/run.py:94` | Branch on `payload.get("code")`: `session_unbound` → resend `connect_frame(defn)` (recover, mirroring the UI it cites) OR fail loud; genuinely-transient (no code — empty-action/dice-retry) → log + continue. Make the comment match the code. Recommended (non-blocking): a wall-clock guard around `run_companion` so any un-recovered stall exits non-zero (No Silent Fallbacks). Add a `session_unbound` test. |
| [LOW] | (Residual, non-blocking, accepted design) The exemption matches `companion_of` against *some* occupant's resolved identity but doesn't bind it to the connecting socket's own auth — anyone knowing a target's Cf-Access email + SOLO slug could self-declare as a companion. A strict improvement over the prior "any string works" hole and the documented companion-process trust shape; a server-minted invite token would harden it if ever desired. | `session_room.py:519` | Future-hardening only; captured as a Delivery Finding. |

**Dispatch-tag roll-up (3 enabled; 6 disabled → assessed manually):**
- `[SILENT]` — CONFIRMED High: `run.py:94` session_unbound silent hang (verified: no resend, no wall-clock guard).
- `[SEC]` — round-1 auth-bypass + PII **RESOLVED** (independently re-verified); 1 residual Low (accepted design).
- `[RULE]` — rule-checker disabled; manual: lang-review #4 (PII) now COMPLIANT (span carries no identity); #11/ADR-119 COMPLIANT (exemption gates on server-resolved identity).
- `[EDGE]` — disabled; manual: the uncovered edge is `session_unbound` mid-session (the High above); mismatched-owner and unresolved-identity now covered by new tests.
- `[TEST]` — disabled; manual: the two defect-encoding tests were correctly retargeted (not gutted); a `session_unbound`-recovery test is the gap the fix must add.
- `[DOC]` — disabled; manual: the `run.py:94` comment overclaims (names "session_unbound resend-connect" / cites App.tsx FATAL_ERROR_CODES but implements neither) — must be corrected with the fix.
- `[TYPE]` — disabled; manual: no type issues.
- `[SIMPLE]` — disabled; manual: no over-engineering.

**Handoff:** Back to Dev (Ponder) for green rework — the fix is a targeted `run.py` change + test; the server side is done and correct.

### Rule Compliance (re-review)

- **#4 PII in logs** — `companion.solo_exempt` now carries slug/player_id/occupied_by (server ids only). COMPLIANT (was the round-1 violation).
- **#11 input validation / ADR-119** — SOLO exemption gates on server-resolved `_player_identities`, not the client string. COMPLIANT (was the round-1 violation).
- **#1 Silent exception swallowing / No Silent Fallbacks** — the connect-rejection path fails loud (compliant), but the in-session `session_unbound` path silently hangs. **VIOLATION** (the High above).
- **#6 test quality** — new tests are meaningful and branch-distinct; retargeted tests are not vacuous. PASS (a session_unbound test is still owed).

### Devil's Advocate (re-review)

Assume the rework is broken and prove it. The server side survives the attack: the auth cross-check is real (gates on a value only the WS-accept boundary can set), the PII is gone from telemetry, and every SOLO-admission edge I can construct — mismatched owner, unresolved identity, connect race — fails *closed* and *loud*. So the server half is genuinely done.

The client half is where it breaks, and it breaks on the story's own terms. The whole reason 160-4 exists is that a companion that can't proceed must **fail loud, not hang**. The rework fixed that for the connect rejection and, correctly, stopped crashing on transient per-message bounces. But it over-generalized "recoverable" into "continue on everything in-session," and `session_unbound` is not continue-recoverable — it is resend-recoverable. A tester runs the 160-3 dogfood against `just server` (uvicorn --reload), edits a file, the seat unbinds, the next action returns `ERROR{code=session_unbound}`, the companion logs one line and blocks on `recv()` with nothing coming back. No crash, no exit code, no further output — indistinguishable from "the brain is thinking." That is a *worse* failure than the loud crash the round-1 code had, because it's invisible on an unattended run, and it's the precise hang-shape the story was written to eliminate. The comment claiming to mirror App.tsx's `FATAL_ERROR_CODES` while inspecting no `code` at all is the tell that the classification was asserted, not implemented. The server is done; the client needs one more pass. REJECT.

### Reviewer (audit) — Re-review of Rework 1

- **Dev Rework-1 deviation (SOLO exemption fails closed when occupant identity unresolved)** → ✓ ACCEPTED by Reviewer: sound and security-driven. Fail-closed is the correct No-Silent-Fallbacks posture; in real play the owner identity is always server-resolved (Cf-Access/Host, ADR-119; the understudy sets a per-seat Host identity), so the happy path is intact, and an unresolved room is a loud misconfiguration, not a silent admit. Security subagent independently confirmed the connect race also fails closed (denial, not bypass).

## Dev Assessment (Rework 2)

**Implementation Complete:** Yes — the single blocking finding fixed; the server side was untouched (already green and re-verified this round).

**Fix (sidequest-understudy/src/companion/run.py only):** the in-session ERROR branch now classifies by `code`, mirroring `sidequest-ui` App.tsx exactly:
- `reconnect_required` OR `code == "session_unbound"` → **re-send `connect_frame(defn)`** and continue (the UI's recovery, App.tsx:1428 / :1490). The server won't re-drive an unbound seat, so this replaces the round-1 bare-`continue`-into-silent-hang. Kills the relocated hang.
- `code in _FATAL_ERROR_CODES` (`{"save_schema_invalid"}`, mirroring App.tsx) → **raise `FatalServerError`** (loud, exits non-zero).
- transient (no fatal code — empty-action bounce / dice-retry) → log + continue (unchanged).
Added `_FATAL_ERROR_CODES` + `FatalServerError`; the comment now matches the code (was overclaiming).

**Tests:** understudy 5 (added `test_session_unbound_resends_connect_and_does_not_hang` — asserts a SECOND connect frame is sent, no hang; `test_fatal_code_in_session_raises_loud` — asserts loud raise + no resend; corrected the transient test's log assertion). Server 8 unchanged.

**Wall-clock guard (Reviewer's non-blocking recommendation): DEFERRED with rationale** — logged as a Design Deviation (Rework 2). The blocking `session_unbound` hang is fixed by the resend; a truly dead socket already surfaces loud via the `websockets` keepalive; a wall-clock guard is a design change (new `CompanionDef` field + changes the event-driven contract) beyond the blocking fix.

**Verified (testing-runner, RUN_ID 160-4-dev-green-rework2):** server 8 passed, understudy 5 passed, ruff clean both repos.

**Branch:** `feat/160-4-companion-solo-seat` (understudy commit; server unchanged) — committing.
**Handoff:** Back to Reviewer (Granny Weatherwax) for re-review.

## Subagent Results

_(Re-review 2 of Rework 2. 3 enabled subagents; 6 disabled via settings.)_

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (8 passed / 5 passed, ruff clean, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | clean | prior finding RESOLVED (high); 2 informational obs | confirmed 0 blocking; prior HIGH RESOLVED |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | clean | none (1 informational, non-blocking) | confirmed 0 blocking |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (3 enabled returned; 6 disabled)
**Total findings:** 0 blocking. The round-2 HIGH (session_unbound silent hang) is RESOLVED (silent-failure hunter, high confidence, test-covered); the round-1 HIGH auth-bypass + MED PII remain RESOLVED (server unchanged); 2 low-confidence informational observations (resend has no retry-cap; `connected` not rolled back on a rejected re-connect) are intentional UI parity, logged-not-silent, and covered by the deferred wall-clock guard — non-blocking.

## Reviewer Assessment

**Verdict:** APPROVED (Re-review 2 of Rework 2)

All findings across three review rounds are resolved at root cause, with no assertions gutted and no fail-loud guard weakened:
- **Round-1 [HIGH] auth-bypass** → the SOLO exemption gates on the server-resolved identity; RESOLVED (security-verified, `test_solo_room_rejects_companion_with_mismatched_owner` + `..._when_owner_identity_unresolved`).
- **Round-1 [MED] PII-in-telemetry** → `companion.solo_exempt` carries only server-minted ids; RESOLVED (`_OWNER not in payload.values()` asserted).
- **Round-1 [MED] legacy-resume** → companion routes to chargen; RESOLVED.
- **Round-2 [HIGH] session_unbound silent hang** → the in-session ERROR branch now classifies by `code` exactly like the human UI (App.tsx): `reconnect_required`/`session_unbound` re-send the connect handshake (recover — no hang), `save_schema_invalid` raises `FatalServerError` (loud), transient errors log+continue. RESOLVED (silent-failure hunter high confidence; `test_session_unbound_resends_connect_and_does_not_hang` + `test_fatal_code_in_session_raises_loud`). The overclaiming comment now matches the code.

**Data flow traced:** server `ERROR{code}` → `run.py` in-session branch → resend `connect_frame` (session_unbound) / raise `FatalServerError` (fatal) / log+continue (transient) — every branch recovers-with-log or fails-loud; none swallows silently. Client-side; `code`/`reconnect_required` are only used in equality/membership checks (no injection surface — security-confirmed).

**Dispatch-tag roll-up (3 enabled; 6 disabled → assessed manually):**
- `[SILENT]` — prior HIGH RESOLVED (high confidence); no new silent path.
- `[SEC]` — CLEAN this round; round-1 auth+PII remain resolved (server unchanged); 1 informational (resend no cap, non-blocking).
- `[RULE]` — manual: lang-review #1 (No Silent Fallbacks) now COMPLIANT on the in-session path (fatal→raise, unbound→resend); #4 PII + #11/ADR-119 remain compliant.
- `[EDGE]` — disabled; manual: session_unbound, fatal-code, transient, and connect-rejection edges all covered by tests; the residual edge (rejected re-connect after a resend) is UI-parity, non-blocking.
- `[TEST]` — disabled; manual: new tests assert real behavior (2nd connect frame on resend; loud raise + no resend on fatal); not vacuous.
- `[DOC]` — disabled; manual: the `run.py` in-session comment now matches the code (the round-2 overclaim is corrected).
- `[TYPE]` — disabled; manual: `FatalServerError(RuntimeError)`, `_FATAL_ERROR_CODES: frozenset` correctly typed.
- `[SIMPLE]` — disabled; manual: the classification is minimal and mirrors an existing precedent; no over-engineering.

**Handoff:** To SM (Captain Carrot) for finish-story.

### Devil's Advocate (Re-review 2)

Assume it's still broken. The strongest remaining attack is the resend loop: session_unbound → resend → what if the resend is itself rejected? For a *legitimate* companion the re-connect re-hits the hardened exemption and is re-admitted (companion_of still matches the seated owner's resolved identity), so it rebinds and plays on — the loop terminates. The only way it doesn't is a server that repeatedly emits session_unbound to a connect frame, which the server doesn't do (session_unbound is for actions on an unbound seat, not for the connect handshake). And even a pathological resend loop is bounded by real network round-trips, logs a WARNING every iteration (visible, not silent), and mirrors the shipped UI exactly — plus the websockets keepalive kills a truly dead socket loudly. The second angle — `connected` not resetting on the resend — means a post-resend rejection is classified as in-session rather than as a fresh connect rejection; but that path either resends (unbound), raises (fatal), or logs+continues (transient), none of which is a *silent* stall, and it matches the UI's own non-rollback state machine. There is no silent hang left and no swallowed error. The story's promise — the companion fails loud or recovers, never hangs silently — holds. APPROVE.

### Reviewer (audit) — Re-review 2 of Rework 2

- **Dev Rework-2 deviation (wall-clock guard deferred)** → ✓ ACCEPTED by Reviewer: sound. It was my own explicitly-non-blocking recommendation; the concrete `session_unbound` hang is fixed by the resend, a dead socket surfaces loud via the `websockets` keepalive, and a run-level deadline is a genuine design change (new `CompanionDef` field + alters the deliberately event-driven contract) rightly deferred with a clear re-entry path (reuse `orchestrate/` `run.py:82`/`seat.py:107`). The residual resend-no-cap / `connected`-no-rollback observations fall under this same deferral and are non-blocking UI parity.
- **Dev Rework-1 deviation (exemption fails closed on unresolved identity)** → ✓ ACCEPTED (re-affirmed from round-1 re-review).