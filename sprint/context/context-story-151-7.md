---
parent: context-epic-151.md
workflow: tdd
---

# Story 151-7: Playtest validation gate

## Business Context

The closing gate (mirrors ADR-113's 59-8): confirm the migration did **not** harm
prose quality and that sidecar fidelity is **at or above** the pre-migration
catch-loop floor. The narrator's bar is Keith's: *good enough to fool a career GM* —
the whole point of freeing its attention was to make the prose better, so a
regression here is a real failure, not a footnote. The GM-panel
`sidecar_extraction.mismatch` rate is the quantitative metric.

## Technical Guardrails

- **Run a playtest** (headless or full per the `sq-playtest` skill) exercising turns
  that touch every migrated field: items, gold, companions, `npcs_present` (incl. a
  confrontation for `side`), `mood`/`visual_scene`/`footnotes`, and single-PC
  perception (`private_segments`) in MP.
- **Measure on the GM panel (OTEL):** `sidecar_extraction.run/.{field}/.mismatch`
  rates; compare sidecar fidelity to the pre-migration baseline (the catch-loop miss
  rate).
- **Pull, don't just restart** (project memory
  `feedback_playtest_verify_pull_not_just_restart`): measure the running binary AFTER
  a FF-pull of server + content; a stale tree masks the truth.
- If a regression is found, **file a follow-up bug** — do not patch within this
  validation story (keep the gate honest).

## Scope Boundaries

**In scope:**
- The validation playtest, the pass/fail criteria, and the metric writeup / sign-off.

**Out of scope:**
- Any code change. Regressions become new stories/bugs, not in-place fixes here.

## AC Context

1. **Coverage:** the playtest exercises items, gold, companions, `npcs_present` (with
   a confrontation), cosmetic fields, and single-PC perception.
2. **Prose unharmed:** narrator prose quality is judged at-or-above pre-migration
   (subjective + Keith sign-off — the career-GM bar).
3. **Fidelity floor:** sidecar fidelity is ≥ the pre-migration catch-loop floor (no
   *more* missed/wrong fields than before the migration).
4. **Mismatch metric:** `sidecar_extraction.mismatch` rate is observable on the GM
   panel and within an agreed tolerance.
5. **Firewall holds in MP:** no single-PC perception leaks into any peer's PART 1.

## Assumptions

- **Depends on 151-6 merged** (full migration complete). Blocked otherwise.
- A measurable pre-migration baseline exists or can be reconstructed (the catch-loop
  miss rate before cutover).
- `sq-playtest` infrastructure is available; the GM panel surfaces the new spans.
