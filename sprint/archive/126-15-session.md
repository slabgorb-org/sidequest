---
story_id: "126-15"
jira_key: ""
epic: ""
workflow: "trivial"
---
# Story 126-15: [DOCS] Author the Fate DEFEND-barrier ADR and fix the wrong ADR-148/149 citations in 9 server files (149 is SRD content)

## Story Details
- **ID:** 126-15
- **Jira Key:** (none)
- **Workflow:** trivial
- **Stack Parent:** none
- **Branch Strategy:** gitflow (feat/126-15-fate-defend-adr-citations)
- **Repos:** sidequest-server (base: develop)

## Technical Approach

**Task 1: Author a new ADR for the Fate DEFEND barrier**

Create `docs/adr/151-fate-defend-barrier-sealed-commit-loop.md` (or similar slug) documenting the Fate DEFEND barrier mechanic introduced in story 126-8. The ADR should cover:
- The DEFEND barrier as part of the sealed-commit loop (parallel to ADR-036 for standard turns)
- The FATE_DEFEND_REQUEST broadcast and client→server FATE_THROW/FATE_DEFEND_THROW message contract
- Authorization (entry.defender validation, anti-grief protections)
- The pending_defenses ledger and resume-safety (ADR-128)
- Concession handling (story 126-14: conceded signal, no roll_4df on concede path)
- OTEL observability (lie-detector spans: fate.defend_phase, fate.action_resolved for defense rolls)

The new ADR should cite ADR-148 (player Fate rolls are physics-is-the-roll) and ADR-144 (Fate Core binding) as context, but is DISTINCT from both: it documents the DEFEND barrier mechanism, not the roll source or the SRD content tier.

**Task 2: Fix wrong ADR-148/149 citations in 9 server files**

Hunt and replace wrong ADR-148/149 citations in production code:
1. `sidequest/game/encounter.py`
2. `sidequest/game/ruleset/fate_projection.py`
3. `sidequest/game/ruleset/fate_resolution.py`
4. `sidequest/game/ruleset/fate.py`
5. `sidequest/handlers/fate_throw.py`
6. `sidequest/protocol/enums.py`
7. `sidequest/protocol/fate.py`
8. `sidequest/protocol/messages.py`
9. `sidequest/server/dispatch/fate_conflict.py`
10. `sidequest/server/websocket_session_handler.py`
11. `sidequest/telemetry/spans/fate.py` (11 files total, story says "9" but ~11 have citations)

For each file, categorize citations:
- **Cite ADR-148:** Fate-action roll mechanics (physics-is-the-roll, dice source, FATE_THROW/FATE_DEFEND_THROW messages, 4dF determinism)
- **Cite ADR-149:** SRD reference content (rules_document sections, the CCB0 license, SRD prose rendering — very rare in server code, mostly appears in content/ui)
- **Cite the NEW ADR:** DEFEND barrier specifically (pending_defenses ledger, DEFEND-phase sealed commit, authorization guards, concession, OTEL spans on the barrier)

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-19T12:57:54Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-19T12:33:03.292554Z | 2026-06-19T12:35:40Z | 2m 36s |
| implement | 2026-06-19T12:35:40Z | 2026-06-19T12:50:44Z | 15m 4s |
| review | 2026-06-19T12:50:44Z | 2026-06-19T12:57:54Z | 7m 10s |
| finish | 2026-06-19T12:57:54Z | - | - |

## Sm Assessment

Setup complete and clean. This is a 1-pt **trivial** docs story scoped to `sidequest-server` (base: develop), no Jira key (tracked via `pf sprint`), no `depends_on`, merge queue clear.

Two deliverables, both documentation:
1. **Author a new ADR** for the Fate DEFEND barrier (the sealed-commit DEFEND phase introduced in 126-8, FATE_DEFEND_REQUEST/FATE_DEFEND_THROW contract, `pending_defenses` ledger + resume-safety, concession path from 126-14, and the OTEL lie-detector spans on the barrier). It cites ADR-148 and ADR-144 as context but is distinct from both.
2. **Correct miscited ADR references** across ~9–11 server files. The load-bearing fact: **ADR-149 is the SRD reference-content ADR**, so anything citing 148/149 for DEFEND-barrier behavior is wrong. Dev should categorize each citation — 148 (physics-is-the-roll / dice source), 149 (SRD content, rare in server code), or the new DEFEND-barrier ADR — rather than blanket-replace.

Risk: low (no engine behavior changes), but accuracy matters — wrong ADR citations are the exact bug being fixed, so the fix must not introduce new wrong ones. Routing to **Hephaestus (dev)** for the implement phase.

## Delivery Findings

### Dev (implementation)
- **Gap** (non-blocking): Story `repos` is `server` only, but the deliverable spans **two repos** — the ADR is an orchestrator artifact. The orchestrator half (ADR-151, ADR-148/spec cross-ref fixes, regenerated indexes) is already committed and pushed to **orchestrator `main`** (trunk-based), commit `e978ed4`. The server half (9-file citation fixes) is on `feat/126-15-fate-defend-adr-citations` and needs the normal review → PR (base `develop`) → finish. Affects SM finish: it must verify/merge the **server PR** and recognize the orchestrator commit is already on main (no PR needed for trunk-based docs). *Found by Dev during implementation.*
- **Improvement** (non-blocking): For future "author an ADR" stories, set `repos: server, orchestrator` (or document the ADR-on-orchestrator path in the story) so the workflow tracks both landing points up front. Affects `sprint/` story authoring (the repos field). *Found by Dev during implementation.*

### Reviewer (code review)
- Endorse the Dev **Gap** finding: SM finish must treat this as two landing points — merge the **server PR** (feat/126-15 → develop), and recognize the orchestrator half (ADR-151 + cross-ref fixes + indexes) is **already on `main`** (commits `e978ed4`/`f038512`, pushed); no orchestrator PR exists or is needed (trunk-based). *Found by Reviewer during code review.*
- No additional upstream findings. ADR-151 accurately documents the as-built feature (Stories 126-8/126-13/126-14); its security-control description (§7) was verified against live code by the security specialist. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

3 deviations

- **Story scoped `repos: server`, but the ADR is an orchestrator artifact**
  - Rationale: This is genuinely a two-repo story; the YAML repo field captured only the citation-fix half. Committing the ADR to trunk-based orchestrator main is the established pattern for ADRs/docs in this repo.
  - Severity: minor
  - Forward impact: SM finish must account for **two** landing points — the server PR (feat/126-15 → develop) and the already-pushed orchestrator main commit. See Delivery Findings.
- **Fixed two stale "ADR-149" refs outside the literal "9 server files"**
  - Rationale: Authoring ADR-151 makes ADR-148 §6 demonstrably wrong; leaving it would perpetuate the exact bug being fixed (No Silent Fallbacks / accuracy). Both are one-line doc fixes in artifacts ADR-151 cross-references.
  - Severity: minor
  - Forward impact: none — pure documentation accuracy; no code or behavior affected.
- **Replacement was uniformly `ADR-148/149` → `ADR-148/151`, not a per-citation 148-vs-149-vs-151 split**
  - Rationale: The categorization the SM anticipated was performed; it just resolved to a single transform because the SRD-149 case the SM hedged for does not appear in the server.
  - Severity: trivial
  - Forward impact: none.

## Design Deviations

### Dev (implementation)
- **Story scoped `repos: server`, but the ADR is an orchestrator artifact**
  - Spec source: session frontmatter / context-story-126-15.md, "Repo: server"
  - Spec text: "Repos: sidequest-server (base: develop)"
  - Implementation: ADRs live only in the orchestrator (`docs/adr/`); the server has no `docs/adr/`. So ADR-151 + the ADR-148/spec cross-ref fixes + regenerated README/CLAUDE.md indexes were committed to the **orchestrator** (`main`, trunk-based per repos.yaml — same path ADR-150 took as `docs(126-12)`), commit `e978ed4`. Only the 9-file citation fixes are on the server `feat/126-15` branch.
  - Rationale: This is genuinely a two-repo story; the YAML repo field captured only the citation-fix half. Committing the ADR to trunk-based orchestrator main is the established pattern for ADRs/docs in this repo.
  - Severity: minor
  - Forward impact: SM finish must account for **two** landing points — the server PR (feat/126-15 → develop) and the already-pushed orchestrator main commit. See Delivery Findings.
- **Fixed two stale "ADR-149" refs outside the literal "9 server files"**
  - Spec source: story title
  - Spec text: "fix the wrong ADR-148/149 citations in 9 server files"
  - Implementation: Also corrected ADR-148 §6's canonical forward-reference ("Story 126-8 / ADR-149" → "…/ADR-151") and the 2026-06-17 design spec's two companion-ADR references, since both pointed at the now-stale 149 reservation that this story resolves.
  - Rationale: Authoring ADR-151 makes ADR-148 §6 demonstrably wrong; leaving it would perpetuate the exact bug being fixed (No Silent Fallbacks / accuracy). Both are one-line doc fixes in artifacts ADR-151 cross-references.
  - Severity: minor
  - Forward impact: none — pure documentation accuracy; no code or behavior affected.
- **Replacement was uniformly `ADR-148/149` → `ADR-148/151`, not a per-citation 148-vs-149-vs-151 split**
  - Spec source: SM Assessment, deliverable 2
  - Spec text: "categorize each citation — 148 (physics-is-the-roll / dice source), 149 (SRD content, rare in server code), or the new DEFEND-barrier ADR — rather than blanket-replace"
  - Implementation: Categorization found **zero** standalone `ADR-149` (SRD) citations in server code — every occurrence of 149 was the `ADR-148/149` DEFEND-barrier pairing where 148 (roll source) is correct and only 149 is wrong. So the categorized fix is uniform: 148 stays, 149→151. Pure `ADR-148` citations (e.g. in `fate_projection.py`, `fate_resolution.py`) were left untouched.
  - Rationale: The categorization the SM anticipated was performed; it just resolved to a single transform because the SRD-149 case the SM hedged for does not appear in the server.
  - Severity: trivial
  - Forward impact: none.

### Reviewer (audit)
- **Story scoped `repos: server`, but the ADR is an orchestrator artifact** → ✓ ACCEPTED by Reviewer: Sound and unavoidable. ADRs live only in `docs/adr/` (orchestrator); the server has no `docs/adr/` (verified). Committing the ADR direct to trunk-based orchestrator `main` matches the established pattern (ADR-150 landed as `docs(126-12)` direct to main; repos.yaml `orchestrator.branch_strategy: trunk-based`). The two-repo reality is correctly surfaced as a Delivery Finding for SM finish. No safer alternative exists given where ADRs must live.
- **Fixed two stale "ADR-149" refs outside the literal "9 server files"** → ✓ ACCEPTED by Reviewer: Correct completion, not scope creep. Authoring ADR-151 makes ADR-148 §6's "Story 126-8 / ADR-149" forward-ref demonstrably wrong; leaving it would re-seed the exact bug. Both are one-line doc-accuracy fixes in artifacts ADR-151 cross-references. Pure documentation, zero behavior impact.
- **Replacement was uniformly `ADR-148/149` → `ADR-148/151`** → ✓ ACCEPTED by Reviewer: Independently verified. `grep -rn 'ADR-149'` over `sidequest/**/*.py` returns **zero** standalone SRD-149 citations — every `149` was the `148/149` DEFEND-barrier pairing where 148 (roll source) is genuinely correct. The categorized fix correctly resolves to a single transform; pure `(ADR-148)` citations (e.g. `fate_conflict.py:218`, `fate.py:30`) were correctly left untouched (confirmed in diff and by edge-hunter).

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**

_Orchestrator (`main`, trunk-based — commit `e978ed4`, pushed):_
- `docs/adr/151-fate-defend-followup-barrier.md` (NEW) — the DEFEND-barrier ADR. Documents the four-phase round (COMMIT → REVEAL → DEFEND → RESOLVE), the conditional block-and-wait DEFEND barrier, `FATE_DEFEND_REQUEST` + `FATE_THROW(action=defend)`, the resume-safe `pending_defenses` ledger (NPC dice locked at REVEAL), physics-is-the-roll player defense via `resolve_action_from_faces`, per-attack player-picks-skill defense + invokes, defender authorization (the 126-8 HIGH fix / ADR-119 lineage, 126-13 OTEL rejection), concession (126-14), and OTEL `role`/`fate.defend_phase`. Includes an explicit "numbering note" explaining the 149→151 reservation history. Status `accepted`, `implementation-status: live`.
- `docs/adr/148-player-fate-roll-is-physics-is-the-roll.md` — §6 forward-ref corrected (`Story 126-8 / ADR-149` → `…/ADR-151`, with a one-line history note).
- `docs/superpowers/specs/2026-06-17-fate-determinative-rolls-design.md` — two stale companion-ADR `149` refs → `151`.
- `docs/adr/README.md`, `CLAUDE.md` — regenerated ADR indexes (`scripts/regenerate_adr_indexes.py`; 151 ADRs loaded, no unknown-tag warnings).
- `sprint/context/context-story-126-15.md` — story context (from setup).

_Server (`feat/126-15-fate-defend-adr-citations`, base `develop` — commit `47831738`, pushed):_
- 9 files, **comments/docstrings only, zero logic change** — `ADR-148/149` → `ADR-148/151` (25 insertions / 25 deletions, symmetric): `server/websocket_session_handler.py`, `server/dispatch/fate_conflict.py`, `protocol/{enums,fate,messages}.py`, `game/encounter.py`, `game/ruleset/fate.py`, `telemetry/spans/fate.py`, `handlers/fate_throw.py`. Two line-wrapped citations handled. `pf_compile` clean on all 9.

**Tests:** N/A — trivial docs story (no TEA RED phase). Verification: ADR frontmatter passed the staged-commit schema-validation hook (2 ADRs, 0 errors); `python3 -m py_compile` green on all 9 server files; `grep` confirms **zero** remaining `ADR-148/149` and zero stray `149` in the touched files; the index regenerator ran clean.

**Branch:** `feat/126-15-fate-defend-adr-citations` (server, pushed) + orchestrator `main` (pushed, `e978ed4`).

**Handoff:** To review (Hermes Psychopompos). Reviewer reviews the server citation-fix branch and can read ADR-151 on `main`. **Note the two-repo split** (see Delivery Findings) — the ADR is already on trunk-based orchestrator main; only the server branch needs a PR at finish.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (GREEN; py_compile PASS ×9, zero `148/149` remain, index regen clean) | N/A |
| 2 | reviewer-edge-hunter | Yes | findings | 1 (truncated diff-file input, not a code defect) | confirmed 0, dismissed 1 (addressed), deferred 0 |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | Yes | clean | none (no secrets/leakage; auth-control description verified accurate vs live code) | N/A |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings |

**All received:** Yes (3 enabled returned: preflight, edge-hunter, security; 6 disabled via `workflow.reviewer_subagents` pre-filled as Skipped)
**Total findings:** 0 confirmed, 1 dismissed (with rationale), 0 deferred

**Dismissed finding (with rationale):** [EDGE] "orchestrator diff section truncated in /tmp/126-15-review-diff.txt" — dismissed: this is an artifact of the Reviewer's own diff-capture command (it ran `git show` of orchestrator commits while `cd`'d into the server repo, which lacks those revisions), **not** a defect in Dev's work. The diff file was regenerated correctly (635 lines, orchestrator content present), and the orchestrator deliverables (ADR-151, ADR-148 §6 fix, spec fixes, indexes) were verified directly by the Reviewer (symbols/cross-refs/frontmatter all real — see Rule Compliance & Observations). Edge-hunter's server-side review independently confirmed all 20 replacements + both wrapped cases correct.

## Reviewer Assessment

**Verdict:** APPROVED

A clean, surgical, accurate docs story. The server change is comment/docstring-only with zero logic touched; the new ADR-151 honestly documents an already-built, already-merged mechanism (Stories 126-8/126-13/126-14) and every claim it makes was verified against live code. No Critical/High/Medium/Low defects found.

**Data flow traced:** N/A for runtime data — this is documentation. Instead I traced the *citation* data flow: the wrong token `ADR-149` (SRD reference content, ADR-149) → its origin (ADR-148 §6 reserved "ADR-149" for the DEFEND barrier before that number was reallocated) → its correction (a new ADR-151 authored as the barrier's real home; all `ADR-148/149` DEFEND-barrier citations rewritten to `ADR-148/151`, 148 retained as the roll-source ADR). Every link verified.

**Pattern observed:** Surgical, intent-preserving citation correction — `fate_conflict.py:218` keeps standalone `(ADR-148)` (roll source) while the DEFEND-barrier docstring above it moves to `148/151`. The author distinguished "roll source" (148) from "barrier" (151) per-citation rather than blanket-replacing. Good pattern.

**Error handling:** N/A (no executable change). The ADR's *description* of error/auth handling (§6 block-and-wait No-Silent-Fallbacks; §7 loud `FateConflictError` on `entry.defender != actor`) was verified to match the live implementation.

### Dispatch-tagged findings (all 8 lanes accounted for)
- `[EDGE]` — edge-hunter: server side **clean** (20/20 replacements + both wrapped continuations correct, no adjacent text altered, standalone 148 untouched). Its sole finding was the Reviewer's truncated diff-file input — dismissed/addressed (see Subagent Results).
- `[SEC]` — security: **clean**. No secrets/credentials/hostnames in the diff. The `request_id` format disclosed in ADR-151 §7 is already broadcast to all seated clients per protocol design — documenting it in service of the auth control is not new attack surface. SRD non-endorsement (ADR-149 §5) N/A — ADR-151 is engine-design prose, no publisher names, no endorsement implied. **Bonus:** security independently verified ADR-151 §7 matches live code (`entry.defender != actor` @ `fate_conflict.py:1197`; `request_id` format @ `:384`; OTEL rejection emit @ `:1204-1218`, Story 126-13).
- `[DOC]` — comment-analyzer **disabled**; Reviewer covered this lane directly: the change IS documentation, and it is accurate — all `148/151` citations sit in genuine DEFEND-barrier contexts; ADR-151's every referenced symbol exists; no stale/misleading text introduced.
- `[SILENT]` — silent-failure-hunter **disabled**; N/A: comment/prose-only diff has no error-handling code to swallow. (ADR-151 *documents* the No-Silent-Fallbacks block-and-wait posture, consistent with code.)
- `[TEST]` — test-analyzer **disabled**; N/A: trivial workflow, no tests in scope; no test files changed.
- `[TYPE]` — type-design **disabled**; N/A: no type/signature changes (docstrings only; `FateThrowPayload` etc. unchanged).
- `[SIMPLE]` — simplifier **disabled**; Reviewer judgment: the change is already minimal (149→151 only); no complexity introduced. ADR-151 is appropriately scoped (documents existing behavior, ships no code).
- `[RULE]` — rule-checker **disabled**; Reviewer covered exhaustively in Rule Compliance below.

### Rule Compliance
Applicable rules are project doctrine (SOUL.md / CLAUDE.md / ADR conventions) — no `.claude/rules/*.md` exist. Enumerated against every changed artifact:
- **No Stubbing / No Silent Fallbacks (CLAUDE.md):** ADR-151 documents a real, shipped mechanism (not a stub); §6 explicitly encodes block-and-wait with "No Silent Fallbacks: no auto-roll." Server changes add nothing executable. ✓ compliant (all 10 changed files).
- **OTEL Observability Principle (CLAUDE.md):** ADR-151 §9 documents the `fate.defend_phase` + `role`-tagged `fate.action_resolved` lie-detector spans; these exist (`telemetry/spans/fate.py`, verified). The ADR strengthens observability documentation. ✓.
- **Bind the Ruleset, Don't Balance It (SOUL.md):** ADR-151 §4 explicitly states the Fate ladder math is untouched — only the dice *source* changes. Consistent with doctrine; no balancing introduced. ✓.
- **ADR frontmatter schema (ADR-088):** ADR-151 carries all required keys (id/title/status/date/deciders/supersedes/superseded-by/related/tags/implementation-status/implementation-pointer); primary tag `game-systems` is a valid `TAG_SECTIONS` key; the staged-commit schema-validation hook passed (2 ADRs, 0 errors); regenerate script loaded 151 ADRs with no unknown-tag WARN. ✓.
- **No false `[VERIFIED]` (Reviewer rule):** every VERIFIED below cites a line and a rule check.

### Observations (≥5)
1. `[VERIFIED]` All 25 server citation changes are contextually-correct DEFEND-barrier references — traced every hunk in the diff; each `148/149→148/151` sits in Story-126-8/126-14 DEFEND prose. Evidence: `/tmp/126-15-review-diff.txt` lines 6–262. Complies with the story's "categorize, don't blanket-replace" intent.
2. `[VERIFIED]` Zero logic/behavior changed — every `+`/`-` line is a comment or docstring; `python3 -m py_compile` PASS on all 9 (preflight). Evidence: diff is 25/25 symmetric, all within `"""`/`#`.
3. `[VERIFIED]` No standalone `ADR-149` (SRD) citation was clobbered — `grep -rn 'ADR-149' --include='*.py' sidequest/` returns zero outside the `148/149` pairing. Evidence: adversarial check + edge-hunter "standalone ADR-148 correctly left untouched."
4. `[VERIFIED]` No `148/149` missed — `grep -rn '148/149'` post-change returns NONE (preflight `grep_148_149: PASS`).
5. `[VERIFIED]` ADR-151 describes **real** symbols (no "winging it") — `FatePendingDefense` (`encounter.py:188`), `dispatch_fate_defense` (`fate_conflict.py:1160`), `resume_fate_exchange` (`:539`), `_build_pending_defenses` (`:359`), `resolve_action_from_faces` (`fate.py:239`), `FATE_DEFEND_REQUEST` (`enums.py:161`), `fate.defend_phase` + `entry.defender` + `roll_4df` all exist at cited locations.
6. `[VERIFIED]` Both line-wrapped citations fixed on both halves — `encounter.py:189-190` and `fate_conflict.py:366-367` keep `(ADR-148/` and update the `149,`→`151,` continuation (edge-hunter + diff lines 9-11, 150-152).
7. `[VERIFIED]` Index regeneration correct & current — ADR-151 present in `README.md` and the `CLAUDE.md` Game-Systems block; re-running `regenerate_adr_indexes.py` produces a 0-line diff (preflight `adr_index_regen: PASS`). All 7 `related` ADRs (36/74/119/128/129/144/148) exist.
8. `[VERIFIED]` ADR-151's auth-control description is neither over- nor under-stated vs live code (security specialist, three line-level matches).

### Devil's Advocate
Let me argue this is broken. *Claim 1: the ADR fabricates mechanism — Claude winging a plausible design.* Refuted: I ran the lie-detector over every named symbol; all eleven exist at the cited files/lines, and the security specialist independently matched §7's auth check, request_id format, and OTEL emit to specific source lines. The ADR is a faithful record of merged code, not invention. *Claim 2: a citation was changed that should have stayed 149 (a real SRD reference), silently corrupting an SRD pointer.* Refuted: an exhaustive `grep` proves there is **no** standalone `ADR-149` anywhere in `sidequest/**/*.py` — 149 appears only as the `148/149` DEFEND-barrier pairing, so there was no SRD citation to corrupt. *Claim 3: a wrapped citation got half-fixed, leaving `ADR-148/` pointing at a dangling line that still reads `149`.* Refuted: both wrapped cases were inspected line-by-line (continuations now read `151,`), and a post-change `grep '148/149'` returns empty. *Claim 4: the two-repo split means the ADR is orphaned / the story can't finish cleanly.* Partially conceded as a process risk, but mitigated: the orchestrator commit is already on `main` (trunk-based, the normal ADR path), and both Dev and Reviewer flagged it explicitly for SM finish so the server PR is merged and the orchestrator commit recognized — nothing is lost. *Claim 5: a confused reader follows ADR-148 §6 to "ADR-149" and lands on SRD content.* Refuted: that exact forward-ref was corrected to ADR-151 with a one-line history note, and the design spec's two stale refs likewise. *Claim 6: regenerated indexes drifted or dropped an ADR.* Refuted: the regenerator loaded all 151 with no unknown-tag warning and a re-run yields a 0-line diff. The devil finds no purchase here — the work is correct and complete.

**Handoff:** To SM (Themis the Just) for finish-story. **Two landing points** — merge the server PR (feat/126-15 → develop); the orchestrator ADR commit is already on `main` (trunk-based, no PR).