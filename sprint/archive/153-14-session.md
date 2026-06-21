---
story_id: "153-14"
jira_key: ""
epic: "153"
workflow: "trivial"
---
# Story 153-14: [NPC-NAME-PCSUBSTRING-SUBSTITUTION] word-boundary-guard the PC-name to you substitution

## Story Details
- **ID:** 153-14
- **Jira Key:** (none — Jira integration disabled)
- **Workflow:** trivial
- **Stack Parent:** none
- **Branch:** feat/153-14-word-boundary-pc-name-sub
- **Branch Strategy:** gitflow (sidequest-server uses develop)

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-21T13:57:18Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-21T13:22:57Z | 2026-06-21T13:24:43Z | 1m 46s |
| implement | 2026-06-21T13:24:43Z | 2026-06-21T13:42:39Z | 17m 56s |
| review | 2026-06-21T13:42:39Z | 2026-06-21T13:57:18Z | 14m 39s |
| finish | 2026-06-21T13:57:18Z | - | - |

## Delivery Findings

No upstream findings.

### Dev (implementation)
- No upstream findings.

### Reviewer (code review)
- **Improvement** (non-blocking): Red `develop` test baseline — 42 deterministic, pre-existing failures unrelated to this change (e.g. stale `monkeypatch` on removed `sidequest.agents.llm_factory.build_async_anthropic` in `tests/server/test_app.py`; chargen/pregen/lore/scenario/pack-load integration drift across ~20 test files). Affects `develop` broadly (not `pov_swap`); needs a dedicated cleanup story so the suite gate is trustworthy again. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `_is_proper_noun_fragment` preceding-word check uses `re.search(r"(\w+)\s+$", text[:name_start])`. Empirically linear (1.5ms @ 20k chars) and safe (disjoint classes, bounded sentence input), but a right-anchored rewrite — `prefix.rstrip()` then `re.search(r"(\w+)$", ...)` — removes the theoretical `\w+`/`\s+` backtracking entirely and reads cleaner. Affects `sidequest/agents/pov_swap.py:252`. *Found by Reviewer during code review.*
- **Gap** (non-blocking): The 5 new tests are he/him only. The suite's established discipline adds pronoun-parity (she/her, they/them) tests for every new pass; the fragment guard is provably pronoun-agnostic so this is low-risk, but a parity test plus an infix case ("Lord Kantos Vah") and a pin for the documented sentence-initial-suffix limitation ("Vah Kantos …" left to swap) would lock the behavior. Affects `tests/agents/test_pov_swap.py`. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

## Design Deviations

None at setup.

### Dev (implementation)
- No deviations from spec. All three ACs implemented directly: standalone PC name still swaps, PC-name-as-fragment-of-NPC-name left intact, possessive still matches, regression tests added. The AC phrase "embedded in a longer NPC name" was implemented in full generality (prefix/infix via the following-capital signal, suffix via preceding-capital-not-sentence-start), not just the prefix example — this is completing the stated AC, not scope creep.

### Reviewer (audit)
- **Dev: "embedded in a longer NPC name" implemented in full generality (prefix/infix/suffix), not just the prefix example** → ✓ ACCEPTED by Reviewer: sound. The AC text is "embedded," the parenthetical "Kantos Vah" is just the documented exemplar; covering infix/suffix via the same adjacency helper is completing the AC, not scope creep. The suffix arm is correctly bounded by the sentence-start exclusion so it doesn't suppress legitimate sentence-initial subjects. No undocumented deviations found.

## Sm Assessment

**Story:** Word-boundary-guard the PC-name→"you" POV substitution so it never fires on a substring of a longer NPC name.

**Origin:** `NPC-NAME-PCSUBSTRING-SUBSTITUTION`, a low-severity finding from the 2026-06-20/21 full-stack /sq-playtest sweep (archived in `sprint/archive/150-13-session.md`). Symptom: `"Kantos Vah"` rendered as `"you Vah"` because the PC name "Kantos" is a prefix of the NPC name "Kantos Vah", and the substitution used a naive (non-word-bounded) replace.

**Technical approach (for Dev):**
- Fix lives in `sidequest/agents/pov_swap.py` — the pass that replaces the PC name with "you". Same module/family as the 71-6 NPC-name-after-connector word-boundary guard.
- Reuse the established codebase idiom `re.search(rf"\b{re.escape(name)}\b", ...)` (also in `agents/npc_context.py` and `server/visibility_classifier.py::_find_pc_in_text`) rather than a fresh matcher or substring replace.
- Possessives ("Kantos's") must still match per the 75-10 word-boundary convention — verify the chosen boundary handling preserves that.

**Acceptance criteria:**
- Standalone PC-name references still swap to "you".
- PC name embedded in a longer NPC name (PC "Kantos" / NPC "Kantos Vah") is left intact.
- Regression test added in `tests/agents/test_pov_swap.py` covering the prefix-collision case, plus a possessive case to lock in existing behavior.

**Routing:** Trivial (phased) workflow → next phase `implement` → Dev (Naomi). 1 point, single-repo (server). No Jira (YAML-only sprint).
## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | tests YELLOW (42 pre-existing failures unrelated to diff), lint/format pre-existing on develop, pyright GREEN, 0 code smells | confirmed 1 (red develop baseline — out of scope), dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings (self-assessed — see Observations [EDGE]) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings (self-assessed — see Observations [SILENT]) |
| 4 | reviewer-test-analyzer | Yes | findings | 7 (1 high→downgraded, 4 medium, 2 low) | confirmed 4 (non-blocking test additions), dismissed 1 (count-assert: over-fire already caught), downgraded 1 (wiring), deferred 1 |
| 5 | reviewer-comment-analyzer | Yes | findings | 1 (low) | confirmed 1 as VERIFIED-correct; dismissed the suggested `[A-Z]` fix (would regress Unicode names) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings (self-assessed — see Observations [TYPE]) |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings (self-assessed — see [SEC]/[RULE] ReDoS) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings (self-assessed — see Observations [SIMPLE]) |
| 9 | reviewer-rule-checker | Yes | findings | 1 (ReDoS, self-rated low) | confirmed 1 as LOW non-blocking (empirically 1.5ms @ 20k chars, disjoint classes) |

**All received:** Yes (4 enabled returned + assessed; 5 disabled pre-filled as Skipped)
**Total findings:** 4 confirmed (all non-blocking), 2 dismissed (with rationale), 1 downgraded HIGH→LOW, 1 confirmed-out-of-scope (red develop baseline)

## Rule Compliance

Enumerated every changed symbol against the Python lang-review checklist (13 checks) + CLAUDE.md/SOUL.md rules:

- **#1 Silent exceptions** — `_is_proper_noun_fragment`: no try/except; both Pass 2/3 guards return `m.group(0)` (correct re.sub no-op, not a swallow). COMPLIANT.
- **#2 Mutable defaults** — signature `(text: str, name_start: int, name_end: int)`: all immutable. COMPLIANT.
- **#3 Type annotations** — all params + `-> bool` annotated; no `Any`, no `type: ignore`. COMPLIANT.
- **#4 Logging** — pure predicate, no error paths; existing `narration.second_person_swap` OTEL span already covers the layer. COMPLIANT (OTEL: cosmetic-prose carve-out applies).
- **#5 Path handling** — no file I/O. N/A.
- **#6 Test quality** — 5 new tests, each asserts exact equality + count or specific substrings; none vacuous; no skips/mocks. COMPLIANT (coverage-addition findings noted below, non-blocking).
- **#7 Resource leaks** — no resources acquired. N/A.
- **#8 Unsafe deserialization** — none. N/A.
- **#9 Async** — synchronous helper + sync callers. N/A.
- **#10 Import hygiene** — no new imports; uses existing `re`; forward-ref to `_is_sentence_start_in` safe under `from __future__ import annotations`. COMPLIANT.
- **#11 Input validation / ReDoS** — both new regexes are CONSTANT (not user-built); `\w`/`\s` disjoint classes ⇒ no catastrophic backtracking; input is a single bounded sentence prefix. `(\w+)\s+$` is a polynomial-worst-case-but-empirically-linear pattern (1.5ms @ 20k chars). LOW non-blocking hardening opportunity (see delivery findings). COMPLIANT-with-note.
- **#12 Dependency hygiene** — no dep changes. N/A.
- **#13 Fix-introduced regressions** — re-scanned: guards return correct no-op; Pass 1 (possessive) intentionally unguarded and safe by construction (`\bKantos's\b` cannot match `Kantos Vah's`). COMPLIANT.
- **CLAUDE.md "Every Test Suite Needs a Wiring Test"** — `swap_to_second_person` is imported and called at `emitters.py:290` (`_apply_pov_swap`, pc_anchored path) and that path is integration-tested by `tests/server/test_merged_mp_emitter_projection.py` (drives `anchor_pc`/`pov_strategy=pc_anchored` and asserts the swap). The new helper is private-internal to that already-wired-and-integration-tested function. SATISFIED at suite level.
- **CLAUDE.md "No Silent Fallbacks"** — guard fails toward NOT swapping a fragment (correct), and the existing emitter path fails loud / returns canonical prose on missing pronouns (unchanged). COMPLIANT.

## Observations

1. **[VERIFIED] Pass 2/3 offset arithmetic is correct** — Pass 2 `name_end = m.start() + len(target_name)` (regex `\b{name}\b\s+(\w+)` matches name+verb, so `m.end()` would overshoot); Pass 3 uses `m.end()` (regex matches only the name). Both pass `[name_start, name_end)` bounding exactly the name token. Evidence: `pov_swap.py:389,422` + the 5 tests pass deterministically.
2. **[VERIFIED] Possessive Pass 1 correctly untouched** — `\b{name}'s\b` = `\bKantos's\b` cannot match `Kantos Vah's` (no apostrophe directly after "Kantos"), so the NPC possessive is intact and the PC's own `Kantos's`→`Your` still fires. Evidence: `test_pc_name_prefix_npc_possessive_left_intact` + `test_pc_possessive_still_swaps_with_collision_name` both pass.
3. **[EDGE] (self, edge-hunter disabled) boundary conditions VERIFIED** — single-word sentence ("Kantos"), name preceded by punctuation `(`/`—` (prefix doesn't end in `\s` → `before` is None), multi-word target ("Zanzibar Jones" barsoom test), intra-word substring ("Al" vs "Alice", handled by pre-existing `\b`). All behave correctly; `before.group(1)[0]` is safe (`\w+` ≥1 char).
4. **[SILENT] (self, silent-failure-hunter disabled) no swallowed errors** — the guard's only control-flow effect is returning the original match unchanged; no except, no suppress, no silent fallback. VERIFIED `pov_swap.py:249-255`.
5. **[TYPE] (self, type-design disabled) clean types** — `(str, int, int) -> bool`, no stringly-typed surface, no casts. VERIFIED.
6. **[SIMPLE] (self, simplifier disabled) appropriately minimal** — two-arm adjacency check is the minimum needed for the "embedded" AC; not over-engineered. The ReDoS-hardening rewrite (rstrip + right-anchor) would also marginally simplify — noted as non-blocking.
7. **[DOC] docstring "capitalized following token" vs `\w`** — comment-analyzer flagged (low). VERIFIED the docstring is behaviorally accurate: `.isupper()` is Unicode-aware, so `\w` + `.isupper()` fires only on uppercase letters (any script) and is intentionally broader than `[A-Z]` — the suggested tightening would REGRESS accented NPC names ("Évrard Vah"). Dismissed the fix; optional one-line doc clarification is non-blocking.
8. **[TEST] coverage additions (non-blocking)** — test-analyzer's pronoun-parity (she/her, they/them), infix ("Lord Kantos Vah"), and documented-limitation pinning (sentence-initial trailing suffix) are valid per the suite's parity discipline, but the guard is provably pronoun-agnostic (inspects char positions, runs before pronoun dispatch). Captured as a delivery finding.
9. **[SEC]/[RULE] ReDoS on `(\w+)\s+$`** — rule-checker (high confidence the pattern exists, self-rated low severity). Confirmed LOW: constant pattern (not user-built), disjoint `\w`/`\s` ⇒ no catastrophic backtracking, sentence-bounded input; empirically 1.5ms at 20,002 chars (66× any real sentence), scaling linearly. Non-blocking hardening opportunity captured as delivery finding.
10. **[PREFLIGHT] red develop baseline (out of scope)** — 42 deterministic test failures reproduce on this branch but are pre-existing on develop (e.g. stale `monkeypatch` on removed `llm_factory.build_async_anthropic`; chargen/pregen/lore/scenario/pack-load integration drift). NONE reference `pov_swap`; a pure-string-helper imported only by `emitters.py` has no causal path to them. The three affected modules run **73 passed / 4 skipped / 0 failed** deterministically. Flagged to SM as a project-health delivery finding.

## Devil's Advocate

Let me argue this code is broken. First attack: the guard over-fires and silently swallows a legitimate PC swap, leaving the player reading their own actions in the third person — the exact El Dorado failure SOUL warns against. Concretely, if the narrator opens a sentence with the PC name followed by a capitalized word that is *not* a surname — "Kantos Tycho-bound, sprints for the lock" — the following-capital arm fires and the PC's own action never swaps to "you". Is this real? The narrator's pov_rules contract writes PC actions with the bare stored name immediately followed by a lowercase verb; a capitalized token directly abutting the name (no verb between) is, in practice, always a name continuation. So the failure requires the narrator to violate its own prose contract. Low-probability, and the docstring explicitly accepts the ambiguity. Not a blocker, but it is an unpinned behavior — captured as a coverage finding.

Second attack: a malicious or chaotic player names their PC something that is a prefix of a common word, e.g. PC "The" or "A" or "I". Then `\bThe\b\s+(\w+)` could match "The Envoy" everywhere and the guard's following-capital arm would suppress swaps wholesale — but that is a pre-existing property of the name-swap passes (matching "The"), not introduced here, and the new guard only *reduces* swaps, never adds a wrong one. So the change is strictly safer than before.

Third attack: performance. Could a hostile run-on narration string blow up `(\w+)\s+$`? I empirically drove 20,002 characters through it: 1.5ms, linear. Disjoint character classes preclude the exponential backtracking that defines a real ReDoS; the worst case is bounded by max-word-length (tiny). Not exploitable.

Fourth attack: does the fix break the emitter path or change the signature consumers rely on? No — `swap_to_second_person`'s signature is unchanged; the helper is private. The integration test for the pc_anchored emitter path passes. Fifth attack: the 42 failing tests — is the reviewer being lied to about "pre-existing"? I reproduced them deterministically, read a representative stack (stale monkeypatch on a renamed symbol), and confirmed none import pov_swap. The change is clean; the baseline is the project's problem, not this story's. Conclusion: no Critical or High in the diff. The attacks surface only non-blocking coverage gaps and a pre-existing red baseline.

## Reviewer Assessment

**Verdict:** APPROVED

**Summary:** A correct, tightly-scoped fix for NPC-NAME-PCSUBSTRING-SUBSTITUTION. The `\b...\b` name boundaries were necessary-but-insufficient (a multi-word NPC name carries an internal boundary), so `_is_proper_noun_fragment` adds an adjacency guard — a name token next to another capitalized word is a fragment of a longer proper noun and is left unswapped. Wired into Pass 2/3; possessive Pass 1 correctly untouched. Implements the AC's "embedded in a longer NPC name" in full generality (prefix/infix via following-capital, suffix via preceding-capital-not-sentence-start).

**Dispatch coverage (all tags):**
- `[EDGE]` — (subagent disabled) self-assessed: boundary conditions VERIFIED (Observation 3).
- `[SILENT]` — (subagent disabled) self-assessed: no swallowed errors; guard returns correct no-op (Observation 4).
- `[TEST]` — non-blocking coverage additions (pronoun parity, infix, limitation-pinning); one dismissed (count-assert — over/under-fire already caught by `test_pc_name_standalone_still_swaps_despite_collision_name`'s `"You draw the blade." in out`). (Observation 8.)
- `[DOC]` — docstring VERIFIED accurate; suggested `[A-Z]` tightening dismissed (would regress Unicode names). (Observation 7.)
- `[TYPE]` — (subagent disabled) self-assessed: fully annotated, no stringly-typed surface (Observation 5).
- `[SEC]` — ReDoS confirmed LOW/non-blocking (constant pattern, disjoint classes, 1.5ms @ 20k). (Observation 9.)
- `[SIMPLE]` — (subagent disabled) self-assessed: appropriately minimal, no over-engineering (Observation 6).
- `[RULE]` — rule-checker: 13/13 checks pass except the ReDoS note (LOW). Wiring rule satisfied at suite level. (Rule Compliance.)

**Data flow traced:** narrator prose `text` → `emitters._apply_pov_swap` (pc_anchored, recipient==anchor) → `swap_to_second_person(target_name=anchor_pc)` → per-sentence `_rewrite_sentence` → Pass 2/3 now gated by `_is_proper_noun_fragment` → swapped prose in the recipient's payload. Safe: signature unchanged, guard only suppresses wrong swaps.

**Pattern observed:** adjacency-based proper-noun-fragment detection at `pov_swap.py:222-255`; reuses the file's `_is_sentence_start_in` for the suffix-disambiguation, consistent with the module's existing pass idioms.

**Error handling:** pure predicate, no failure modes; `before.group(1)[0]` safe (`\w+`≥1 char); fails toward not-swapping (correct, no silent fallback).

**Tests:** affected modules 73 passed / 4 skipped / 0 failed deterministically (`-p no:randomly`). 42 unrelated pre-existing develop failures flagged to SM, not caused by this change.

**Handoff:** To SM (Camina Drummer) for finish-story.