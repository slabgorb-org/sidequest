---
story_id: "158-8"
jira_key: null
epic: 158
workflow: tdd
---
# Story 158-8: MP pronoun localization — recipient's own action renders third-person (+ solo reconnect/replay variant)

## Story Details
- **ID:** 158-8
- **Jira Key:** (none — Jira not enabled)
- **Workflow:** tdd
- **Stack Parent:** none
- **Type:** bug
- **Points:** 3
- **Priority:** p2
- **Repos:** server,ui

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-23T11:04:52Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-23T08:40:50.550181+00:00 | - | - |
| red | 2026-06-23T08:40:50.550181+00:00 | 2026-06-23T10:18:24Z | 1h 37m |
| green | 2026-06-23T10:18:24Z | 2026-06-23T10:25:42Z | 7m 18s |
| review | 2026-06-23T10:25:42Z | 2026-06-23T10:38:35Z | 12m 53s |
| red | 2026-06-23T10:38:35Z | 2026-06-23T10:49:04Z | 10m 29s |
| green | 2026-06-23T10:49:04Z | 2026-06-23T10:55:27Z | 6m 23s |
| review | 2026-06-23T10:55:27Z | 2026-06-23T11:04:52Z | 9m 25s |
| finish | 2026-06-23T11:04:52Z | - | - |

## Source Finding (Ping-Pong, 2026-06-22)

Playtest bug from caverns_and_claudes/beneath_sunden sweep. The per-player MP pronoun localizer (layer that swaps PC names ↔ "you" per recipient when broadcasting narration) has TWO distinct defects, both facets of single-anchor localization:

### Facet (1) — Agreement Break (Severe; Also Fires in Solo)

When the localizer swaps a PC's name → "you" (subject token), dependent gendered pronouns referring to the SAME PC in the same passage (he/him/his) are left 3rd-person. Result: grammatically broken person disagreement.

**MP repro (turn 2):** Groucho's screen reads "**You** grab the rope a beat later and follows, the wet hemp cold through **his** gloves, the draught pushing up past **him**..." — subject Groucho→You swapped, but his/him NOT swapped to your/you.

**SOLO repro (session 697cbc14):** No MP localization involved at all — narrator converted a 3rd-person-authored solo action ("Groucho ... lowers himself") to 2nd person within one passage: "...as **you** swing **his** legs over the collar ... breathing up against **him** as **he** takes the rope." So facet (1) is NOT purely an MP-localizer artifact — it also occurs when the narrator itself emits a 2nd-person conversion in solo.

**FIXER note:** Likely a shared root with MP facet (1); confirm.

### Facet (2) — Non-Anchor Recipient Gets No 2nd Person (Unimplemented per Driver)

The localizer anchors a single "you" to the card's PRIMARY actor and only de-localizes the OTHER name(s); it never re-anchors "you" to the recipient's own PC. So a recipient reads about THEMSELVES in 3rd person on their own screen.

**Repro (turn 1):** On Harpo's screen, Groucho is correctly de-localized to "Groucho", but Harpo's own action reads "**Harpo** moves to the winch without a word..." — third person; there is NO "you" anywhere on Harpo's screen. Harpo reads about herself in 3rd person.

**FIXER summary:** The swap needs to (a) carry gendered pronouns with the name swap [facet 1], and (b) re-anchor 2nd person per recipient, not per card [facet 2].

## Prior Work (Research Ground — Do Not Re-Implement)

- **153-14:** Word-boundary/proper-noun guard for PC-name→you POV swap (MP pronoun bug). Confirm this guard is still working (no "you Vah" fragment leaks). Don't regress it.
- **153-29 (commit 8dec6bcd):** Prior "MP pronoun agreement-break fix". The 2026-06-22 SOLO repro still shows the agreement break firing — so either 153-29's fix was MP-localizer-scoped and the solo/narrator path is uncovered, or it's incomplete. Research which path 153-29 touched and where the gap is.
- **Localizer location:** Per-player localizer lives in the perception/broadcast fan-out layer (ADR-104 perception filtering at tool layer, ADR-105 broadcast-layer perception firewall, ADR-108 MP item attribution per-recipient). Search the server for the name↔"you" swap / pronoun localization code (grep for the localizer that does PC-name→"you" per recipient).
- **UI scope:** Repos: server,ui. Confirm whether any client-side reconciliation (ADR-133) touches the rendered narration text per recipient, or whether ui is in scope only for verifying the rendered card. Note this for TEA.

## Draft Acceptance Criteria (for TEA/Dev/Architect Refinement)

- **AC1 (agreement break):** When a PC name is swapped to "you" on a recipient's screen, dependent gendered pronouns (he/him/his) referring to that SAME PC in the same narration are carried to 2nd person (your/you/you). No "You... his... him" disagreement.
- **AC2 (per-recipient re-anchor):** Each recipient's own PC is anchored to "you" on their own screen (re-anchor per recipient, not per card). A non-anchor recipient never reads about their own PC in 3rd person.
- **AC3 (solo variant):** A 3rd-person-authored solo action converted to 2nd person carries gendered pronouns too — no agreement break in solo replay/reconnect. Confirm shared-root with AC1 or document the separate path.
- **AC4 (OTEL observability):** The localization/agreement decision emits OTEL watcher spans so the GM panel can verify the swap fired (which tokens swapped, per recipient). Per CLAUDE.md: the GM panel is the lie-detector. If a subsystem isn't emitting OTEL spans, you can't tell whether it's engaged or whether Claude is just improvising.

## Notes for TEA (Red Phase Owner)

- This is a server-primarily bug with ui as a secondary verify surface. The red phase should pin BOTH facets with failing tests, and include a wiring test (per CLAUDE.md) that the localizer is reached from the real broadcast fan-out, not just unit-tested in isolation.
- The full server suite has a known ~258–269 pre-existing hermeticity-guard baseline (build_async_anthropic LlmClientError + loader baselines) and requires `SIDEQUEST_DATABASE_URL` set — don't panic at the count; gate regressions against the baseline.

## TEA Assessment

**Tests Required:** Yes
**Status:** RED (3 failing facet-2 tests, ready for Dev) + GREEN regression pins for the already-fixed facet 1

### Key measured finding (reshapes the story)
Facet 1 (the agreement break, **including** the title's "+ solo reconnect/replay variant") is **already fixed by 153-29** (commit `8dec6bcd`, in this branch — 0 behind develop). Probed the exact playtest repro strings against the current `swap_to_second_person`:
- "Groucho ... through **his** gloves ... past **him**" → "...through **your** gloves ... past **you**" ✓
- solo "Groucho lowers **himself** ... as **he** takes" → "...lower **yourself** ... as **you** take" ✓

The driver's 2026-06-22 solo repro was a **stale-tree artifact** (they were on `d19afd32`). Per Keith's scope decision (2026-06-23): **Facet 2 only + pin Facet 1.** The deliberate post-`;` clause-local NPC-bleed tradeoff (153-29) is intentionally NOT reopened.

**The genuine gap (Facet 2)** is entirely in the emit layer: `sidequest/server/emitters.py::_apply_pov_swap` (~L258) gates `if recipient_pc_name != anchor_pc: return payload_dict` (~L279), so a non-anchor recipient gets the canonical prose and reads their own PC in 3rd person. The localizer (`swap_to_second_person`) needs **no change** — probed: it already re-anchors any PC (subject or object) with full agreement, and is a no-op when the recipient isn't named (which preserves the anchor-only-card test). Dev: re-anchor the swap target to the recipient's OWN PC at the per-recipient fan-out (call sites ~586-601 peer, ~615-638 merged-MP, ~680-706 solo).

**Test Files:**
- `tests/server/test_narration_pov_emission.py` (Story 158-8 section appended) — per-recipient re-anchor **wiring** tests through the real `emit_event` fan-out:
  - `test_158_8_non_anchor_recipient_own_pc_reanchored_to_you` — RED (Katia reads "Katia steadies" not "you steady")
  - `test_158_8_reanchor_carries_gendered_pronoun_agreement` — RED (herself→yourself / her→you on Katia's frame)
  - `test_158_8_per_recipient_swap_emits_otel_span_for_own_pc` — RED (AC-4: a `narration.second_person_swap` span with `swap_target_name="Katia"`)
  - `test_158_8_anchor_frame_unaffected_other_pc_stays_a_name` — GREEN guard (one PC re-anchors per screen)
  - `test_158_8_recipient_not_named_in_card_is_unchanged` — GREEN guard (no-op when recipient absent → keeps anchor-only test green)
- `tests/agents/test_pov_swap_158_8_finding_pins.py` (new) — 7 GREEN regression pins locking in 153-29 against the exact finding repro strings (MP + solo + female PC + clause-local gate).

**Tests Written:** 12 (5 wiring + 7 unit pins) covering AC1/AC2/AC3 (as regression-pinned green) and AC2/AC4 (as RED).
**RED verification:** testing-runner run `158-8-tea-red` — 3 intended-RED tests fail by **assertion** (not error); all 7 pre-existing emission tests + all 5 `test_pov_swap_otel.py` tests stay green. No production code touched.

### Rule Coverage

| Rule (source) | Test(s) | Status |
|------|---------|--------|
| Test quality — no vacuous assertions (lang-review #6) | self-check: rewrote the clause-gate parametrize so the NPC word matches each pronoun set (was vacuous for she/they) | fixed |
| No source-text wiring tests (server CLAUDE.md) | facet-2 tests drive the real `emit_event` fan-out + assert OTEL spans; zero `read_text()`/source-grep | covered |
| Every suite needs a wiring test (CLAUDE.md) | `test_158_8_*` in `test_narration_pov_emission.py` exercise the production per-recipient emit path | covered |
| OTEL observability — subsystem decision emits a span (CLAUDE.md / AC-4) | `test_158_8_per_recipient_swap_emits_otel_span_for_own_pc` | failing (RED) |

**Rules checked:** lang-review #6 (test quality) is the applicable TEA rule; #1–#5 govern Dev's production code (flagged for Dev). **Self-check:** 1 vacuous assertion found and fixed (clause-gate parametrize).

**Handoff:** To Dev — wire per-recipient re-anchor in `_apply_pov_swap`; emit the per-recipient swap span; keep the localizer untouched.

### Rework (Round-Trip 2 — Reviewer REJECT, 2026-06-23)

**Tests Required:** Yes
**Status:** RED — 17 failing rework tests ready for Dev; the existing 13 (section-7 facet-2 + premise-guard) stay GREEN. No production code touched.

**What the REJECT was:** the Facet-2 re-anchor (section 7) widened a latent crash. `swap_to_second_person` raises `ValueError` for any pronouns outside `{he/him, she/her, they/them}` (`pov_swap.py:878`), validation fires BEFORE name matching, and `_apply_pov_swap` now runs for EVERY `pc_anchored` recipient inside `emit_event`'s `repo.transaction()` (`emitters.py:518`). A single recipient with freeform chargen pronouns (`pronouns_allow_freeform=True`, `builder.py:2194`) raises mid-fan-out → the NARRATION turn ROLLS BACK → the whole table gets no narration.

**Required behavior (pins the Reviewer's fix):** `_apply_pov_swap` must guard `pronouns in _PRONOUN_FORMS`, fail OPEN to canonical 3rd-person prose (same shape as the existing empty-pronoun guard at `emitters.py:289`), and emit an OTEL skip span. No bare try/except.

**Test File (appended section 8):** `tests/server/test_narration_pov_emission.py`
- `test_158_8_freeform_test_pronouns_are_genuinely_noncanonical` — GREEN premise-guard (the 5 freeform strings are genuinely outside `_PRONOUN_FORMS`; protects the section from going vacuous if the canonical set widens).
- `test_158_8_noncanonical_pronoun_recipient_falls_open_to_canonical[×5]` — RED: a freeform-pronoun recipient gets canonical prose, emit does not raise.
- `test_158_8_noncanonical_pronoun_does_not_brick_the_table[×5]` — RED (blast radius): a Carl-only card (never names Katia) still crashed; after the guard, Carl/Donut/Katia all receive frames AND the NARRATION event persists (no transaction rollback).
- `test_158_8_noncanonical_pronoun_emitter_does_not_crash[×2]` — RED: the crash also reaches the EMITTER swap call site (`emitters.py:~689/707`), not just the peer loop.
- `test_158_8_noncanonical_pronoun_emits_skip_span[×5]` — RED (AC-4 / OTEL): a `narration.pov_swap_skipped` span fires for the recipient.

**OTEL contract (TEA-defined; Dev implements to match):** span name `narration.pov_swap_skipped`, attributes `recipient_pc` (which screen), `reason="unsupported_pronouns"` (why), `pronouns` (the offending chargen value). The Reviewer mandated "a skip span"; the exact name/attributes are TEA's contract so the GM panel can attribute the fail-open to a screen — this also satisfies the [SILENT]/`recipient_pc` observability gap the Reviewer + round-1 TEA flagged.

**RED verification:** targeted run of the whole `test_narration_pov_emission.py` file (`-n0`, `SIDEQUEST_TEST_DATABASE_URL` set) — 17 failed by the documented `ValueError: unsupported pronouns: 'she/they'; supported: [...]` at `pov_swap.py:878` (confirmed the crash propagates out of `_emit_event`), 13 passed (section-7 facet-2 tests + premise-guard unaffected). Used a scoped direct run rather than the testing-runner subagent because the suite SKIPS without `SIDEQUEST_TEST_DATABASE_URL` (which the runner does not export) and the blast radius is one file.

### Rework Rule Coverage

| Rule (source) | Test(s) | Status |
|------|---------|--------|
| No-Silent-Fallbacks + OTEL Observability (CLAUDE.md / Reviewer [RULE]) — the fail-open skip path must emit a span | `test_158_8_noncanonical_pronoun_emits_skip_span` | failing (RED) |
| Fail-loud regression must not crash the table (Reviewer [SEC] blocking) | `test_158_8_noncanonical_pronoun_does_not_brick_the_table` (EventLog-persisted assertion) | failing (RED) |
| Test quality — no vacuous assertions (lang-review #6) | `test_158_8_freeform_test_pronouns_are_genuinely_noncanonical` guards the premise; every assertion checks a value, not just truthiness | covered (GREEN guard) |
| Both call sites wired (CLAUDE.md "every suite needs a wiring test") | peer path (`falls_open`, `does_not_brick`) + emitter path (`emitter_does_not_crash`) both driven through the real `emit_event` fan-out | failing (RED) |

**Self-check:** no vacuous assertions in the new tests — each asserts an exact text value, queue size, persisted-row predicate, or specific span attribute. Added a dedicated premise-guard test so a future `_PRONOUN_FORMS` widening can't silently void the section.

**Handoff:** To Dev (Inigo) — add the `pronouns in _PRONOUN_FORMS` guard to `_apply_pov_swap`, fail open to canonical prose, and emit the `narration.pov_swap_skipped` span (`recipient_pc`/`reason`/`pronouns`). Keep the localizer untouched. Fold the stale call-site comment at `emitters.py:598-601` (Reviewer [DOC]) into the change.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest/server/emitters.py` — `_apply_pov_swap`: swap the RECIPIENT's own PC (`recipient_pc_name`) instead of the card's single `anchor_pc`; drop the `recipient_pc_name != anchor_pc` guard (kept the `is None` guard and the `pc_anchored`/atmospheric gate). One-helper change; the localizer (`swap_to_second_person`) is untouched, exactly as TEA scoped. The `narration.second_person_swap` OTEL span now fires per recipient with their own PC as `swap_target_name` (AC-4) because the swap runs with that target — no new span code needed.

**How each AC is met:**
- AC2 (per-recipient re-anchor): on a non-anchor recipient's frame their own PC → "you"; other PCs stay names. (`test_158_8_non_anchor_recipient_own_pc_reanchored_to_you`)
- AC1/AC3 (agreement, incl. solo): the recipient swap reuses the 153-29 machinery, so gendered pronouns carry (`test_158_8_reanchor_carries_gendered_pronoun_agreement` + the green facet-1 pins).
- AC4 (OTEL): per-recipient swap span fires for the recipient's own PC (`test_158_8_per_recipient_swap_emits_otel_span_for_own_pc`).

**Tests:** 114/114 passing (GREEN) across the full POV/narration-emission surface — `test_narration_pov_emission.py` (12), `test_pov_swap_158_8_finding_pins.py` (7), `test_pov_swap_otel.py` (5), `test_pov_swap.py` (78), `test_narration_pov_regression.py` (3), `test_opening_pov_swap_71_5.py` (3). All three previously-RED tests now pass; zero regressions. (testing-runner run `158-8-dev-green`.)
**Lint/format:** `ruff check` clean; `ruff format` applied to the two test files (TEA's red commit predates a format pass).
**Branch:** `feat/158-8-mp-pronoun-localization` (server) — pushed. UI: no change (see Delivery Findings).

**Handoff:** To Reviewer for code review.

### Rework (Round-Trip 2 — Reviewer REJECT fix, 2026-06-23)

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest/server/emitters.py` — `_apply_pov_swap`: added a `pronouns not in _PRONOUN_FORMS` guard immediately after the existing empty-pronoun guard. When the recipient's chargen pronouns are non-canonical/freeform, the helper now (a) returns `payload_dict` unchanged — fail-open to canonical 3rd-person prose, the same shape as the empty-pronoun branch — instead of handing them to `swap_to_second_person` (which raises `ValueError` inside `emit_event`'s `repo.transaction()` and rolls back the whole table's turn), and (b) emits a `narration.pov_swap_skipped` OTEL span (`recipient_pc`, `reason="unsupported_pronouns"`, `pronouns`) so the GM panel sees the fail-open. Added module-level `_tracer = trace.get_tracer("sidequest.server.emitters")` + `from opentelemetry import trace`; imported `_PRONOUN_FORMS` from `sidequest.agents.pov_swap` (the canonical single source of truth, exactly as the Reviewer's fix instruction specified). Folded the stale anchor-only call-site comment (emitters.py peer-loop, Reviewer [DOC]) to describe per-recipient re-anchor. The localizer (`swap_to_second_person`) is untouched.

**How the REJECT is resolved:**
- No `ValueError` escapes the emit (`test_158_8_noncanonical_pronoun_recipient_falls_open_to_canonical[×5]`, `…emitter_does_not_crash[×2]`).
- The whole table still gets narration + the NARRATION event persists — no transaction rollback (`test_158_8_noncanonical_pronoun_does_not_brick_the_table[×5]`).
- The fail-open is observable, not silent (`test_158_8_noncanonical_pronoun_emits_skip_span[×5]` — `narration.pov_swap_skipped` with `recipient_pc`/`reason`/`pronouns`). No bare try/except.
- Canonical-pronoun swaps are unaffected (all section-7 facet-2 + `test_pov_swap*` stay green).

**Tests:** GREEN — verified directly (PG-backed, `SIDEQUEST_TEST_DATABASE_URL` set, `-n0`):
- `test_narration_pov_emission.py` + `test_pov_swap_158_8_finding_pins.py` + `test_pov_swap_otel.py` + `test_pov_swap.py` → **126 passed** (the 17 previously-RED rework tests now pass; section-7 unregressed).
- `test_narration_pov_regression.py` → 3 passed.
- Emit-path consumers (`test_emitters.py`, `test_opening_pov_swap_71_5.py`, `test_opening_emit_event_71_13.py`, `test_perception_rewriter_wiring.py`, `test_merged_mp_emitter_projection.py`, `test_confrontation_single_delivery.py`, `test_confrontation_mp_broadcast.py`, `test_projection_end_to_end_wiring.py`, `test_emit_fanout_recipient_drop.py`, `test_deliver_to_connected_recipients_59_22.py`, `test_adr105_b1_secret_invariant_wiring.py`, `test_replay_kind_coverage.py`) → **68 passed, 6 skipped** (env/feature-gated skips, no failures).
- Total: **197 passed, 0 failed, 6 skipped**. Used direct targeted runs rather than the testing-runner subagent because the PG-backed suite SKIPS without `SIDEQUEST_TEST_DATABASE_URL` (which the runner doesn't export).

**Lint/format:** `ruff check sidequest/server/emitters.py` clean; `ruff format --check` — both changed files already formatted.
**Branch:** `feat/158-8-mp-pronoun-localization` (server) — pushed (`575f8a0b..42035ed9`). UI: still no change (the fix is server-side; see the round-1 Dev finding — SM should not open a UI PR).

**Handoff:** To Reviewer (Westley) for re-review of the rework.

## Delivery Findings

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): Story title's "(+ solo reconnect/replay variant)" describes Facet 1, which is already fixed by 153-29 — measured green. Affects the story title/scope only (no code). The remaining real work is Facet 2 (per-recipient re-anchor). *Found by TEA during test design.*
- **Improvement** (non-blocking): The `narration.second_person_swap` span carries `swap_target_name`/`swap_count` but not `recipient_pc`; the OTEL test docstring in `tests/agents/test_pov_swap_otel.py` claims a `recipient_pc` attribute that the span never sets. Affects `sidequest/agents/pov_swap.py` (~L904) / that docstring — Dev may add `recipient_pc` when wiring per-recipient swaps so the GM panel can attribute a swap to a screen, not just a target name. *Found by TEA during test design.*
- **Gap** (non-blocking): The empty-pronoun no-op at `emitters.py:289` (`if not pronouns: return payload_dict`) still has no observability — the Reviewer's [SILENT] finding (`_pronouns_for_pc` conflates "no pronouns" with "PC not in snapshot"). The rework only pins the *unsupported*-pronoun skip span; Dev can route the empty-pronoun no-op through the same `narration.pov_swap_skipped` span (e.g. `reason="no_pronouns"`) for near-free coverage, but no RED test requires it. Affects `sidequest/server/emitters.py::_apply_pov_swap`. *Found by TEA during test design (rework).*
- **Improvement** (non-blocking, root cause): The crash's root is the type gap — `Character.pronouns: str` (character.py:106) is unconstrained while the localizer demands a 3-value enum (Reviewer [TYPE]). The in-function guard is the minimal fix; a `Literal`/validated field or chargen-time normalization would prevent the whole class. Affects `sidequest/game/character.py` + `sidequest/game/builder.py` — candidate follow-up story. *Found by TEA during test design (rework).*

### Dev (implementation)
- **Gap** (non-blocking): The story declares `repos: server,ui`, but the fix is entirely server-side (the per-recipient swap happens at `emit_event` fan-out, before the wire; the UI renders received text verbatim). The `ui` branch `feat/158-8-mp-pronoun-localization` has **no commits**. Affects sprint bookkeeping — SM should NOT open a UI PR at finish; this story is a single-repo (server) delivery. *Found by Dev during implementation.*
- **Gap** (non-blocking, follow-up): The rework added `narration.pov_swap_skipped` only for unsupported pronouns; the empty-pronoun no-op (`if not pronouns: return payload_dict`) in `_apply_pov_swap` is still silent (Reviewer [SILENT] + TEA finding). Folding it into the same span (`reason="no_pronouns"`) is near-free and would close the `_pronouns_for_pc` empty-vs-missing observability gap. Affects `sidequest/server/emitters.py::_apply_pov_swap`. *Found by Dev during implementation (rework).*
- **Improvement** (non-blocking, root cause): The in-function guard is the minimal fix; the class is only fully prevented by constraining `Character.pronouns: str` (character.py) to the canonical set (a `Literal`/validator or chargen-time normalization at builder.py). Worth a dedicated type-hardening story so other localizer callers can't re-trip the crash. Affects `sidequest/game/character.py` + `sidequest/game/builder.py`. *Found by Dev during implementation (rework).*

### Reviewer (code review)
- **Conflict** (blocking): Non-canonical freeform pronouns crash the whole turn. `swap_to_second_person` raises `ValueError` for any pronouns outside `{he/him, she/her, they/them}` (pov_swap.py:877), chargen sets `pronouns_allow_freeform=True` (builder.py:2194), and `_apply_pov_swap` has no guard for non-empty-but-non-canonical values — so a recipient with e.g. "she/they"/"any"/"xe/xem" raises inside the `with repo.transaction()` block (emitters.py:518) and rolls back the NARRATION event for ALL players. Affects `sidequest/server/emitters.py::_apply_pov_swap` (guard `pronouns in _PRONOUN_FORMS` → fail-open to canonical prose + emit a skip span). *Found by Reviewer during code review.* **This is the REJECT.**
- **Improvement** (non-blocking, pre-existing): `_pronouns_for_pc` (emitters.py:247) returns `""` both for "PC found, no pronouns" and "PC not in snapshot at all", so the `if not pronouns` no-op masks a possible snapshot/seat inconsistency with no span/log. The freeform-pronoun fix should add observability to this skip path too. Affects `sidequest/server/emitters.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking, pre-existing, out of diff scope): The solo/emitter Invariant-3 path (emitters.py:~700) serializes the NarrationPayload without stripping the `_visibility` sidecar (anchor_pc/visible_to/pov_strategy/fidelity) — the peer (L157) and merged-MP (L681) paths strip it, the solo path does not, so server-internal routing metadata reaches the solo client. Pre-existing; this diff neither introduces nor fixes it. Affects `sidequest/server/emitters.py` — file a separate story. *Found by Reviewer during code review.*
- **Improvement** (non-blocking, pre-existing): The 153-14 proper-noun-fragment guard's sentence-start exclusion lets a PC name that equals the *trailing token* of a sentence-initial NPC full name swap erroneously (target "Vah" on "Kantos Vah bows..." → "Kantos you bow..."). Pre-existing in the localizer; this story's per-recipient change *widens* its reach to non-anchor recipients. Out of scope (localizer untouched by decision). Affects `sidequest/agents/pov_swap.py::_is_proper_noun_fragment` — candidate follow-up. *Found by Reviewer during code review.*
- **[Round-Trip 2] Conflict RESOLVED** (was blocking): the round-1 freeform-pronoun turn-abort is fixed in commit `42035ed9` — `_apply_pov_swap` guards `pronouns in _PRONOUN_FORMS`, fails open to canonical prose, emits `narration.pov_swap_skipped`. Verified 137/137 green + single-choke-point (only caller is emitters.py:317). *Found by Reviewer during code review (rework re-review).*
- **Improvement** (non-blocking, NEW): the `narration.pov_swap_skipped` span writes the raw player-supplied freeform `pronouns` string to an OTEL attribute (emitters.py:312) — minor PII/no-length-bound concern. Truncate/normalize (e.g. `pronouns[:64]`) or use a placeholder. Best folded into the `Character.pronouns` type-hardening follow-up. Affects `sidequest/server/emitters.py` + `sidequest/game/character.py`. *Found by Reviewer during code review (rework, [SEC][LOW]).*
- **Improvement** (non-blocking, pre-existing): two silent skip-returns in `_apply_pov_swap` lack spans — the empty-pronoun guard (emitters.py:292, conflates no-pronouns vs PC-not-in-snapshot) and the invalid-text guard (emitters.py:314). Route both through `narration.pov_swap_skipped` with distinct `reason` values to match the new instrumented path. Affects `sidequest/server/emitters.py`. *Found by Reviewer during code review (rework, [SILENT]).*

## Design Deviations

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Did not write RED tests for AC1 (MP agreement break) or AC3 (solo agreement break)**
  - Spec source: context-story-158-8.md / session draft ACs — AC1, AC3
  - Spec text: "When a PC name is swapped to 'you' ... dependent gendered pronouns ... are carried to 2nd person" / "A 3rd-person-authored solo action converted to 2nd person carries gendered pronouns too"
  - Implementation: AC1/AC3 covered by GREEN regression pins (`test_pov_swap_158_8_finding_pins.py`) rather than RED tests, because the behavior is already correct on this branch (fixed by 153-29, commit `8dec6bcd`) — measured against the exact playtest repro strings.
  - Rationale: a RED phase requires a failing test; AC1/AC3 cannot fail on current code. Writing them as regression pins both honors "pin Facet 1" (Keith's 2026-06-23 scope decision) and protects the fix from silent regression. RED energy is focused on the only genuine gap, Facet 2 (AC2/AC4).
  - Severity: minor
  - Forward impact: none — AC1/AC3 remain enforced (green); the story delivers Facet 2 (per-recipient re-anchor) only.

- **[Rework] Authored the skip-span OTEL contract the Reviewer left unspecified**
  - Spec source: session Reviewer Assessment (2026-06-23) — [SEC] Fix Required + [RULE]
  - Spec text: "emit an OTEL skip span so the GM panel sees it (per OTEL principle / No-Silent-Fallbacks)"
  - Implementation: the RED tests assert a specific span — name `narration.pov_swap_skipped` with attributes `recipient_pc`, `reason="unsupported_pronouns"`, `pronouns` — rather than any unnamed span. TEA-authored, since the Reviewer named no contract.
  - Rationale: a span needs a stable name + attributes for the GM panel to filter and attribute the fail-open to a screen; this also closes the [SILENT]/`recipient_pc` observability gap the Reviewer and round-1 TEA both flagged.
  - Severity: minor
  - Forward impact: Dev must emit exactly this span/attributes to pass `test_158_8_noncanonical_pronoun_emits_skip_span`; a future story may fold the empty-pronoun no-op (emitters.py:289) into the same span.

- **[Rework] Scoped RED to the blocking crash only; non-blocking Reviewer observations left to follow-up**
  - Spec source: session Reviewer Assessment — [SILENT] (empty-vs-missing pronoun conflation), [TEST] (object-position wiring gap), [SEC] (_visibility solo leak), [EDGE] (Kantos-Vah tail re-anchor)
  - Spec text: "[SILENT] ... should add observability to this skip path"; "[TEST] ... no Facet-2 wiring test for a recipient PC in OBJECT position"
  - Implementation: no RED tests for those; the rework pins only the blocking [SEC]/[RULE] crash, matching the Reviewer's explicit handoff ("recipient with non-canonical pronouns → canonical prose, no ValueError escaping emit, skip span fires").
  - Rationale: those are tagged non-blocking / pre-existing / out-of-scope by the Reviewer; object-position is moot for the freeform path (the guard fails open BEFORE any swap, so token position never matters); widening RED would re-litigate settled scope. Captured as delivery findings instead.
  - Severity: minor
  - Forward impact: empty-pronoun observability, object-position wiring, the `_visibility` solo-leak, and the Kantos-Vah edge remain open follow-ups (none introduced by this story).

### Dev (implementation)
- **Deferred TEA's `recipient_pc` OTEL span attribute (the per-recipient improvement finding)**
  - Spec source: session Delivery Findings — TEA improvement (`narration.second_person_swap` lacks `recipient_pc`)
  - Spec text: "Dev may add `recipient_pc` when wiring per-recipient swaps so the GM panel can attribute a swap to a screen, not just a target name."
  - Implementation: Left the span attributes as-is (`swap_target_name`, `swap_count`). With the re-anchor fix, `swap_target_name` IS now the recipient's own PC, which satisfies AC-4's test and gives a per-recipient signal; adding `recipient_pc` requires threading the recipient id into `swap_to_second_person` (a localizer signature change) that no test requires.
  - Rationale: minimalist discipline — the word was "may", not "must"; the localizer stays untouched per the story scope. Logged as a non-blocking follow-up for a future observability story.
  - Severity: minor
  - Forward impact: none — AC-4 is met; a future story can add `recipient_pc` to the span if the GM panel needs screen-level attribution.

- **[Rework] Guarded ONLY the unsupported-pronoun path; did not add a span to the empty-pronoun no-op**
  - Spec source: session Reviewer Assessment — [SILENT] (`_pronouns_for_pc` conflates "no pronouns" with "PC not in snapshot"); TEA rework Delivery Finding (empty-pronoun no-op lacks observability)
  - Spec text: "The [SEC] fix should add observability to this skip path"; "Dev can route the empty-pronoun no-op through the same `narration.pov_swap_skipped` span ... but no RED test requires it."
  - Implementation: Added the skip span only to the new `pronouns not in _PRONOUN_FORMS` branch. The pre-existing empty-pronoun branch (`if not pronouns: return payload_dict`, emitters.py) still returns silently — unchanged.
  - Rationale: minimalist discipline — both the Reviewer ([SILENT] = non-blocking, pre-existing) and TEA ("no RED test requires it") scoped this as a follow-up. The empty-pronoun path is pre-existing behavior the rework did not introduce or widen; adding a span there is out of the blocking fix's scope.
  - Severity: minor
  - Forward impact: the empty-pronoun / PC-not-in-snapshot conflation remains unobservable — open follow-up (see Delivery Findings). Trivial to fold into the same span later (`reason="no_pronouns"`).

### Reviewer (audit)
- **TEA: "Did not write RED tests for AC1/AC3"** → ✓ ACCEPTED by Reviewer: sound — Facet 1 is measurably green on this branch (153-29); a RED phase cannot have a passing-by-construction test, and pinning it green is exactly what "pin Facet 1" requires. The exact-repro pins are non-vacuous and well-placed.
- **Dev: "Deferred TEA's `recipient_pc` OTEL span attribute"** → ✓ ACCEPTED by Reviewer: sound — "may", not "must"; `swap_target_name` already carries the per-recipient signal (it IS the recipient's own PC post-fix), and threading recipient id into the localizer is out of scope. Reasonable non-blocking follow-up.
- **UNDOCUMENTED (Reviewer audit):** The Dev docstring rewrite of `_apply_pov_swap` is accurate, but the call-site comment at emitters.py:598-601 ("Fires only when the recipient's PC matches the sidecar's anchor_pc … No-op for atmospheric / non-anchor recipients") was NOT updated and now contradicts the code (it describes the old anchor-only behavior). Severity: L. Fold into the rework. → ✓ RESOLVED in rework (Round-Trip 2): the comment is now folded to describe per-recipient re-anchor + the freeform fail-open. [DOC] closed.

**Round-Trip 2 (rework re-review) audit:**
- **TEA [Rework]: "Authored the skip-span OTEL contract the Reviewer left unspecified"** → ✓ ACCEPTED by Reviewer: sound — the Reviewer mandated "a skip span" without naming it; TEA's `narration.pov_swap_skipped` + `recipient_pc`/`reason`/`pronouns` is a clean, discoverable contract that also closes the round-1 `recipient_pc` attribution gap on this path. Dev implemented it verbatim.
- **TEA [Rework]: "Scoped RED to the blocking crash only; non-blocking observations left to follow-up"** → ✓ ACCEPTED by Reviewer: sound — matches my explicit round-1 handoff scope ("recipient with non-canonical pronouns → canonical prose, no ValueError, skip span"). Object-position is genuinely moot for the freeform path (guard fails open before any swap). The deferred items (empty-pronoun span, `_visibility` leak, Kantos-Vah) are correctly non-blocking.
- **Dev [Rework]: "Guarded ONLY the unsupported-pronoun path; did not add a span to the empty-pronoun no-op"** → ✓ ACCEPTED by Reviewer: sound — the empty-pronoun guard is pre-existing and unchanged by this diff; the [SILENT] subagent agrees it's a non-blocking follow-up. Minimalist discipline correct. Logged as a follow-up in Delivery Findings.

## Subagent Results

_Round-Trip 2 (rework re-review, 2026-06-23). Same toggle set as round 1: preflight, silent_failure_hunter, security enabled; the other 6 disabled via `workflow.reviewer_subagents`._

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 | confirmed 0, dismissed 0 (137 passed / 0 failed / 0 skipped; ruff check + format clean; 0 smells) |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings (Reviewer-covered: guard is the single choke point; only caller of `swap_to_second_person` is emitters.py:317) |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 3 | confirmed 0 blocking; the new guard's span is observable (not silent); 2 PRE-EXISTING silent guards (empty-pronoun L292 [SILENT][MED], invalid-text L314 [SILENT][LOW]) confirmed non-blocking/out-of-diff |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings (Reviewer-covered: §8 tests non-vacuous, drive the real `_emit_event` ×16, no source-text wiring; premise-guard prevents vacuity) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings (Reviewer-covered: the round-1 [DOC] stale comment is FIXED in this diff — folded to per-recipient re-anchor) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings (Reviewer-covered: `Character.pronouns: str` unconstrained remains the root cause — non-blocking follow-up; in-function guard is the agreed minimal fix) |
| 7 | reviewer-security | Yes | findings | 1 | confirmed 1 [SEC][LOW] non-blocking (`pronouns` span attribute echoes raw player freeform text — PII/length nit, suggest truncation); DoS fully closed, no cross-player leak, no injection/ReDoS — all verified |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings (Reviewer-covered: guard is minimal — one membership check + skip span; no over-engineering) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings (Reviewer-covered: lang-review python #1–#13 enumerated in Rule Compliance below) |

**All received:** Yes (3 enabled subagents returned clean/findings; 6 disabled subagents covered by Reviewer's own analysis)
**Total findings:** 0 confirmed blocking, 3 confirmed non-blocking (1 [SEC][LOW] new + 2 [SILENT] pre-existing), 0 dismissed

## Reviewer Assessment

**Verdict:** APPROVED _(Round-Trip 2 — rework re-review, 2026-06-23)_

The rework resolves the round-1 blocking [SEC] HIGH exactly as prescribed, with no new blocking issues. `_apply_pov_swap` now guards `pronouns not in _PRONOUN_FORMS` immediately after the empty-pronoun guard: it fails open to canonical 3rd-person prose (`return payload_dict`, the same shape as the existing empty-pronoun branch) and emits a `narration.pov_swap_skipped` OTEL span (`recipient_pc` / `reason="unsupported_pronouns"` / `pronouns`). No bare try/except. The localizer is untouched. The freeform-pronoun turn-abort that bricked the whole table is closed.

**Why APPROVE:** the prescribed fix is implemented faithfully, the guard is a true single choke point (`swap_to_second_person` has exactly one production caller — `emitters.py:317`, inside `_apply_pov_swap`, after the guard — so no path can bypass it), all 137 tests in the POV/emit surface pass, and every remaining finding is LOW or pre-existing/non-blocking. No Critical/High.

**Data flow traced:** player-supplied freeform pronoun (chargen, `pronouns_allow_freeform`) → `Character.pronouns` → `_pronouns_for_pc` → `_apply_pov_swap` guard `pronouns not in _PRONOUN_FORMS` → **skip span + `return payload_dict`** (the already-projected, perception-filtered per-recipient dict) → `_deliver_fanout` after the committed transaction. Safe: the untrusted value is validated against the canonical set before reaching `swap_to_second_person`; the fail-open returns the recipient's own already-filtered frame (recipient reads their own PC in 3rd person — cosmetic degradation, no cross-player leak); the NARRATION event commits, so the table is not bricked.

### Observations (tagged by source)

- **[VERIFIED] DoS closed — single choke point.** `swap_to_second_person`'s only production caller is `emitters.py:317` inside `_apply_pov_swap`; the guard at `emitters.py:297` short-circuits every non-canonical value before that call. Evidence: `grep -rn swap_to_second_person sidequest/` → one call site + def + docstring example. Confirmed by [SEC] subagent.
- **[VERIFIED] Fail-open is observable, not silent.** The guard emits `narration.pov_swap_skipped` with `recipient_pc`/`reason`/`pronouns` (`emitters.py:309-312`), satisfying the OTEL Observability Principle + No-Silent-Fallbacks. Confirmed by [SILENT] subagent (span fires, closes on `with` exit, then returns). The skip span even closes the round-1 `recipient_pc` attribution gap on this path.
- **[SEC] (LOW, non-blocking, NEW)** The `pronouns` span attribute (`emitters.py:312`) echoes raw player-supplied freeform text to the trace store — minor PII/no-length-bound concern. Severity LOW: the GM panel is a local dev-side observability surface (Keith's lie-detector, not a third-party sink); pronouns are low-sensitivity; the same string already lives in `snapshot.characters[].pronouns`. No injection (OTEL attrs are typed strings) and no ReDoS (constant-time dict membership). Recommend folding a truncation/normalization into the `Character.pronouns` hardening follow-up rather than blocking here.
- **[SILENT] (MED, non-blocking, PRE-EXISTING)** The empty-pronoun guard (`emitters.py:292`, `if not pronouns: return`) returns silently with no span and conflates "PC has no pronouns" with "PC not in snapshot" (`_pronouns_for_pc` falls off the loop → `""`). Unchanged by this diff; now conspicuous next to the new instrumented guard. Follow-up: route it through the same span with `reason="pronouns_empty"` / `reason="pc_not_in_snapshot"`.
- **[SILENT] (LOW, non-blocking, PRE-EXISTING)** The invalid-text guard (`emitters.py:314`, `if not isinstance(text, str) or not text: return`) also returns silently. Pre-existing; a `reason="text_missing_or_invalid"` skip span would match the new pattern. Follow-up.
- **[DOC] (resolved)** The round-1 stale call-site comment (old anchor-only wording) is now FOLDED to describe per-recipient re-anchor + the freeform fail-open (`emitters.py` peer-loop comment). Round-1 [DOC] finding closed.
- **[TEST] (VERIFIED good)** §8 adds 17 behavioral tests + a premise-guard, driving the real `handler._emit_event` fan-out (16 call sites), no source-text wiring (`grep` confirms none). Coverage: fail-open-to-canonical ×5, table-not-bricked-with-EventLog-persisted ×5, emitter-call-site ×2, skip-span ×5 — all parametrized over genuinely non-canonical values (premise-guard pins non-vacuity). The round-1 [TEST] object-position note is moot for the freeform path (the guard fails open before any swap, so token position never matters).
- **[TYPE] (non-blocking, root cause — unchanged)** `Character.pronouns: str` (character.py) remains unconstrained vs the localizer's 3-value set. The in-function guard is the agreed minimal fix; a `Literal`/validated field or chargen-time normalization is the durable follow-up (fold the [SEC] truncation concern in here).
- **[EDGE] (non-blocking, pre-existing — unchanged)** The 153-14 sentence-start fragment edge ("Kantos Vah"→"Kantos you") is untouched (localizer unchanged); still a candidate follow-up.
- **[SIMPLE] (VERIFIED good)** The fix is minimal — one dict-membership check + a 3-attribute skip span + an early return. No over-engineering; `_PRONOUN_FORMS` reused as the single source of truth (Reviewer-sanctioned in round 1) rather than duplicating the canonical set.
- **[RULE]** lang-review python: #1 no silent swallowing (the fail-open is span-observable, not a swallowed exception — compliant); #6 test quality (non-vacuous, no skips, behavioral — compliant); #7 resource handling (span uses `with` — compliant); #10 import hygiene (`from opentelemetry import trace` correctly at runtime scope, `_PRONOUN_FORMS` private import sanctioned, no cycle — pov_swap does not import emitters); #11 input validation (untrusted pronouns validated before use — compliant). #2/#3/#5/#8/#9/#12 N/A to this diff. Full enumeration in Rule Compliance below.

### Rule Compliance (lang-review python #1–#13, enumerated against the diff)

| # | Rule | Instances in diff | Verdict |
|---|------|-------------------|---------|
| 1 | Silent exception swallowing | fail-open guard (emitters.py:297-313) | COMPLIANT — guarded return with an OTEL span; not an `except`/`suppress`/bare-catch |
| 2 | Mutable default args | none | N/A |
| 3 | Type annotation gaps | `_apply_pov_swap` signature unchanged (already annotated); no new public fn | COMPLIANT |
| 4 | Logging coverage/correctness | subsystem decision uses an OTEL span (correct channel); no `logger` sensitive-data leak | COMPLIANT (span attr PII = [SEC][LOW] nit, not a logging-rule violation) |
| 5 | Path handling | none | N/A |
| 6 | Test quality | §8 (17 tests + premise-guard) | COMPLIANT — exact-value asserts, EventLog-persisted predicate, span-attribute asserts; no `assert True`, no skips, params genuinely distinct |
| 7 | Resource leaks | `with _tracer.start_as_current_span(...)` (emitters.py:309) | COMPLIANT — context-managed span |
| 8 | Unsafe deserialization | none | N/A |
| 9 | Async pitfalls | sync code | N/A |
| 10 | Import hygiene | `from opentelemetry import trace`; `from ...pov_swap import _PRONOUN_FORMS` | COMPLIANT — runtime-scoped (used at runtime), no star import, no circular import |
| 11 | Security: input validation | `pronouns` (untrusted) checked vs `_PRONOUN_FORMS` before use (emitters.py:297) | COMPLIANT |
| 12 | Dependency hygiene | no dep changes | N/A |
| 13 | Fix-introduced regressions | re-scan of the guard | COMPLIANT — single choke point covers all call sites; only nit is the [SEC][LOW] span-attr PII (non-blocking) |

### Devil's Advocate

Could the rework still break? I pushed on four angles. **(1) Bypass.** If any code path called `swap_to_second_person` directly — opening narration, the solo emitter frame, a future caller — the guard in `_apply_pov_swap` wouldn't protect it and the table-abort would persist there. I grepped: the localizer has exactly one production caller, `emitters.py:317`, downstream of the guard. No bypass today; the risk is a *future* caller that forgets the guard — which is precisely why the [TYPE] root-cause (constrain `Character.pronouns`) matters as a follow-up, so the localizer can't be handed a bad value from anywhere. **(2) A "canonical-looking" value that still raises.** The guard uses the *same* `_PRONOUN_FORMS` dict that `swap_to_second_person` keys on, so they cannot drift — any value the localizer would reject is rejected by the guard first. The only other raise in the localizer is empty `target_name`, already handled by the `recipient_pc_name is None` early return. **(3) The fail-open leaks something.** It returns `payload_dict` unchanged — but that dict is the *already-projected, perception-filtered* per-recipient frame, not the canonical union; the swap only ever rewrites the recipient's own name, so skipping it exposes nothing cross-player. A freeform-pronoun player simply reads their own PC in third person — ugly, not a breach. **(4) A malicious player weaponizes the span.** They set their pronoun to a 10MB string or an identifying name. The span attribute carries it verbatim — a real but LOW concern: it's a local dev-side trace store, the same string already rides in the snapshot, OTEL attrs are typed (no injection), and the SDK truncates oversized values rather than crashing the turn. Worst case is a bloated trace and a PII smell in Keith's own panel — bounded by the future chargen-length/normalization fix. None of these rise to blocking. The one thing I'd insist on long-term is the type constraint, so the crash class is impossible rather than guarded at one site. For this story's scope — close the table-wide DoS, observably — the rework is correct and complete.

**Handoff:** To SM (Vizzini) for finish-story.

---
_Round-Trip 1 verdict (REJECTED, 2026-06-23) — SUPERSEDED by the APPROVED rework above. Preserved for the record:_

> **REJECTED** — [HIGH][SEC] Non-canonical freeform pronouns made `swap_to_second_person` raise `ValueError` inside `emit_event`'s `repo.transaction()`, rolling back the NARRATION turn for the whole table. Fix required: guard `pronouns in _PRONOUN_FORMS` → fail-open to canonical prose + OTEL skip span. Routed to red rework → TEA failing tests (commit 61dbd452) → Dev guard (commit 42035ed9). Resolved.