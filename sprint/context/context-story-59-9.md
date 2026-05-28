---
parent: context-epic-59.md
workflow: trivial
---

# Story 59-9: Fix cross_player redaction gap in redact_dispatch_package

## ⚠️ Staleness Check

**The gap is LIVE as of 2026-05-28.** Epic 59 backlog stories have a known
staleness pattern (many overtaken by fast IntentRouter landings), so this was
verified against current code before writing — and the bug is real.

Evidence:

- `redact_dispatch_package` (`sidequest/agents/prompt_redaction.py:26-76`) loops
  **only** `pkg.per_player` (line 37: `for pd in pkg.per_player`). It strips
  redacted `SubsystemDispatch` and `NarratorDirective` entries from each
  `PlayerDispatch`, then rebuilds the package with `per_player=new_players`
  (line 75). **`pkg.cross_player` is never read, never filtered, and copied
  through unchanged.**
- `CrossAction` (`sidequest/protocol/dispatch.py:165-168`) carries
  `dispatch: list[SubsystemDispatch]`, and every `SubsystemDispatch` carries a
  `visibility: VisibilityTag` (`dispatch.py:96`) which can be
  `redact_from_narrator_canonical=True` (`dispatch.py:58`). So a cross_player
  dispatch *can* be flagged for redaction — the type permits it — but the
  redactor has no branch to act on it.
- The blind spot is load-bearing because the redactor is **live on the narrator
  prompt path**: `build_narrator_prompt` calls it at
  `orchestrator.py:1622-1627`, then passes the supposedly-redacted
  `visible_dispatch_package` into `run_dispatch_bank` at `orchestrator.py:2562`.
  `run_dispatch_bank` (`subsystems/__init__.py:200-206`) explicitly *does*
  iterate `cross_player` (line 205) and folds those dispatches' directives into
  the high-attention narrator block. **Net effect: a cross_player dispatch tagged
  `redact_from_narrator_canonical=True` survives redaction and reaches the
  narrator — a perception-firewall hole.**
- Asymmetry proof that this is an oversight, not a design choice: the
  dispatch-bank executor (`subsystems/__init__.py:205`), the lie-detector watcher
  (`dispatch_engagement_watcher.py:193`), the dispatch counter
  (`intent_router.py:170`), the pass-summary counter (`intent_router_pass.py:183`),
  and the idempotency-key validator (`dispatch.py:229`) **all** iterate
  `cross_player`. The redactor is the lone consumer that forgets it.
- No existing test covers cross_player redaction. `tests/agents/test_prompt_redaction.py`
  has three cases (`test_redacted_dispatch_stripped_entirely`,
  `test_redacted_narrator_directive_stripped`, `test_no_redactions_is_noop`) —
  all build `per_player`-only packages. The gap is untested.

## Business Context

Epic 59's IntentRouter spine engages mechanical engines *before* the narrator
runs, then the narrator narrates already-real state. `redact_dispatch_package`
is the **structural defense** of the ADR-104/105 perception firewall on that
path: it strips dispatches the narrator must not know about (e.g. a sealed PvP
action, a secret per-player outcome) so the narrator "cannot leak what it was
never told" (module docstring, `prompt_redaction.py:5-6`).

ADR-105 ("Broadcast-Layer Perception Firewall") exists precisely because a
merged multiplayer turn has **no single `perspective_pc`** the tool-layer filter
(ADR-104, `narrator_perception_filter.py`) can be correct for — so the SDK
narrator composes one shared narration covering multiple PCs
(`105-broadcast-layer-perception-firewall.md:35-45`). Cross_player dispatches
are the data structure for exactly those multi-PC interactions
(`dispatch.py:160-168`, "Group G extends"). A redaction gap in `cross_player` is
therefore not an edge case — it is the gap directly over the surface ADR-105 was
written to close. A secret cross-player dispatch leaking into the shared
narration is the SOUL "Illusionism" firewall failing in its highest-stakes case.

This is a 1-pt trivial fix: extend the redactor's loop to cover `cross_player`,
matching the symmetry every other consumer already has, and pin it with a test.

## Technical Guardrails

**File to modify:**
- `sidequest/agents/prompt_redaction.py` — `redact_dispatch_package` (lines 26-76).
  Add a `cross_player` filtering branch mirroring the existing `per_player` logic.

**Test file to extend:**
- `tests/agents/test_prompt_redaction.py` — add a cross_player redaction case
  alongside the three existing per_player cases.

**Pattern to follow (the existing per_player loop, lines 37-60):**
- For each `CrossAction` in `pkg.cross_player`, filter its `dispatch` list:
  entries with `d.visibility.redact_from_narrator_canonical` go to `removed`;
  the rest are kept.
- Rebuild each `CrossAction` with `model_copy(update={"dispatch": kept})` (the
  per_player branch uses `pd.model_copy(...)` at lines 53-59 — use the same
  immutable-copy idiom, do not mutate in place).
- Append the rebuilt `CrossAction` list into the final
  `pkg.model_copy(update={...})` at line 75 (currently only updates
  `per_player`).

**OTEL — reuse, don't add:** the existing `prompt.redaction.structural` span
(lines 62-73) already records `redacted_count`, `redacted_kinds`, and
`redacted_idempotency_keys` over the combined `removed` list. Cross_player
removals must land in that **same** `removed` list so they are counted in the
existing span. Do NOT add a second span — the per-subsystem decision is already
covered, and CLAUDE.md flags label/cosmetic-only changes as not needing new
spans. The fix is correct when cross_player removals show up in the existing
span's attributes.

**`CrossAction` shape constraint:** `CrossAction` has **no**
`narrator_instructions` field (only `participants`, `witnesses`, `dispatch` —
`dispatch.py:165-168`; confirmed by the comment at `subsystems/__init__.py:203`:
"CrossAction has no narrator_instructions field"). So the cross_player branch
filters `dispatch` ONLY. Do not invent a directive filter for cross_player.

**LethalityVerdict:** unchanged — it carries no `VisibilityTag` in the current
protocol (`prompt_redaction.py:50-52` documents this); the cross_player branch
does not touch lethality.

## Scope Boundaries

**In scope:**
- Extend `redact_dispatch_package` to filter `cross_player[*].dispatch` by
  `redact_from_narrator_canonical`, routing removals into the same `removed` list.
- Rebuild the returned package with the filtered `cross_player`.
- One new test pinning cross_player redaction behavior.

**Out of scope:**
- Any change to the `per_player` filtering (already correct — do not refactor it).
- Adding directive filtering for cross_player (the type has no
  `narrator_instructions`).
- Adding a new OTEL span (reuse the existing `prompt.redaction.structural`).
- `CrossAction` schema changes, the `_witnesses_include_participants` validator
  (`dispatch.py:170-195`), or any perception-fidelity / `secrets_for` /
  `visible_to` handling — this story is *only* the binary
  `redact_from_narrator_canonical` strip. Fidelity-based asymmetric rewriting is
  ADR-105's broadcast-layer concern, separate from structural hiding.
- The SECRET_NOTE routing of removed entries (`orchestrator.py:1518`,
  `_last_secret_routes`) — that consumer already reads `removed`; once
  cross_player removals are in `removed`, routing works without further change.

## AC Context

The trivial-fix bar is one test that pins the specific redaction behavior. The
test must demonstrate the gap-before / fixed-after distinction — i.e. it would
FAIL against current `main`.

**AC1 — Redacted cross_player dispatch is stripped from the package:**
Build a `DispatchPackage` with a `cross_player=[CrossAction(...)]` whose
`dispatch` contains two `SubsystemDispatch` entries: one with
`redact_from_narrator_canonical=True`, one with it `False` (mirror the helper
fixtures `_redacted_viz` / `_open_viz` already in
`test_prompt_redaction.py:21-36`). Call `redact_dispatch_package(pkg)`. Assert:
(a) the redacted entry appears in `removed` (by `idempotency_key`); (b) the
returned package's `cross_player[0].dispatch` retains ONLY the open entry; (c)
the open entry's `idempotency_key` is the surviving one. This is the exact shape
of the existing `test_redacted_dispatch_stripped_entirely`
(`test_prompt_redaction.py:39-68`), retargeted from `per_player` to
`cross_player`.

**AC2 — Cross_player removals are counted in the existing span:** Either assert
the combined `removed` list length includes both per_player and cross_player
removals when a package mixes them, or (lighter) assert that a cross_player-only
redacted package yields `len(removed) == 1`. The point is that cross_player
removals flow through the same `removed` accumulator the span reads — not a
separate path. (A per_player + cross_player mixed-package case is the strongest
single assertion.)

**AC3 — No-op safety preserved:** A `cross_player` `CrossAction` with all
dispatches `redact_from_narrator_canonical=False` is returned unchanged (nothing
in `removed`, dispatch list intact). Confirms the fix does not over-strip — the
cross_player analogue of `test_no_redactions_is_noop`
(`test_prompt_redaction.py:100-108`).

## Assumptions

- `CrossAction.dispatch` is the only redaction-bearing field on cross_player;
  confirmed by the schema (`dispatch.py:165-168`) — no `narrator_instructions`,
  no top-level visibility on `CrossAction` itself.
- The existing `removed` list type signature
  (`list[SubsystemDispatch | NarratorDirective | LethalityVerdict]`,
  `prompt_redaction.py:34`) already accommodates the `SubsystemDispatch` entries
  cross_player contributes — no signature change needed.
- `model_copy` is the established immutable-rebuild idiom in this function
  (`prompt_redaction.py:54`, `:75`); the fix follows it rather than mutating.
