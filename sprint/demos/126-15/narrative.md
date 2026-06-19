# Narrative

## Problem Statement
Problem: The engineering team's internal reference manual had mislabeled road signs — nine backend files were citing "ADR-149" as the authority for how the Fate combat defense system works, but ADR-149 is actually the rulebook about *game content licensing*, not combat mechanics. Anyone following those citations landed in completely the wrong place. Additionally, the defense system itself had never been formally documented anywhere.

Why it matters: When engineers troubleshoot combat bugs or extend the system, they follow the citation trail. Wrong citations waste debugging time, create confusion about what the system is supposed to do, and erode trust in the documentation as a whole. An undocumented system is a system that can only be understood by reading raw code — which means slower onboarding, riskier changes, and no authoritative "source of truth" when behavior is disputed.

---

## What Changed
Think of the project's Architecture Decision Records (ADRs) as a library of engineering rulebooks — each numbered document explains why a system works the way it does.

**Before:** Nine backend files contained comments saying "see ADR-148/149 for why this works." ADR-149 is the rulebook about game content licensing (the SRD chapter). Nobody had written the actual rulebook for the Fate combat defense barrier at all.

**After:** A brand new rulebook — ADR-151 — was written that formally documents exactly how the defense barrier works (the four-phase combat round, how the server waits for a player to roll dice before proceeding, how it handles players quitting mid-fight, and how the system logs everything for verification). All nine files now correctly cite "ADR-148/151" — pointing to the right chapters. Old references in two other documents that also pointed at the now-wrong ADR-149 were cleaned up as well.

Zero game behavior changed. This was entirely a documentation accuracy fix.

---

## Why This Approach
The fix was "find every wrong citation, replace with the right one, and write the missing document." That's the right call because:

1. **The mismatch was systematic, not one-off.** ADR-149 was reserved as a placeholder for the defense barrier before it was reclassified as SRD content. So every file that cited it was citing a reservation that had been quietly reassigned — a widespread, consistent error with a single root cause.
2. **Writing the ADR first made the replacement obvious.** Once ADR-151 existed as the real home for defense-barrier documentation, it was unambiguous which citation to use in each file. The team categorized each occurrence (roll-source vs. SRD-content vs. defense-barrier) rather than doing a blind find-and-replace — then discovered that in practice every server occurrence was the defense-barrier case, making the fix uniform.
3. **No code changes means no risk.** Every edit was inside comments and documentation strings. The Python compiler verified nothing executable changed; a search confirmed zero remaining wrong citations.

---

## Before/After
| | Before | After |
|---|---|---|
| **Citation in 9 server files** | `# See ADR-148/149` | `# See ADR-148/151` |
| **Where citation leads** | ADR-149: SRD content licensing (irrelevant to combat) | ADR-151: Fate DEFEND barrier — four-phase round, block-and-wait, pending_defenses ledger |
| **DEFEND barrier documentation** | None — system existed in code only, no formal spec | ADR-151: complete record of mechanism, contract, authorization, concession, and observability |
| **ADR-148 §6 forward reference** | "Story 126-8 / ADR-149" (stale placeholder) | "Story 126-8 / ADR-151" (correct, with one-line history note) |
| **Remaining wrong citations** | 9+ files, 25 occurrences | Zero — `grep -rn 'ADR-148/149' sidequest/` returns empty |
| **Risk to game behavior** | N/A (pre-fix) | Zero — every change is a comment or docstring; `py_compile` passes on all 9 files |
