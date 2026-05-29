---
parent: context-epic-59.md
workflow: trivial
---

# Story 59-24: Extend leak_audit cross_player coverage

## ⚠️ Staleness Check

**The gap is LIVE as of 2026-05-29** — verified against current code while
authoring this context (post-59-9 merge). This is the **direct sibling** of
59-9 (merged PR #515): 59-9 closed the *primary* perception-firewall hole in
`redact_dispatch_package`; 59-24 closes the matching blind spot in the
*secondary* safety net. The asymmetry is the same one-loop omission, one file
over.

Evidence (read at `sidequest/telemetry/leak_audit.py:76-84`):

- `audit_canonical_prose` builds `redacted_entities` by looping **only**
  `package.per_player` (line 77: `for pd in package.per_player`). It checks
  each `SubsystemDispatch.visibility.redact_from_narrator_canonical` (line 81)
  and collects `d.params["target"]` (lines 82-84). **`package.cross_player` is
  never iterated.**
- A `cross_player` `CrossAction` carries `dispatch: list[SubsystemDispatch]`
  (`protocol/dispatch.py:183`), each with the same redactable `VisibilityTag`.
  So a cross_player redacted dispatch's `target` token is **never added to
  `redacted_entities`**, and the leak scan (lines 89-97) therefore never looks
  for it in the prose.
- Net effect: if a cross_player redacted entity's token leaks into canonical
  narrator prose, `audit_canonical_prose` returns `leaks_detected=0` and the
  `narrator.canonical_leak_audit` OTEL span reports a **clean audit** — a
  **false negative**. The GM-panel lie-detector is blind to the entire
  cross_player dimension.
- This exactly mirrors the gap 59-9 just fixed in `redact_dispatch_package`,
  where every other cross_player consumer (`run_dispatch_bank`, the engagement
  watcher, the idempotency validator) iterates `cross_player` and only these
  two redaction-aware consumers forgot it. 59-9 fixed the redactor; this fixes
  the auditor.

## Business Context

`audit_canonical_prose` is the **lie-detector** for the structural-hiding
firewall (ADR-104/105, SOUL "Illusionism"). The CLAUDE.md OTEL Observability
Principle is explicit: the GM panel is how we catch the narrator improvising or
a firewall regressing. A leak audit that cannot see cross_player gives a
**false sense of safety** — precisely the failure mode OTEL exists to prevent.

**This is NOT a live leak today.** 59-9 closed the actual hole: redacted
cross_player dispatches no longer reach the narrator. 59-24 is **defense in
depth** — it ensures a *future* regression in cross_player redaction would be
*caught* by the audit instead of passing silently. The call sites
(`orchestrator.py` ~3070, ~3407) correctly pass the **canonical, pre-redaction**
package to the audit (the audit must know what was *supposed* to be hidden to
verify it wasn't leaked) — so the fix is entirely inside `leak_audit.py`; no
call-site change.

## Technical Guardrails

**File to modify:**
- `sidequest/telemetry/leak_audit.py` — `audit_canonical_prose` (lines 76-84).
  Add a `cross_player` collection branch mirroring the existing `per_player`
  loop.

**Test file to extend:**
- `tests/telemetry/test_leak_audit.py` — add a cross_player case alongside the
  existing per_player cases.

**Pattern to follow (the existing per_player loop, lines 77-84):**
```python
for pd in package.per_player:
    for d in pd.dispatch:
        if not isinstance(d, SubsystemDispatch):
            continue
        if d.visibility.redact_from_narrator_canonical:
            target = d.params.get("target") if isinstance(d.params, dict) else None
            if isinstance(target, str):
                redacted_entities.append(target)
```
Add the analogous loop over `package.cross_player`, iterating `ca.dispatch`
(CrossAction has fields `participants`, `witnesses`, `dispatch` only — no
`narrator_instructions`). Keep the same `isinstance` guards and the same
`params["target"]` extraction. Append into the **same** `redacted_entities`
list so the existing leak scan (lines 89-97) and the existing
`redact_tag_count` span attribute (line 102/110) cover cross_player with no
further change.

**OTEL — reuse, don't add:** the existing `narrator.canonical_leak_audit` span
(lines 107-112) already reports `redact_tag_count=len(redacted_entities)` and
`leaks_detected`. Cross_player targets flowing into `redacted_entities` means
they are counted by the existing span. Do **NOT** add a new span (CLAUDE.md
flags cosmetic/label-only changes as not needing spans; this is the same
accumulator reuse pattern 59-9 used).

## Scope Boundaries

**In scope:**
- Extend `audit_canonical_prose` to collect redacted `target`s from
  `package.cross_player[*].dispatch` into the same `redacted_entities` list.
- One+ test pinning cross_player leak detection (FAILS against current main).

**Out of scope:**
- Any change to the `per_player` collection (already correct).
- Any call-site change in `orchestrator.py` — the canonical package is passed
  on purpose; do not switch it to the redacted view.
- `CrossAction` schema changes, fidelity / `secrets_for` / `visible_to`
  handling (ADR-105 broadcast concern, separate).
- Adding a new OTEL span (reuse `narrator.canonical_leak_audit`).
- Touching `redact_dispatch_package` (that was 59-9, already merged).

## AC Context

The trivial-fix bar is one test that FAILS against current `main` and pins the
new behavior.

**AC1 — Cross_player redacted target is leak-detected:** Build a
`DispatchPackage` with a `cross_player=[CrossAction(...)]` whose `dispatch`
contains a `SubsystemDispatch` with `redact_from_narrator_canonical=True` and
`params={"target": "<entity_id>"}`. Pass `prose` that contains a token for that
entity (via `entity_tokens_by_id`). Assert the result has `leaks_detected >= 1`
and the entity in `leaked_entities`. Against current code this returns
`leaks_detected=0` (the cross_player target is never collected) → RED.

**AC2 — Cross_player redacted target counted in `redact_tag_count`:** A
cross_player redacted dispatch contributes to `redact_tag_count` (the span
attribute). Either a cross_player-only package yields `redact_tag_count >= 1`,
or a mixed per_player+cross_player package counts both — proving cross_player
flows through the same `redacted_entities` accumulator.

**AC3 — No false positive:** A cross_player dispatch with
`redact_from_narrator_canonical=False` (or whose token is absent from prose)
does not register a leak — confirms the fix does not over-detect.

## Assumptions

- `CrossAction.dispatch` is the only redaction-bearing field on cross_player
  (schema `dispatch.py:180-184`); the `target` lives in
  `SubsystemDispatch.params["target"]`, same as per_player.
- The canonical (pre-redaction) package reaching the audit already contains the
  cross_player dispatches (redaction happens separately for the narrator-visible
  view); confirmed by the docstring at `leak_audit.py:63-66`.
- Reference implementation: the 59-9 fix in
  `sidequest/agents/prompt_redaction.py` (merged PR #515) and its archived
  session `sprint/archive/59-9-session.md`.
