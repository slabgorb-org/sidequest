---
story_id: "117-4"
jira_key: ""
epic: "117"
workflow: "tdd"
---
# Story 117-4: Harden the unminted-objective lie-detector

## Story Details
- **ID:** 117-4
- **Title:** Harden the unminted-objective lie-detector
- **Points:** 5
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** setup
**Phase Started:** 2026-06-15T00:24:14.751389+00:00

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-15T00:24:14.751389+00:00 | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap (blocking — the core of 117-4):** The Intent Router exposes NO signal for a
  *narrator-introduced, un-seeded* objective. The router (`intent_router.py`) classifies
  the **player's `<raw_action>`** into mechanical dispatches and runs **before** the
  narrator — it never sees the narration the narrator is about to write. Its one
  objective-related subsystem, `quest_offer` (117-3, `intent_router.py:269`), fires **only
  when `snapshot.pending_quest_offers` is non-empty** — i.e. only when an authored
  `QuestSeed` (opening `tone.quest_seed` or seed-trope) already exists
  (`intent_router_pass.py:399`). The perseus_cloud / barsoom repro is the **un-seeded**
  case: a noir "discreet job" hook with no `QuestSeed` behind it → `pending_quest_offers`
  empty → router emits no `quest_offer` → the only thing watching is the brittle keyword
  `detect_unminted_objective`. **So the "ride the intent router" framing in the story
  title only covers SEEDED hooks** (where 117-3 already built `_check_quest_offer_engaged`
  as the structurally-sound mismatch witness, `dispatch_engagement_watcher.py:340`). For
  the truly un-seeded improvisation there is currently no router classification to
  consume. **Dev must resolve which of these 117-4 builds:**
  - **(A)** Thread the existing `quest_offer` `DispatchPackage` signal into
    `detect_unminted_objective` (the seam these RED tests pin): detector fires when the
    router classified objective-engagement (a `quest_offer` dispatch present) AND
    quest_log stayed empty AND nothing minted. This hardens the SEEDED path beyond the
    keyword list and is fully testable with synthetic packages. **The RED tests target
    this seam.**
  - **(B)** ALSO add a new router classification for narrator-given/un-seeded objectives
    (a new objective-giving subsystem or a router flag the detector reads), to cover the
    exact perseus_cloud failure where no seed exists. This is the larger build the story
    title gestures at; if in scope, it needs its own router-prompt block + a signal on the
    `DispatchPackage` the detector consumes. **If Dev judges (B) out of 117-4's scope,
    say so loudly** and keep the keyword path as the un-seeded backstop (tests (c) pin that
    it is not regressed).
- **Question (non-blocking):** "Nothing minted it" — the negative gate (b) — is pinned via
  `quest_log` non-empty after the turn (the same gate the current detector uses). A
  `quest_offer` accept (`quest_offer.py`), `record_quest`, and `seed_drive`
  (`quest_seed.py`) ALL land in `quest_log`, so the single empty-`quest_log` check
  already distinguishes minted-vs-not for every mint path. If Dev wants finer attribution
  (which path minted), that is observability, not the firing gate — the gate stays
  `quest_log` emptiness.
- **Improvement (non-blocking):** The `quest_offer` *mismatch* witness (117-3) already
  catches "router dispatched accept but quest_log empty" for SEEDED offers. 117-4's
  `detect_unminted_objective` should NOT double-flag that exact case — consider whether the
  detector stands down when a `quest_offer` mismatch span would already fire (analogous to
  `_package_dispatched_confrontation` standing down the improvised-combat detector). Not
  pinned in RED; flagged for Dev's design.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Option A only (Keith's ruling, 2026-06-14):** Hardened the SEEDED path by riding
  the router's `quest_offer` `DispatchPackage` signal. Did NOT build a new narrator-output
  objective classifier (option B) — that is carved out to follow-up story 117-6. The
  keyword `_UNMINTED_OBJECTIVE_MARKERS` path is RETAINED unchanged as the un-seeded
  backstop and annotated in the detector docstring as provisional pending 117-6.
- **No dedupe stand-down (TEA's non-blocking Improvement note):** The RED headline test
  (`test_fires_on_router_objective_with_zero_keyword_markers`) explicitly pins that
  `detect_unminted_objective` MUST fire on the seeded-but-empty case — the same case 117-3's
  `_check_quest_offer_engaged` also flags via `run_dispatch_engagement_watcher`. The tests
  are the contract, so I did NOT stand the detector down when `quest_offer` is present.
  Double-flagging is avoided *in practice* by signal separation, not suppression: the two
  detectors emit DIFFERENT spans (`dispatch_engagement.quest_offer.mismatch` from 117-3's
  per-quest_id witness vs `narration.unminted_objective.suspected` from this structural
  empty-log detector). They answer different questions — "this named quest_id wasn't minted"
  vs "an objective was classified yet quest_log is wholly empty" — so two beeps on the same
  turn are complementary GM signal, not redundant noise. No over-engineering: behavior
  matches every pinned assertion.
- **Decline false-positive fix (Hermes REJECT, HIGH/blocking — corrected 2026-06-14):** My
  initial `_package_dispatched_quest_offer` matched ANY quest_offer dispatch regardless of
  `decision`, so a DECLINED offer on an empty quest_log (a normal early-game "no thanks",
  where the engine correctly mints nothing + emits `quest.offer_declined`) falsely fired
  `narration.unminted_objective.suspected` — the GM-panel-flood mode the epic forbids, and
  *less* correct than the 117-3 sibling witness `_check_quest_offer_engaged` which excludes
  decline. Fixed: renamed the helper to `_package_accepted_quest_offer`, gated on
  `params["decision"] == "accept"`. `decline` (honest non-mint) and `unknown_decision`
  (already flagged by `quest_offer.py`'s own `quest_offer.mismatch`) are both excluded —
  only an accept-without-mint is an unminted objective, matching the engine's mint contract.
  Added two regression tests (`test_no_fire_on_declined_quest_offer`,
  `test_watcher_silent_on_declined_quest_offer`) closing the decline-coverage gap that
  masked the bug. This also retires my earlier "signal separation" defense for the decline
  case — Hermes was right that it didn't hold there (117-3 is silent on decline, so my span
  would have fired alone and falsely).

### TEA (test design)
- **Detector signature gains `package`:** Story title says "ride the intent router". The
  router signal IS the `DispatchPackage`. The RED tests therefore pin a new
  `package: DispatchPackage | None` parameter on BOTH `detect_unminted_objective` and
  `run_unminted_objective_watcher`, and pin the live handler threading
  `turn_context.dispatch_package` into the watcher call (it already threads the same object
  into `run_dispatch_engagement_watcher` one call above, `websocket_session_handler.py:1142`
  vs `:1167`). Reason: there is no other seam by which the router's classification reaches
  this post-narration detector. Dev is free to default `package=None` so the keyword-only
  callers/backstop keep working.
- **Headline case rides `quest_offer`, not a new subsystem:** The RED headline test
  injects a synthetic `quest_offer` `DispatchPackage` as the router's objective signal
  (option A in Delivery Findings). If Dev builds a NEW objective-giving router signal
  (option B) instead of/in addition to `quest_offer`, the headline test's `_quest_offer_package`
  fixture must be updated to emit that signal — the *behavioral* assertions (fires on
  router-objective + empty log; silent on minted) are signal-agnostic and stay.

## TEA Assessment

**Tests Required:** Yes
**Reason:** n/a

**Test Files:**
- `tests/agents/test_unminted_objective_router_backed.py` — router-backed
  unminted-objective detection: headline open-ended hook (zero keyword markers,
  router-classified) fires; minted-quest negative; keyword backstop preserved; signature +
  AST wiring.

**Tests Written:** 11 tests covering 4 AC clusters (a/b/c/d).
**Status:** RED — 10 failing for feature-absence (the `package` router seam does not exist),
1 passing (premise guard validating the synthetic fixture). Existing
`tests/agents/test_unminted_objective_watcher.py` (keyword path) stays green (9 passed) —
unchanged, so the keyword backstop is provably not yet removed.

**RED proof:** every failure is `detect_unminted_objective()/run_unminted_objective_watcher()
got an unexpected keyword argument 'package'`, or the two signature reflection asserts, or
the AST wiring assert (handler does not pass `package=` yet). No import errors.

**Handoff:** To Dev for implementation.
