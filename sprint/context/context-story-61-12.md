---
parent: context-epic-61.md
workflow: tdd
---

# Story 61-12: Compact narrator `output_only.md` prose (~50% reduction) and fix npcs_met/npcs_present field drift

## Business Context

Epic 61's runaway-Valley incident (2026-05-23, ~$313 in 48 hours) was driven by
unbounded snapshot growth × 8 tool-loop iterations × uncached input. Stories
61-1 through 61-5 closed the snapshot-side hole. This story closes the
**prose-side** hole: `narrator_prompts/output_only.md` (the OUTPUT-ONLY tool-use
guidance block) is currently 284 lines / ~24,784 bytes / ~3,600 tok — 28% of the
13,105-tok per-turn prompt. Because it lives in `system_blocks[0]` it is
cache-friendly, but **every** non-magic world (`road_warrior`, `pulp_noir`,
`tea_and_murder`, `spaghetti_western`) pays ~400 tok of magic-only prose every
turn, and several rules are restated 2-3× across the file.

The story is structurally identical to 61-2/61-3: enumerate the actual growers,
compact by preservation-rewrite (NEVER by deleting rules), and gate plugin-
conditional prose behind the existing `context.magic_state is not None` switch
at `orchestrator.py:1859`. Customer-facing impact: zero. Narrator output is
unchanged. This is a token-budget and correctness story, not a feature.

A small but load-bearing **correctness fix** rides along: the file uses both
`npcs_met` (line 208 main spec block) AND `npcs_present` (line 281-283 ROSTER
DISCIPLINE block) for what is **the same sidecar field**. The codebase canonical
name is `npcs_present` (25+ call sites across `protocol/messages.py`,
`session.py`, `persistence.py`, `narration_apply.py`, telemetry spans), and
`orchestrator.py:979,1003` carries a silent fallback (`patch.get("npcs_present",
patch.get("npcs_met", []))`) that papers over the divergence. Memory's hard ban
on fallbacks applies: the prose drift gets fixed AND the fallback is removed
in this story.

## Drift-Direction Resolution (Important)

**Story description had AC-1 inverted.** The original AC said "zero `npcs_present`,
only `npcs_met`". The codebase shows the opposite is canonical:

| Site | Field used |
|------|-----------|
| `protocol/messages.py:241` (`ScrapbookEntryNpcRef`) | `npcs_present` |
| `game/session.py:384` (`WorldStatePatch.npcs_present`) | `npcs_present` |
| `game/persistence.py:148` (DB column) | `npcs_present` |
| `agents/orchestrator.py:439` (`NarrationResult.npcs_present`) | `npcs_present` |
| `server/narration_apply.py` (10+ refs) | `npcs_present` |
| `server/emitters.py:45,53,579,622` | `npcs_present` |
| `telemetry/spans/encounter.py`, `telemetry/spans/npc.py` | `npcs_present` |
| `server/render_trigger.py:84` | `npcs_present` |
| `agents/tools/begin_confrontation.py:35` ("narrator's sidecar npcs_present") | `npcs_present` |
| `agents/orchestrator.py:979,1003` (parser fallback) | `npcs_present` primary, `npcs_met` silent fallback |

**Inverted AC-1 (TEA-resolved 2026-05-24, user-confirmed):**
1. `output_only.md` (post-rewrite) ships with **zero occurrences** of `'npcs_met'` — only `'npcs_present'`.
2. `orchestrator.py:979` and `orchestrator.py:1003` drop the `patch.get("npcs_met", [])`
   fallback — single-key parse against `'npcs_present'` only.

See **Design Deviations → TEA** in the session file for the full deviation log.

## Technical Guardrails

**From epic 61 architecture:** 61-12 must preserve every rule currently
enforced by prose-content tests (AC-6). It does NOT touch snapshot fields,
section selection, or tool definitions. It MAY add a new conditional prose
section (the magic-rule extraction in AC-3).

**Files in scope (server repo, all paths under `sidequest-server/`):**

| File | Change |
|------|--------|
| `sidequest/agents/narrator_prompts/output_only.md` | REWRITE (compaction + field-drift fix) |
| `sidequest/agents/narrator_prompts/magic_output_rules.md` *(new)* | EXTRACT CRITICAL MAGIC EFFECT RULE (§1) + CRITICAL MAGIC RULE (§3) + CRITICAL MAGIC NEGATIVE CASE prose |
| `sidequest/agents/narrator_prompts/__init__.py` | ADD `NARRATOR_MAGIC_OUTPUT_RULES: str = _load("magic_output_rules.md")` + `__all__` entry |
| `sidequest/agents/orchestrator.py:1859-1879` | Conditional registration block — register a new section (e.g. `"magic_output_rules"`, Early zone, SectionCategory.Rules) when `context.magic_state is not None`, alongside the existing `magic_context` registration |
| `sidequest/agents/orchestrator.py:979,1003` | DROP `patch.get("npcs_met", [])` silent fallback — single-key parse against `'npcs_present'` only |
| `sidequest/agents/narrator_guardrails.py:4,31` | Remove `npcs_met` references in docstring + constraint string (line 31's "entry in ``npcs_met`` —" becomes "entry in ``npcs_present`` —") |
| Existing test files | UPDATE phrase-match assertions to post-rewrite spellings — never xfail, never skip |

**Compaction passes (preservation-by-rewrite):**

1. **Items table collapse.** Four `items_*` field paragraphs (lines 186-195)
   become one block: a shared sentence on `{name, description, category,
   recipient}` schema + one line per field naming the trigger. ~150 tok saved.

2. **Magic prose extraction (conditional).** CRITICAL MAGIC EFFECT RULE
   (§1, ~12 lines), CRITICAL MAGIC RULE (§3, ~15 lines), and CRITICAL MAGIC
   NEGATIVE CASE (~16 lines) move OUT of `output_only.md` and into the new
   `magic_output_rules.md`. The new prose registers via
   `registry.register_section(...)` only when `context.magic_state is not
   None` — the existing chokepoint at `orchestrator.py:1859`. On non-magic
   worlds (road_warrior, pulp_noir, tea_and_murder, spaghetti_western), zero
   bytes leak. ~400 tok saved per turn on those worlds.

3. **Banner demotion.** Today: 8 `CRITICAL` + 6 `MANDATORY` = 14 banners. Target:
   ≤ 4 total. Survivors are the load-bearing ones (STRICT SPLIT / silent-fallback
   gate, INVENTORY contract, ADVERSARY/ROSTER `npcs_present` contract, MAGIC
   block — the latter lives in `magic_output_rules.md` post-extraction so doesn't
   count toward the 4). Others demote to normal-emphasis prose.

4. **Tail self-restatement removal.** STRICT SPLIT (lines 236-242),
   PERCEPTION FIREWALL (lines 244-260), WHEN TO ATTACH visual_scene
   (lines 271-275), ROSTER DISCIPLINE (lines 277-283) — three of these
   restate rules already given upstream in the same file. Keep one
   one-line pointer to each rule, drop the restated paragraph.
   **EXCEPTION:** PERCEPTION FIREWALL is load-bearing (ADR-105 multiplayer
   leak vector) — it stays as a SHORT (3-4 line) section, not deleted.

5. **TRIGGER CRITERIA tightening.** §4's 9-bullet enumeration (lines 106-120)
   collapses to a general principle + a pointer to the `begin_confrontation`
   tool's enum (which authoritatively lists `combat`, `brawl`, `ship_combat`,
   `dogfight`, `negotiation`, `chase`, `trial`, `auction`, `social_duel`,
   `scandal`). The 4 social/non-violence types still must be explicitly named
   in surviving prose — Story 50-2's regression tests assert each token is
   present in the file (see `test_50_2_confrontation_trigger_prompt.py`).

**Target byte/token budget:** ~24,784 bytes / ~3,600 tok today →
**≤ 13,800 bytes / ≤ 2,000 tok** after rewrite (AC-2).

**Patterns to follow:**

- **NO-FALLBACK (project memory `feedback_no_fallbacks_hard`).** Don't introduce
  a magic-rules fallback for non-magic worlds; the conditional registration
  IS the gate. Don't soften the orchestrator.py:979/1003 fallback removal to
  "warn then continue" — fail loud or remove cleanly. Single-key
  `patch.get("npcs_present", [])` is the post-rewrite shape.
- **No content-coupled tests (`feedback_no_content_coupled_tests`).** Tests
  assert phrase presence/absence on `NARRATOR_OUTPUT_ONLY` (the loaded
  constant). They do NOT load live `genre_packs/*` to fire the prose.
- **One mechanism per problem (`feedback_one_mechanism_per_problem`).** Magic
  prose has ONE gate — the existing `context.magic_state is not None` at
  `orchestrator.py:1859`. Do NOT add a parallel `world.has_active_magic_plugin()`
  helper unless the existing chokepoint isn't sufficient.
- **Diamonds and Coal.** The 4 surviving CRITICAL banners are diamonds.
  Demoted prose is still coal — necessary for the rules to be expressible,
  but it doesn't shout. Reader attention is a finite resource the prose
  spends in inverse proportion to how loud everything else is.

**Token-measurement methodology:** The full anthropic tokenizer isn't trivially
available offline; use Anthropic's `chars/4` rule-of-thumb (matches the
within-5% empirical accuracy quoted in their docs) or `tiktoken`'s
`cl100k_base` as a slightly-conservative proxy. The test budget is set in
**bytes** to avoid tokenizer-library dependency churn: `len(NARRATOR_OUTPUT_ONLY)
< 13800` enforces the ~2,000 tok ceiling under the chars/4 heuristic.

**Dependencies / sequencing:**

- 61-9 (rename `output_only_sdk.md` → `output_only.md`) is **MERGED**
  (commit 60de0bd on main, e218ac6 on server develop). This story operates on
  the post-rename file.
- No downstream blockers in the active sprint.

## Scope Boundaries

**In scope:**

- Rewrite `output_only.md` per the five compaction passes above.
- Create `magic_output_rules.md` and wire its conditional registration in
  `orchestrator.py` adjacent to the existing magic_context block.
- Add `NARRATOR_MAGIC_OUTPUT_RULES` constant to `narrator_prompts/__init__.py`.
- Fix the `npcs_met` → `npcs_present` field drift in the prose (both line
  208 and any incidental references) AND in the orchestrator parser fallback.
- Update `narrator_guardrails.py` constraint strings to reference
  `npcs_present`.
- Update existing prose-content test assertions to post-rewrite spellings
  (no xfail, no skip).
- Full server suite passes (`uv run pytest -v`).

**Out of scope:**

- Snapshot-field projection (61-2's surface).
- Tool definitions or tool-use protocol changes (ADR-102 unchanged).
- Genre-pack prose edits.
- ADR amendments (none required — ADR-101's "SDK as narrator backend" is
  unchanged; ADR-102's tool contract is unchanged).
- Renaming `npcs_met` references in unrelated test files that aren't
  asserting on the prose (e.g. `test_narrator_sdk_hybrid_split.py` uses
  `npcs_present` already and is unaffected).
- Per-turn cost measurement against a live playtest (AC-7's "≥ 1,500 tok
  drop on non-magic playtest turn" is verified at Verify phase via a
  synthetic prompt assembly, not a live LLM call).

## AC Context

**AC-1 (inverted): Field-drift correctness.**
Verifiable by `grep -c 'npcs_met' sidequest/agents/narrator_prompts/output_only.md`
returning `0`. AND `grep -nE 'npcs_met' sidequest/agents/orchestrator.py` showing
no parser fallback. Test: `'npcs_met' not in NARRATOR_OUTPUT_ONLY` AND the
extracted-game-patch function returns the same list whether the sidecar key is
present or absent (deterministic single-key parse).

**AC-2: Total byte budget.**
`len(NARRATOR_OUTPUT_ONLY) <= 13800` bytes (≈ 2,000 tok under chars/4
heuristic). Today: 24,784 bytes. Reduction: ~44% bytes, matches the "~50%
prose reduction" target with headroom.

**AC-3: Magic prose extraction.**
Three negative assertions on `NARRATOR_OUTPUT_ONLY` (each of the three magic-rule
banners is GONE), three positive assertions on `NARRATOR_MAGIC_OUTPUT_RULES`
(each is PRESENT), and one wiring assertion via orchestrator: when
`context.magic_state is not None`, a section named `magic_output_rules` is
registered on the prompt registry; when `context.magic_state is None`, no such
section appears.

**AC-4: Items field consolidation.**
Today there are four near-identical paragraphs introducing `items_gained`,
`items_lost`, `items_discarded`, `items_consumed`. Post-rewrite there is ONE
introduction (a shared schema sentence + one trigger line per field).
Verifiable by: each of the 4 field names appears in `NARRATOR_OUTPUT_ONLY`
(rule still expressible), AND the total bytes between the first and last
of the 4 field-name occurrences is reduced by ≥ 30% from the current
distance.

**AC-5: Banner count.**
`NARRATOR_OUTPUT_ONLY.count('CRITICAL') + NARRATOR_OUTPUT_ONLY.count('MANDATORY')
<= 4`. Current: 14 (8 CRITICAL + 6 MANDATORY).

**AC-6: Existing prose-content tests still pass.**
Not a TEA-authored test — this is a verify-phase gate: the existing assertions
in `test_narrator.py`, `test_50_2_confrontation_trigger_prompt.py`,
`test_47_9_innate_proactive.py`, `test_narrator_prompt.py`, and
`test_57_4_recency_guardrails_migration.py` will need phrase-string updates
where Dev's rewrite changes the wording. The rule being asserted must still
be expressible — if a test phrase becomes unfindable because the rule itself
was removed (not just rephrased), that's a deviation that requires this story's
AC-6 to be re-evaluated. No xfail, no skip, no test deletion-without-replacement.

**AC-7: Per-turn token reduction on non-magic-world turn.**
Verified at verify phase via synthetic prompt assembly: build a narrator prompt
for a `tea_and_murder/glenross` turn (no `magic_state`), measure
`len(system_blocks[0])`, and assert it dropped by ≥ 6,000 bytes (≈ 1,500 tok
under chars/4) vs the pre-change baseline captured at the start of the story.
TEA writes the assertion shape; Dev captures the baseline before starting
rewrite.

## Assumptions

- `tiktoken`'s cl100k_base is **NOT** assumed to be available — tests use byte
  budgets (chars/4 heuristic) to avoid tokenizer-dependency drift.
- The conditional-section mechanism at `orchestrator.py:1859-1879` is the
  authoritative wiring point. If Dev finds a more natural spot (e.g. inside
  `build_magic_context_block` itself), that's a deviation with rationale.
- No live LLM call is required for any RED-phase or verify-phase test in this
  story. The byte-level assertions are deterministic and the conditional-
  registration assertion fires against the in-process `PromptRegistry`.
- The 4 surviving banners are author's-judgment-call diamonds. The test
  enforces the **count ceiling** (≤ 4), not which 4 — the AC asks for "load-
  bearing" survivors but doesn't enumerate them; Reviewer judges fit.
- The orchestrator.py:979/1003 fallback removal is in-scope per user
  confirmation 2026-05-24. If anything in the test suite relies on emitting
  `npcs_met` and reading it back, that's a stale-test fix — never xfail it.

If any assumption proves wrong during RED phase, log under `## Design
Deviations → ### TEA (test design)` in the session file.
