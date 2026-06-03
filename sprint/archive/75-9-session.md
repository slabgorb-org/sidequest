---
story_id: "75-9"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 75-9: [DESIGN] NPC-pool ratification gate + pool/Npc split (ADR-135) — governs ADR-118 projection source

## Story Details
- **ID:** 75-9
- **Jira Key:** (none — personal project)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-03T18:28:18Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-03T17:59:05Z | 2026-06-03T18:03:37Z | 4m 32s |
| red | 2026-06-03T18:03:37Z | 2026-06-03T18:05:49Z | 2m 12s |
| green | 2026-06-03T18:05:49Z | 2026-06-03T18:16:52Z | 11m 3s |
| spec-check | 2026-06-03T18:16:52Z | 2026-06-03T18:18:41Z | 1m 49s |
| verify | 2026-06-03T18:18:41Z | 2026-06-03T18:20:30Z | 1m 49s |
| review | 2026-06-03T18:20:30Z | 2026-06-03T18:26:52Z | 6m 22s |
| spec-reconcile | 2026-06-03T18:26:52Z | 2026-06-03T18:28:18Z | 1m 26s |
| finish | 2026-06-03T18:28:18Z | - | - |

## Sm Assessment

**Setup complete — handing off RED to Igor (TEA).**

Story 75-9 is a **design-only** story (sibling to 75-3, which delivered the
ADR-118 design). The deliverable is a written design of record governing which
NPCs are eligible to be projected into the live ADR-118 retrieval index, plus the
follow-on implementation stories it spawns. No production engine code lands here
unless a small, testable predicate seam (`is_projectable(member) -> bool`) proves
warranted — and if so, it arrives with a unit test + wiring assertion.

**Reuse-first is the headline.** The pool/`Npc` split and the ratification gate
*already exist and are live* — `NpcPoolMember.observation_pending` (Story 49-6,
`npc_pool.py:58`), `_auto_mint_prose_only_npcs`, and the ADR-118 entity_card /
entity_store / entity_sync machinery. This story *governs and reconciles* those
structures; it does not rebuild them. Architect/TEA should resist any greenfield
framing.

**Open design question for the design phase (logged in Delivery Findings):**
the "(ADR-135)" in the title is a cross-reference, not the ADR this story emits —
latest ADR is 137, and the title's own clause points at ADR-118 as the governed
surface. Decide: new ADR-138 vs. a design spec amending ADR-118 §D3.

Context document: `sprint/context/context-story-75-9.md` (validated). Branch
`feat/75-9-npc-pool-ratification-gate` created in sidequest-server off develop.

## TEA Assessment

**Tests Required:** No
**Reason:** Design-only story — chore bypass under the documentation criterion.
The deliverable is a written design of record (ADR and/or design spec in `docs/`)
governing which NPCs are eligible for the ADR-118 projection source. There is no
production code committed to in this story, so there is no behaviour to drive
red→green. The context's AC1–AC4 are artifact-completeness review gates, not
executable assertions. This mirrors the sibling design-only story 75-3 (the
ADR-118 design itself), which shipped zero code.

**Paranoid Igor's tripwire (the line where tests WOULD be mandatory):**
If, during GREEN, the design concludes that a *code* seam should land **in this
story** — e.g. a pure `is_projectable(member) -> bool` predicate, or any
gate→projection-index wiring — that is a scope expansion from design-only to
design+code. It must NOT be merged on this branch without bouncing back to RED for:
1. a failing unit test on the predicate's truth table (ratified → projectable;
   `observation_pending=True` → not projectable; purged → evicted), and
2. a wiring/OTEL assertion proving the predicate is reachable from the live
   `to_card()` / retrieval path — never a source-text grep (repo "No Source-Text
   Wiring Tests" doctrine; prefer an OTEL span or fixture-driven behaviour test).
Per the context's own scope boundary, the safer outcome is to *defer* any such
code to a named follow-on implementation story and keep 75-9 design-only.

**Rule Coverage:** N/A — the Python lang-review checklist applies to code, and
this story produces a documentation artifact. The checklist becomes binding on any
follow-on implementation story the design spawns.

**Self-check:** No vacuous tests written (none written at all — bypass). No
pre-existing vacuous tests touched.

**Status:** RED bypassed (design-only). Ready for Dev.
**Handoff:** To Ponder Stibbons (Dev) to author the design of record.

## Dev Assessment

**Implementation Complete:** Yes (design-only — the deliverable is a design of record)

**Deliverable:** **ADR-138** — *NPC Ratification Gates Projection Eligibility*.
The Story 49-6 ratification gate (`NpcPoolMember.observation_pending`) is named as
the single projection-eligibility source of truth: unratified pool members stay out
of the ADR-118 retrieval index **and** the ADR-135 public reference surface. Key
design move (D2): the gate governs the **fill/index, never the floor** — a
scene-present, freshly-minted NPC still reaches the prompt via the 75-2 working-set
(live-struct read), so the present scene is never dropped (SOUL Guitar Solo /
ADR-014). All four context ACs are satisfied: AC1 (artifact names real structures +
rationale + rejected alternatives), AC2 (purge needs no eviction; defensive eviction
+ `entity_card.evicted` span specified), AC3 (ADR-135 shares the gate — explicit
yes), AC4 (follow-on stories 75-11..75-14 enumerated with scope).

**Files Changed (orchestrator repo, trunk-based `main`):**
- `docs/adr/138-npc-ratification-gates-projection.md` — new ADR (design of record)
- `docs/adr/README.md`, `docs/adr/DRIFT.md` — regenerated indexes (`regenerate_adr_indexes.py`)
- `sprint/context/context-story-75-9.md` — story context (committed)
- `sprint/epic-75.yaml` — story status backlog→in_progress (workflow tooling)

**Tests:** N/A — RED bypassed (design-only). ADR frontmatter validated by the
commit hook (`validate_adr_frontmatter.py`: 1 file, 0 errors). No engine code
landed, so no behaviour suite to run.

**Branch / push:** Committed to orchestrator `main` (trunk-based) as `e074e6c`,
rebased over concurrent oq-1 work (73-4, 59-15) and pushed. The `sidequest-server`
`feat/75-9-npc-pool-ratification-gate` branch is **empty** (no engine code) — see
the Dev deviation re: repo scope. No PR is created (orchestrator is trunk-based;
matches sibling ADR-118/75-3 and ADR-137/77-1).

**Self-review:** No source-text wiring tests, no stubs, no engine code. Reuse-first
honored — the ADR governs existing live structures (49-6 gate, ADR-118 machinery)
rather than rebuilding them. The implementation (`is_projectable()` predicate +
wiring + OTEL) is deferred to 75-11..75-14, each carrying its own RED tests per
Igor's tripwire.

**Handoff:** To Granny Weatherwax (Reviewer) — review ADR-138 as a design-review
(artifact completeness + internal consistency), not a code diff.

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** None blocking (one accepted improvement + one forward-verification note)

Structural gate (`gates/spec-check`) passed: every context AC (AC1–AC4) maps to a
Dev Assessment entry, implementation marked complete, and both `### TEA` and
`### Dev` deviation subsections are present and well-formed.

Substantive AC-by-AC check against the artifact (ADR-138), verified by content, not
by trusting the assessment:
- **AC1 (eligibility decision + rationale + rejected alternatives, real structures):**
  Satisfied. D1 states `observation_pending = True` ⇒ not projectable; Context names
  `NpcPoolMember.observation_pending` and the `to_card()` projector; four rejected
  alternatives are documented.
- **AC2 (purge/eviction path + OTEL span):** Satisfied. D5 establishes purge needs
  no eviction (the tidy consequence of D1), and specifies a defensive
  `entity_card.evicted{reason=unprojectable}` span; D6 lists the observability set.
- **AC3 (ADR-135 reconciliation, yes/no + why):** Satisfied. D4 is an explicit
  *yes* — the public reference surface shares the gate, with rationale and the note
  that the gate runs *before* ADR-135's public-vs-keeper projection (orthogonal to
  the spoiler firewall).
- **AC4 (follow-on stories with scope):** Satisfied. 75-11..75-14 enumerated with
  per-story scope.

**Accepted improvement (Extra-in-artifact — Architectural, Trivial → Option A):**
ADR-138 §D2 adds a floor-vs-fill distinction the story context did not spell out
(the gate governs the semantic *fill*/index, never the 75-2 *floor*). This is a
correct strengthening — it is what preserves the SOUL *Guitar Solo* / ADR-014
guarantee that a scene-present NPC is never dropped. Accepted as-is; no spec change
needed (the story context is a per-story doc, and the ADR is now the design of
record).

**Forward-verification note (Ambiguous → Option D, defer to 75-12):** D2's
"never dropped" guarantee assumes the 75-2 working-set floor reads the *live*
`npc_pool`/`Npc` structs and therefore *can* include a still-`observation_pending`,
scene-present member. If 75-2's selection happens to pre-filter on a flag that
excludes pending members, D2's guarantee would not hold. This is an implementation
assumption internal to the design, correctly deferred — **75-12 must assert, via a
behaviour/OTEL test, that a freshly-minted pending member present this turn appears
in the floor while being absent from the fill/index.** Logged for traceability; not
a blocker for the design artifact.

**Decision:** Proceed to verify (TEA). No hand-back to Dev.

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed (design-only — no behaviour suite; deliverable is an ADR)

### Simplify Report

**Teammates:** none spawned.
**Files Analyzed:** 0 code files.

Changed-file discovery found **no code files** in the 75-9 deliverable — the commit
(`e074e6c`) touches only `docs/adr/138-*.md` (+ regenerated `README.md`/`DRIFT.md`),
`sprint/context/context-story-75-9.md`, and one `sprint/epic-75.yaml` status line;
the `sidequest-server` feature branch is empty (`git diff develop...HEAD` → ∅).
Per the verify-workflow: **"No code changes to review — skipping simplify."**

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | skipped (no code) | — |
| simplify-quality | skipped (no code) | — |
| simplify-efficiency | skipped (no code) | — |

**Applied:** 0 · **Flagged:** 0 · **Noted:** 0 · **Reverted:** 0
**Overall:** simplify: clean (no code to review)

### Quality Checks (documentation deliverable)

The relevant quality gate for an ADR deliverable is the ADR frontmatter validator,
not `pf check` (no Python/TS to lint or test):
- `validate_adr_frontmatter.py`: **0 errors** (19 pre-existing title/H1 warnings on
  unrelated ADRs; ADR-138 is not among them — its title matches its H1).
- Index sync: 138 ADR files, ADR-138 present in `README.md` (2 rows: main table +
  deferred section). `regenerate_adr_indexes.py` output is committed and consistent.
- Orchestrator working tree clean.

**Quality Checks:** All passing
**Handoff:** To Granny Weatherwax (Reviewer) — design-review of ADR-138 (artifact
completeness + internal consistency), not a code diff.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean (GREEN) | 1 hygiene (epic-75.yaml unstaged status flip) | confirmed 1 (LOW, non-blocking) |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (1 enabled subagent returned GREEN; 8 disabled via `workflow.reviewer_subagents`)
**Total findings:** 3 confirmed (all LOW/non-blocking), 0 dismissed, 0 deferred

The 8 diff-based specialists are disabled at the project level — appropriate here:
the deliverable is a markdown ADR with no code paths, types, error handling, or
security surface for them to analyze. I reviewed the design substance myself (below)
and ran two reuse-first greps against the live tree.

## Reviewer Assessment

**Verdict:** APPROVED

ADR-138 is a sound, well-formed design of record. It satisfies all four context ACs,
honors reuse-first on the load-bearing structures (the 49-6 gate and the ADR-118
index machinery), and its central move — gate the *fill*, never the *floor* — is the
correct way to keep phantoms out of the index without violating SOUL *Guitar Solo* /
ADR-014. No Critical/High issues. Three LOW findings documented below; none block,
all are routed to the follow-on implementation stories.

**Observations (tagged):**

- `[VERIFIED]` ADR-138 frontmatter is schema-valid — `validate_adr_frontmatter.py`
  reports 0 errors; `status: proposed`, `implementation-status: deferred` (the one
  status that permits a non-null pointer without the drift/partial requirement —
  pointer is present and accurate), `supersedes: []` symmetric. Complies with the
  ADR-088 frontmatter schema. Evidence: `docs/adr/138-...md:1-13`.
- `[VERIFIED]` Reuse-first honored on the core structures — D1/D3 govern the existing
  `NpcPoolMember.observation_pending` (Story 49-6, `npc_pool.py:58`) and the ADR-118
  `to_card()` machinery rather than rebuilding them. Grep confirms **no** existing
  `is_projectable`/projectability predicate, so D3's predicate is genuinely new, not
  a reinvention. Evidence: `grep -rniE "is_projectable|projection_eligibl" sidequest/` → empty.
- `[RULE]` **LOW — reuse-first miss in D6.** D6 proposes emitting a *new*
  `npc.ratification.{outcome}` span for gate decisions, but the 49-6 gate **already
  emits** promote/purge spans: `npc_observation_gate_*_span`
  (`telemetry/spans/npc.py:659`, re-cite/promote) and `npc_observation_gate_purged_span`
  (`:689`, remove/purge). The design of record should **reference and reuse** those
  existing spans; only the `retrieval.npc_unratified_skipped` counter and the
  defensive `entity_card.evicted` span are genuinely new. Non-blocking (design-doc
  accuracy, not a code defect) but must be captured so 75-12 reuses the existing
  telemetry instead of duplicating it.
- `[SIMPLE]` (self-assessed; subagent disabled) **LOW — name-collision gap.** The
  design does not address the case where a ratified `Npc`/card and a freshly
  re-minted `observation_pending` pool member share a name (the index id is
  `npc:<name>`). 75-12 must define dedup-by-id behavior at the projection seam so a
  pending twin cannot shadow or duplicate a ratified card. A devil's-advocate hole,
  not a blocker for the design artifact.
- `[LOW]` hygiene (`[from preflight]`) — `sprint/epic-75.yaml` carries an unstaged
  `in_progress → in_review` status flip (workflow tooling), and `sprint/epic-59.yaml`
  has unrelated whitespace noise from another story. Neither is code or affects docs
  correctness. SM commits sprint YAML at finish; the epic-59 noise is out of 75-9's
  scope and must not be swept into this story's commit.
- `[VERIFIED]` D2 floor/fill distinction is internally consistent and honors the SOUL
  doctrines — the gate touches only the semantic fill/index; the 75-2 working-set
  floor (live-struct read) keeps a scene-present member whole. Architect already
  logged the forward-verification note for 75-12. Evidence: ADR-138 §D2 + Architect
  spec-check assessment above.

**Dispatch-tag coverage** (gate requires all 8; 8 specialists disabled, assessed by me):
- `[EDGE]` N/A — no code paths in a documentation deliverable. (disabled)
- `[SILENT]` N/A — no error-handling code; D6 *mandates* observable gate decisions
  (No Silent Fallbacks honored by design). (disabled)
- `[TEST]` N/A — design-only, RED correctly bypassed; the TEA tripwire defers all test
  obligation to 75-11..75-14. (disabled)
- `[DOC]` The deliverable **is** documentation — reviewed directly. File references
  (`npc_pool.py`, `entity_card.py`, `to_card()`) are accurate against the live tree;
  internally consistent. One reuse-first inaccuracy in D6 (see `[RULE]`).
- `[TYPE]` N/A — no types defined (predicate deferred to 75-11). (disabled)
- `[SEC]` N/A — no security surface; note the design *tightens* an exposure (keeps
  unratified phantom NPCs off the public ADR-135 reference surface) — a net
  privacy/spoiler positive. (disabled)
- `[SIMPLE]` Design is proportionate, not over-engineered — reuse-first, defers code,
  marks the optional 75-14 as "drop if not needed." See the name-collision LOW above. (disabled)
- `[RULE]` LOW reuse-first miss in D6 — confirmed against `telemetry/spans/npc.py:659/:689`.

### Rule Compliance

Applicable rules for a design-only ADR deliverable, enumerated:

- **ADR-088 frontmatter schema** (every field, enum, symmetry): 138 → **compliant**
  (0 validator errors; status/impl-status enums valid; supersession trivially
  symmetric with `supersedes: []`).
- **"Don't Reinvent — Wire Up What Exists"** (CLAUDE.md, load-bearing): mostly
  **compliant** (reuses 49-6 gate + ADR-118 machinery; no duplicate predicate) — one
  **LOW violation** in D6 (proposes new ratification span over existing 49-6 spans).
- **No Silent Fallbacks** (CLAUDE.md/SOUL): **compliant** — D5/D6 make every gate,
  skip, and eviction decision OTEL-observable; defensive eviction is explicitly
  "never silently served."
- **No Stubbing** (CLAUDE.md): **compliant** — no stub code; implementation honestly
  deferred to enumerated follow-on stories, not left as empty shells.
- **OTEL Observability Principle** (every subsystem decision emits a span): **compliant**
  in intent (D6), modulo the reuse note above.
- **SOUL — Guitar Solo / Diamonds & Coal (ADR-014)**: **compliant** — D2 guarantees
  the present scene is never dropped; ratification = coal→diamond on engagement.

### Devil's Advocate

Assume ADR-138 is broken. Where does it fail? First, the entire "purge needs no
eviction" tidiness (D5) rests on an absolute: that a member is *never* indexed while
`observation_pending`. That holds only if the projection seam consults the gate
synchronously before every embed. If a future async embedding pass races a same-turn
purge, a phantom could be embedded microseconds before removal and linger as a
ghost card — the "defensive eviction" path exists precisely because the absolute is
not truly absolute, which means D5's clean story is aspirational, not guaranteed.
Second, name collisions: the index id is `npc:<name>`. The narrator re-mints prose
NPCs freely; nothing in the design prevents a *new* pending "Borin" from colliding
with an already-ratified "Borin" card. If the projector keys on name alone, the
pending twin could overwrite or shadow the canonical card, or the gate could promote
the wrong one — a real data-integrity hole the ADR is silent on. Third, the ADR-135
coupling assumes 65-9 (public Cast projection) renders live; if that surface caches,
a just-ratified NPC won't appear until refresh, and a just-purged phantom could
linger publicly for a turn — a spoiler-adjacent staleness. Fourth, the whole edifice
assumes the 49-6 gate fires every turn; a turn that errors before adjudication leaves
pending members un-ruled (though `narration_apply.py:2319` shows unresolved-survivor
handling already exists, partially mitigating this). None of these break the *design
artifact* — they are implementation risks the follow-on stories must close — but the
name-collision gap is concrete enough that I have raised it as a LOW finding and a
delivery finding for 75-12. The design is approved because it is the right shape and
its gaps are downstream, not structural.

**Data flow traced:** player action → narrator mints prose NPC → `NpcPoolMember(observation_pending=True)`
(`session_helpers.py:1851`) → 49-6 gate next turn promotes (clear flag) or purges
(`narration_apply.py:2319`) → ADR-138 D1: only ratified/promoted members reach the
ADR-118 `to_card()` projector and the ADR-135 reference surface. Safe: phantoms never
embed; present-scene members ride the floor regardless (D2).

**Pattern observed:** Reuse-first governance ADR over live structures — same pattern
as ADR-118 completing the lore RAG. Good pattern.

**Handoff:** To SM (Captain Carrot) for finish-story. Three LOW findings recorded as
delivery findings for the follow-on implementation stories; none block.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

- **Question (non-blocking, sm/setup):** The story title cites "(ADR-135)" but
  ADR-135 is *Reference Pages Are a Public Table Tool* and the latest ADR on disk
  is 137. The title's own clause ("governs ADR-118 projection source") indicates
  the primary governed surface is **ADR-118**, with ADR-135 a relevant
  cross-reference (reference pages render the public NPC pool). **If this design
  warrants its own ADR, it should take the next free number (138), not 135.**
  Architect to confirm during design: new ADR-138 vs. a design spec amending
  ADR-118 §D3. See `sprint/context/context-story-75-9.md` Assumptions.
- **Gap (non-blocking, sm/setup):** The pool/Npc split AND a ratification gate
  already exist (`NpcPoolMember.observation_pending`, Story 49-6;
  `npc_pool.py:58`). This is a *governance/reconciliation* design over existing
  live structures, not greenfield — reuse-first. Design must not rebuild the
  split or the gate.

### TEA (test design)
- **Improvement** (non-blocking): Story is design-only; RED bypassed (documentation
  deliverable). The tripwire for Dev/Reviewer — if the design concludes a code
  predicate (`is_projectable(member) -> bool`) or any gate→projection wiring should
  land *in this story* rather than a follow-on, that is a scope expansion from
  design-only to design+code and **must bounce back to RED** for a failing unit
  test + a wiring/OTEL assertion (per repo "No Source-Text Wiring Tests" doctrine).
  Affects `sidequest-server` (any new predicate module). *Found by TEA during test design.*
- **Question** (non-blocking): The context's AC1–AC4 are artifact-completeness review
  gates, not executable tests. Reviewer (Granny) should treat them as a design-review
  checklist, not expect a green test suite for this story. Affects
  `sprint/context/context-story-75-9.md`. *Found by TEA during test design.*

### Dev (implementation)
- **Question** (non-blocking, RESOLVED): The "(ADR-135)" title question (raised by
  SM) is resolved by ADR-138 §D4 — reference pages **do** share the ratification
  gate, and the design takes a new number (ADR-138), not 135. Affects
  `docs/adr/138-npc-ratification-gates-projection.md`. *Found by Dev during implementation.*
- **Improvement** (non-blocking): ADR-138 enumerates follow-on implementation
  stories **75-11..75-14** but does not create them (story creation is PM/SM scope).
  Sprint currently ends at 75-10. Recommend adding 75-11 (`is_projectable()` +
  unit tests), 75-12 (ADR-118 projection wiring + OTEL), 75-13 (ADR-135 reference
  wiring), 75-14 (optional defensive eviction) via `pf sprint story add`. Affects
  `sprint/epic-75.yaml`. *Found by Dev during implementation.*

### TEA (test verification)
- No upstream findings during test verification. Design-only deliverable; no code to
  simplify, ADR frontmatter validates clean (0 errors), index in sync.

### Reviewer (code review)
- **Improvement** (non-blocking): ADR-138 §D6 should reuse the existing Story 49-6
  ratification spans (`npc_observation_gate_*_span` / `npc_observation_gate_purged_span`,
  `telemetry/spans/npc.py:659`, `:689`) rather than introduce a new
  `npc.ratification.{outcome}` span — only the `retrieval.npc_unratified_skipped`
  counter and the defensive `entity_card.evicted` span are genuinely new. Affects
  `sidequest-server/sidequest/telemetry/spans/npc.py` (75-12 must reuse, not
  duplicate). *Found by Reviewer during code review.*
- **Gap** (non-blocking): ADR-138 is silent on name collisions between a ratified
  `Npc`/card and a freshly re-minted `observation_pending` pool member sharing a name
  (index id `npc:<name>`). 75-12 must define dedup-by-id at the projection seam so a
  pending twin cannot shadow/duplicate a ratified card. Affects
  `sidequest-server/sidequest/game/entity_card.py` (projection id strategy).
  *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `sprint/epic-75.yaml` has an unstaged
  `in_progress → in_review` status flip; SM commits sprint YAML at finish. The
  unrelated `sprint/epic-59.yaml` whitespace noise belongs to another story and must
  NOT be swept into 75-9's history. Affects `sprint/epic-75.yaml`. *Found by Reviewer
  during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No deviations from spec. RED is bypassed under the documentation chore-bypass
  criterion: the story's deliverable is a design artifact (ADR/spec markdown), and
  the context explicitly frames its acceptance criteria as artifact-completeness
  review gates rather than executable behaviour. This is consistent with the
  sibling design-only story 75-3 (ADR-118 design), which shipped no code. Writing a
  failing test against the not-yet-designed `is_projectable()` predicate was
  considered and rejected — it would presuppose a signature/module the design must
  decide first, producing a vacuous or fictional test.

### Dev (implementation)
- **Design-only deliverable lands in the orchestrator repo, not the story's `sidequest-server` scope**
  - Spec source: `.session/75-9-session.md` Repos / `sprint/epic-75.yaml` `repos: sidequest-server`
  - Spec text: "repos: sidequest-server" — the story is scoped to the server repo
  - Implementation: The design of record is **ADR-138**, committed to the
    **orchestrator** repo (`docs/adr/138-npc-ratification-gates-projection.md`) on
    trunk-based `main`, with regenerated `docs/adr/README.md` + `DRIFT.md` and the
    `sprint/context/context-story-75-9.md`. The `feat/75-9-...` branch in
    sidequest-server is **empty** — no engine code lands in a design-only story.
  - Rationale: ADRs live only in the orchestrator (`docs/adr/`), and the ADR-index
    tooling (`scripts/regenerate_adr_indexes.py`) scans that tree. Sibling
    design-only stories landed identically — ADR-118 (75-3) and ADR-137 (77-1) were
    both direct commits to orchestrator `main`, not subrepo PRs. Established pattern.
  - Severity: minor
  - Forward impact: SM finish should NOT expect a sidequest-server PR — the
    deliverable is already on orchestrator `main` (trunk-based, no PR); the empty
    server feature branch can be deleted unused. Implementation code (the
    `is_projectable()` predicate + wiring + OTEL) is deferred to follow-on stories
    75-11..75-14, each carrying its own RED tests.

### Reviewer (audit)
- **TEA — "RED bypassed under documentation chore-bypass"** → ✓ ACCEPTED by Reviewer:
  correct call; the deliverable is a markdown ADR with no behaviour to drive
  red→green, and the tripwire for any future code seam is well-stated.
- **Dev — "Design-only deliverable lands in the orchestrator repo, not the story's
  `sidequest-server` scope"** → ✓ ACCEPTED by Reviewer: matches the sibling
  precedent (ADR-118/75-3, ADR-137/77-1 both committed to orchestrator `main`); the
  ADR-index tooling lives in the orchestrator, so this is the only correct home. The
  empty server branch and no-PR finish are expected, not defects.
- **Undocumented (Reviewer-spotted):** ADR-138 §D6 proposes a new
  `npc.ratification.{outcome}` span while the Story 49-6 gate already emits
  promote/purge spans (`telemetry/spans/npc.py:659`, `:689`). Spec ("Don't Reinvent")
  says reuse; design proposes new. Severity: **LOW** (design-doc accuracy; routed to
  75-12). Logged as a delivery finding, not a blocker.

### Architect (reconcile)

Existing TEA and Dev deviation entries reviewed: both accurate, all 6 fields
substantive, cited spec sources verified to exist (`.session/75-9-session.md`,
`sprint/epic-75.yaml`, ADR-118/75-3, ADR-137/77-1). No corrections needed. The
Reviewer's audit stamped both ACCEPTED and surfaced one undocumented item, which I
formalize here for the manifest:

- **ADR-138 §D6 proposes a new ratification span instead of reusing the live Story 49-6 spans**
  - Spec source: `sidequest-server/CLAUDE.md` — "Don't Reinvent — Wire Up What Exists"
  - Spec text: "Before building anything new, check if the infrastructure already
    exists in the codebase. … The fix is integration, not reimplementation."
  - Implementation: ADR-138 §D6 specifies emitting `npc.ratification.{outcome}` with
    `outcome ∈ {promote, purge, pending}`, but the 49-6 gate already emits
    `npc_observation_gate_*_span` (promote, `telemetry/spans/npc.py:659`) and
    `npc_observation_gate_purged_span` (purge, `:689`). Only the `pending` outcome,
    the `retrieval.npc_unratified_skipped` counter, and the `entity_card.evicted`
    span are genuinely new.
  - Rationale: design-of-record accuracy — captured so the 75-12 implementer reuses
    the existing promote/purge spans and adds only the genuinely-new emissions, rather
    than duplicating telemetry.
  - Severity: minor (LOW)
  - Forward impact: 75-12 must reference the existing spans; ADR-138 §D6 should be
    amended (one-line clarification) when 75-12 lands, or by a follow-up doc tweak.
- **ADR-138 is silent on ratified-vs-pending name collision at the projection id (`npc:<name>`)**
  - Spec source: ADR-118 §D3 (`docs/adr/118-universal-retrieval-layer.md`)
  - Spec text: "`id` — stable: \"npc:borin\", …" (EntityCard id keyed on name)
  - Implementation: ADR-138 does not define behavior when a freshly re-minted
    `observation_pending` pool member shares a name with an already-ratified
    `Npc`/card — both would resolve to id `npc:<name>`, risking shadow/duplicate.
  - Rationale: design gap, not a chosen deviation — the present design assumes name
    uniqueness across the ratified/pending boundary, which the narrator's free
    re-minting does not guarantee.
  - Severity: minor (LOW)
  - Forward impact: 75-12 must define dedup-by-id at the projection seam
    (`game/entity_card.py`); does not affect any sibling story already merged.

No ACs were deferred (AC1–AC4 all satisfied per the Architect spec-check and Reviewer
verdict), so the AC-deferral cross-check is a no-op.