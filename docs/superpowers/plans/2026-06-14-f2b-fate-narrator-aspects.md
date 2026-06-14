# F2b — Aspects-as-Prompt + Invoke Surfacing + Compel Proposal — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Story:** 116-2 · **Epic:** 116 (ADR-144 F2) · **Branch base:** `develop` (gitflow) · **Repo:** `sidequest-server`
**Decomposition:** `docs/superpowers/plans/2026-06-14-f2-narrator-intent-router-integration.md` (slice F2b).
**Design:** `docs/superpowers/specs/2026-06-14-fate-core-binding-replaces-native-design.md` §4.5, §5 (epic F2).
**Depends on:** F1b (FateSheet + fate-point economy + `offer_compel`/`accept_compel`/`invoke_aspect`) and F2a (`_build_fate_summary`) — **both merged.**

---

## 1. Goal

F1 built the Fate engine; F2a classifies freeform actions into Fate dispatches. But **the narrator is blind to the Fate fiction**: `build_narrator_prompt` carries no aspects, no fate points, no invokable aspects, and the narrator has no way to *propose a compel*. So the prose never says "your **Hot-Headed** trouble flares — invoke it for +2?" and never offers the fate-point economy that is the heart of Fate.

F2b makes the narrator Fate-aware on the **prompt** side and gives it **one new tool**:
1. Register per-turn **Fate prompt sections** (character aspects, fate points, invokable character + scene aspects) gated on `pack.rules.ruleset == "fate"`, reusing F2a's `_build_fate_summary` projection as the single source of truth.
2. Add an **invokable-aspect directive** so the narrator surfaces to the player which aspects can be invoked (+2 / reroll) and at what cost (a free invoke, else a fate point).
3. Add a **`propose_fate_compel`** narrator tool: the narrator proposes a compel on an aspect → `FateRulesetModule.offer_compel` fires `fate.compel.offered` → a **pending compel** is stored on the snapshot. (Accept/refuse round-trip is deferred to F3/UI per the decomposition §7.2 — F2b proposes and records; it does not mutate the fate-point economy.)

**Non-goals (this slice):** the compel **accept** path (`accept_compel`, earns a fate point) — deferred to F3 UI. Player-driven invoke *resolution* already rides F1d/F2a (`FateActionPayload.invoke_aspect`); F2b only **surfaces** invokability, it does not re-implement invoke. Create-advantage rendering + the honesty watcher are **F2c** (116-4).

## 2. Architecture — reuse, don't reinvent (CLAUDE.md)

Everything F2b needs already exists; this slice is wiring.

```
build_narrator_prompt (agents/orchestrator.py:1746+)
  → registry.register_section(agent, PromptSection.new(name, body, AttentionZone.Valley, SectionCategory.X))
        ◀── NEW: a "fate_state" section (+ invokable-aspect directive), gated on pack.rules.ruleset=="fate",
            built from _build_fate_summary(snapshot)  (intent_router_pass.py:229-256)
        mirrors the magic block (orchestrator.py:2318-2344) and mutation block (2358-2386)

narrator tool-use turn
  → propose_fate_compel tool   ◀── NEW (agents/tools/propose_fate_compel.py, @tool ruleset-gated to "fate")
        → ruleset.offer_compel(aspect_text, actor)   (game/ruleset/fate.py — fires fate.compel.offered, no economy change)
        → store a pending compel on the snapshot (for F3 accept)
```

**Prompt-section framework** (verified live): `registry.register_section(agent_name, PromptSection.new(name, content, AttentionZone.{Primacy|Early|Valley|Late|Recency}, SectionCategory.X))` (orchestrator.py:1803-1811). The magic and mutation blocks are the exact precedent for a **conditional, per-turn, state-derived** section — mirror them. Fate points and aspects are **volatile** (change mid-session), so the section belongs in **`AttentionZone.Valley`** (per-turn game-state band), NOT the cached/STABLE prefix.

**Shared projection:** `_build_fate_summary(snapshot)` (intent_router_pass.py:229-256) already returns `{skills, fate_points, character_aspects, scene_aspects, active_conflict}`, gated identically on `pack.rules.ruleset == "fate"` (intent_router_pass.py:386-387). F2b builds its prompt section from the **same** function — one source of truth for "what aspects/points/skills exist this turn." If the function lives only in `intent_router_pass.py`, hoist it (or a thin shared `fate_projection`) to a location both the router pass and the prompt builder import, rather than duplicating the projection. **Do not author a second projection.**

**Tool registry** (verified live): `@tool(name=, description=, category=ToolCategory.WRITE)` (tool_registry.py:160-220) + a `BaseModel` args class (`extra="forbid"`) + `async def handler(args, ctx: ToolContext) -> ToolResult`. `advance_confrontation` (agents/tools/advance_confrontation.py:86-147) is the template. WN tools are **ruleset-gated** (availability filtered per bound ruleset — see `tests/agents/test_102_5_wn_tool_narrator_wiring.py`); `propose_fate_compel` must gate to `ruleset == "fate"` the **same way** (discover the exact gating from the WN tools; do not invent a new mechanism).

## 3. Shared contracts

1. **Fate prompt section** — a `PromptSection` named `"fate_state"` in `AttentionZone.Valley`, registered ONLY when `pack.rules.ruleset == "fate"`. Body (human-readable, from `_build_fate_summary`):
   - per-PC: skills line (or the top few), current fate points, character aspects (high concept / trouble / character), filled-consequence aspects;
   - scene aspects (situation aspects + boosts currently in play);
   - an **invokable-aspect directive**: the aspects this player may invoke for +2 (or reroll) and the cost (free invoke if available, else 1 fate point), phrased as guidance for the narrator to surface to the player.
2. **`PendingCompel`** — a small model stored on the snapshot (e.g. `encounter.pending_compels: list[PendingCompel]` or a session-scoped field; choose the spot F3 will read) carrying `{actor, aspect_text, reason}`. F2b appends one when `propose_fate_compel` fires; F3 consumes/clears it on accept/refuse. Do **not** mutate fate points here.
3. **`propose_fate_compel` tool** — `ToolCategory.WRITE`, ruleset-gated to `"fate"`. Args: `{actor: str, aspect_text: str, reason: str}`. Handler: resolve the actor's `fate_sheet`; call `ruleset.offer_compel(aspect_text=, actor=)` (fires `fate.compel.offered` — already live, F2b only *fires* it); append a `PendingCompel`; return a `ToolResult` describing the offer.

## 4. OTEL

- `fate.compel.offered` — **already live + routed** (telemetry/spans/fate.py:161-177 + SPAN_ROUTES). F2b's tool *fires* it via `offer_compel`. Do **not** redefine it.
- No new span is strictly required for F2b. If a wiring test needs an anchor for "the Fate prompt section was built," prefer a **behavior assertion on the assembled prompt** (section present for a fate pack, absent otherwise) over a new span — the section is prompt content, not a subsystem decision. (A `fate.prompt.section_built` span is optional; only add it if the GM panel genuinely needs to see prompt assembly. Default: no new span.)

---

## Task 1 — Fate prompt section + invokable-aspect directive

- [ ] **Step 1: Write the failing test** — `tests/agents/test_fate_narrator_prompt.py` (mirror `tests/magic/test_narrator_pre_prompt.py` and `tests/mutation/test_102_7_context_builder.py` — the conditional-section-gating precedents). Build a synthetic `ruleset: fate` pack + a snapshot with a PC that has a `FateSheet` (aspects, fate points, a live scene aspect). Call the real `build_narrator_prompt` (or the section-building helper it calls) and assert: (a) for a fate pack, a `"fate_state"` section exists in the assembled prompt and its body contains the PC's character aspects, fate-point count, and the invokable-aspect directive; (b) for a **non-fate** pack (e.g. native/WN), NO `"fate_state"` section is registered. Behavior test on prompt output — **no source-text greps**.
- [ ] **Step 2: Run test to verify it fails.**
- [ ] **Step 3: Hoist/share `_build_fate_summary`** if needed so both `intent_router_pass.py` and the prompt builder import one projection (no duplicate). Add a `_build_fate_prompt_section(snapshot, pack)` (or inline in `build_narrator_prompt`) that, **gated on `pack.rules.ruleset == "fate"`**, renders the summary into a `PromptSection.new("fate_state", body, AttentionZone.Valley, SectionCategory.<the same category magic/mutation use for state>)` and registers it. Include the invokable-aspect directive (which aspects can be invoked, the +2/reroll, and free-invoke-else-fate-point cost). Mirror the magic block (orchestrator.py:2318-2344).
- [ ] **Step 4: Run test to verify it passes.**
- [ ] **Step 5: Confirm zone/caching correctness** — assert (a test or a note) the section is in `Valley`, NOT in `STABLE_SECTION_NAMES`/the cached prefix (fate points are volatile; promoting them would stale the cache — see project memory on ADR-112 cache promotion). Run `tests/agents/test_narrator_prompt.py` to confirm no regression to the existing prompt assembly.
- [ ] **Step 6: Commit** — `feat(fate): F2b — Fate narrator prompt section (aspects, fate points, invokable-aspect directive)`.

## Task 2 — `propose_fate_compel` tool + pending-compel storage

- [ ] **Step 1: Write the failing test** — `tests/agents/tools/test_propose_fate_compel.py` (mirror `tests/agents/tools/test_102_5_wn_tool_handlers.py` for handler behavior + `tests/agents/test_102_5_wn_tool_narrator_wiring.py` for ruleset gating). Assert: (a) dispatching `propose_fate_compel` through the **real** tool registry with a fate-bound pack calls `offer_compel`, fires `fate.compel.offered` (real `InMemorySpanExporter`), and appends a `PendingCompel` to the snapshot with the right `{actor, aspect_text, reason}`; (b) the tool is **available** when `ruleset == "fate"` and **absent** for a non-fate ruleset (gating mirrors the WN tools); (c) the handler does **not** change the actor's fate-point count (accept is deferred).
- [ ] **Step 2: Run test to verify it fails.**
- [ ] **Step 3: Implement the tool** — `sidequest/agents/tools/propose_fate_compel.py`: `ProposeFateCompelArgs(BaseModel, extra="forbid")` `{actor, aspect_text, reason}`; `@tool(name="propose_fate_compel", category=ToolCategory.WRITE, <ruleset-gate to "fate" the same way WN tools gate>)`; handler resolves `snapshot.find_creature_core(actor).fate_sheet`, calls `ruleset.offer_compel(aspect_text=, actor=)`, appends a `PendingCompel` (define the model + its snapshot home), returns a `ToolResult`. Register it (mirror how existing tools self-register via the decorator).
- [ ] **Step 4: Run test to verify it passes.**
- [ ] **Step 5: Wiring** — confirm the tool is reachable from the narrator's tool set for a fate pack (the ruleset-gated availability test in Step 1 IS the wiring proof — it drives the real registry/filter, per "Every Test Suite Needs a Wiring Test" + "No Source-Text Wiring Tests").
- [ ] **Step 6: Commit** — `feat(fate): F2b — propose_fate_compel narrator tool + pending-compel storage`.

## Task 3 — Final verification

- [ ] **Step 1: Lint** — `uv run ruff check` on all changed files.
- [ ] **Step 2: Format check** — `uv run ruff format --check` on the changed set (the ungated trap).
- [ ] **Step 3: Type check** — `uv run pyright` on the changed source; 0 errors.
- [ ] **Step 4: Fate + narrator + tool suites** — `SIDEQUEST_DATABASE_URL=... uv run pytest -n0 -q tests/agents/test_fate_narrator_prompt.py tests/agents/tools/test_propose_fate_compel.py tests/agents/test_narrator_prompt.py tests/agents/test_tool_registry.py tests/agents/test_102_5_wn_tool_narrator_wiring.py tests/telemetry/ -k "fate or prompt or tool"`.
- [ ] **Step 5: Full sweep** — `SIDEQUEST_DATABASE_URL=... SIDEQUEST_GENRE_PACKS=... uv run pytest`; baseline-compare (a failure not in the recorded develop baseline is a regression). Confirm no regression to existing narrator-prompt or tool-availability behavior for non-fate packs.
- [ ] **Step 6: Commit any fixups.**

## 5. Test strategy

- **No source-text wiring tests.** Prove the section by asserting on the **assembled prompt** (present for fate, absent for non-fate); prove the tool by **dispatching through the real registry** and asserting `offer_compel`'s span + the snapshot `PendingCompel`.
- **Gating both ways** — every test pairs a fate-pack assertion with a non-fate-pack negative (the section/tool must not leak into native/WN packs), the same discipline F2a used for `_build_fate_summary`.
- **Volatility/caching** — pin the section to Valley; a test (or assertion) guards it out of the cached/STABLE prefix.

## 6. Open / deferred (flagged, not dropped)

1. **Compel accept/refuse.** F2b proposes + stores `PendingCompel`; the accept path (`ruleset.accept_compel` → +1 fate point) lands with the **F3 UI** surface (ADR-107 aside channel is the natural carrier). Flagged in decomposition §7.2.
2. **Player invoke resolution** already rides F1d/F2a (`FateActionPayload.invoke_aspect`); F2b only surfaces invokability in prose. No duplicate invoke path here.
3. **NPC/opponent aspects in the prompt.** F2b surfaces PC aspects + scene aspects. Whether the narrator should also see opponent character aspects (to invoke against the player) is an F2c/F2d-adjacent question — out of scope here.

## 7. Done when

- A narrator turn in a `ruleset: fate` pack carries a `fate_state` prompt section (aspects, fate points, invokable-aspect directive); a native/WN pack carries none.
- The narrator can call `propose_fate_compel`, firing `fate.compel.offered` and recording a `PendingCompel`, with no fate-point mutation; the tool is absent under non-fate rulesets.
- All gates green; full sweep clean against baseline.
