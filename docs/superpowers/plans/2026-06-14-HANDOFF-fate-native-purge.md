# HANDOFF — F1c shipped; next: purge native-ruleset creep from the Fate plans/spec

**Date:** 2026-06-14 · **Author:** Architect (Neo) · **For:** a fresh-context session

---

## 1. What just shipped — F1c (DONE)

The Fate Core conflict-exchange engine is **complete and in review**:

- **PR:** https://github.com/slabgorb-org/sidequest-server/pull/857 → base `develop`, branch `feat/f1c-fate-conflict`.
- **What it is:** `sidequest/server/dispatch/fate_conflict.py` — mirrors `wn_round.py` one tier over. Sealed-commit barrier (`encounter.fate_commits`, sibling to `wn_commits`), Notice/Empathy turn order, the three proactive Fate actions (overcome / create_advantage / attack) + reactive engine-rolled defend, shift absorption into stress+consequences (delegates to F1b mutators), taken-out (`withdrawn`) vs concede, every decision emitting a `fate.*` OTEL span.
- **Tests:** 16 in `tests/server/dispatch/test_fate_conflict.py` (drive the **real registered** `FateRulesetModule` + a real `InMemorySpanExporter` = the suite's wiring test) + 4 model tests. Full sweep 382 passed; WN sealed-round regression 11 passed (native/WN path 0 diff lines); pyright 0; ruff clean.
- **7 commits** (one per TDD task + format fixup + final-review follow-ups). Built via `superpowers:subagent-driven-development` (implementer → spec review → code-quality review per task, + a holistic final review = APPROVE FOR MERGE).
- **Plan (corrected):** `docs/superpowers/plans/2026-06-14-f1c-fate-conflict-exchange-engine.md`.

### The native-creep already removed in F1c
The F1c plan draft had smuggled in a **d20 `full_defense`** action (forgo your turn for +2 to defenses) as a fourth committed action with a hand-tuned +2 stance. Keith ruled it out ("remove all native ruleset, one more time"). It was purged from the F1c plan AND the shipped code: the `FateSealedCommit.action` Literal is `["overcome", "create_advantage", "attack"]`; defense is reactive (engine-rolled); no `full_defenders` set; no +2 stance. The only `full_defense` strings left in F1c docs are explicit **negations** ("there is no full_defense — not in the Fate SRD").

---

## 2. NEXT STEPS — purge the remaining "port it to native" creep

**Standing ruling (Keith, emphatic, 2026-06-14):** *Bind the Ruleset, Don't Balance It.* Fate Core's actions are exactly four — **Overcome / Create an Advantage / Attack / (reactive) Defend.** "Full/total defense" (+2 stance) is a **d20/Pathfinder import, NOT in the Fate SRD** = native creep. Purge on sight. This keeps getting re-added; it is doctrine now. See ADR-143/ADR-144, SOUL.md, and memories `[[fate-four-actions-no-full-defense]]`, `[[fate-core-replaces-native-two-srd-end-state]]`, `[[wwn-combat-is-wn-round-engine-never-balance-native]]`, `[[defer-to-srd-for-mechanics]]`.

### Concrete targets (verified 2026-06-14)

**A. F1d plan** — `docs/superpowers/plans/2026-06-14-f1d-fate-dispatch-routing.md` (NOT yet implemented; purge BEFORE building it):
- **Line 31** — rationale lists the action set as `{overcome, create_advantage, attack, full_defense, concede}` → drop `full_defense` → `{overcome, create_advantage, attack, concede}`.
- **Line 164** — `FateActionPayload.action: Literal["overcome", "create_advantage", "attack", "full_defense", "concede"]` → drop `full_defense`. (Mirror the shipped `FateAction` Literal in `encounter.py`, which is `["overcome","create_advantage","attack"]`; the payload adds `"concede"` since concede is a pre-roll routing value, not a committed action.)
- **Lines 152-153** docstring — "the four committed actions plus `concede`" → "the three proactive actions plus `concede`".
- **Lines 473-490** `dispatch_fate_action` — remove the `full_defense` special-case. Currently: `# full_defense seals no roll...` + `if payload.action != "full_defense":` guards the roll/seal. With full_defense gone, **all three** proactive actions seal a roll, so the guard becomes unconditional (concede already returns earlier at line 452 via `concede_in_conflict`). End state: compute `outcome = ruleset.resolve_action(...)`, set `ladder_total, dice`, then `seal_fate_commit(...)` — no conditional.
- **Line 436** docstring — "the four proactive actions seal via seal_fate_commit" → "the three proactive actions...".
- Check the F1d tests for any `full_defense` action value and remove/replace.

**B. Design spec** — `docs/superpowers/specs/2026-06-14-fate-core-binding-replaces-native-design.md`:
- **Line 75** — "...{...attack, defend}; full-defense option (+2 to all defends, no proactive action)." → strike the full-defense clause; the action set is overcome/create-advantage/attack + reactive defend.
- **Line 155** — F1c acceptance bullet mentions "full-defense" → replace with the clean-miss / tie-boost coverage that actually shipped.

**C. Sweep for anything else.** Before declaring done:
```bash
# Should return ONLY explicit negations ("there is no full_defense"):
grep -rni "full[_-]defen" docs/superpowers/ docs/adr/144*.md sidequest-server/sidequest sidequest-server/tests
# Watch also for other native re-imports into the Fate path: HP/HpPool usage in fate_*,
# bespoke +2 stances, range/movement balancing subsystems, native beat/dial language
# applied to Fate. (Legit mentions like "replaces the native ruleset" / "no native/WN
# regressions" are FINE — they're about removing native, not porting to it.)
```

### How to verify the purge
- `grep -rni "full[_-]defen"` across docs + server returns only negation notes.
- F1d, when implemented, has `FateActionPayload.action` = `["overcome","create_advantage","attack","concede"]` and no `full_defense` branch in `dispatch_fate_action`.
- ADR-144 / the spec describe only the four Fate Core actions.

---

## 3. State of the wider F1 slice

| Slice | Scope | Status |
|-------|-------|--------|
| F1a | Resolution primitive + module registration + OTEL | **merged** |
| F1b | Fate character facet + fate-point economy | **merged** (PR #853) |
| F1c | `fate_conflict.py` exchange engine | **in review — PR #857** |
| F1d | Dispatch routing (`FATE_ACTION` → `run_fate_exchange`) | plan exists; **purge full_defense first**, then implement |
| F2/F3/F4 | narrator action classifier + opponent AI / UI / content skill lists | future |

F1d depends on F1c (`seal_fate_commit`, `fate_barrier_closed`, `run_fate_exchange`, `concede_in_conflict`, `FateConflictError`, `FateExchangeResult`). F1d feeds `run_fate_exchange(round_number=snapshot.turn_manager.interaction)` — that param is wired live in F1c (resolved span + watcher payload).

## 4. Working notes
- Repo: `sidequest-server` targets `develop` (gitflow). Orchestrator targets `main`. Run tests directly `uv run pytest -n0` (no testing-runner; no `-n auto`). Scope ruff to changed files.
- The F1b/F1c/F1d plan files were **untracked** in the orchestrator at session start; the full_defense edits to the F1c plan (and the ones still needed for F1d/spec) are local doc edits, not committed.
- Build method that worked well: `superpowers:subagent-driven-development` — fresh implementer per task, spec-review then code-quality-review, fix via the same implementer (SendMessage by agentId), amend per-task commits.
