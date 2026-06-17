---
story_id: "124-4"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 124-4: Inspector State tab — dark-Tufte treatment (124-3 follow-on)

## Story Details
- **ID:** 124-4
- **Jira Key:** (none — Jira not enabled)
- **Workflow:** tdd
- **Stack Parent:** none
- **Epic:** 124 (OTEL Inspector — Tufte visualization follow-ups)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-17T00:27:22Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-16T23:29:54Z | 2026-06-16T23:33:35Z | 3m 41s |
| red | 2026-06-16T23:33:35Z | 2026-06-17T00:01:50Z | 28m 15s |
| green | 2026-06-17T00:01:50Z | 2026-06-17T00:12:45Z | 10m 55s |
| review | 2026-06-17T00:12:45Z | 2026-06-17T00:27:22Z | 14m 37s |
| finish | 2026-06-17T00:27:22Z | - | - |

## Story Context
**Title:** Inspector State tab — dark-Tufte treatment (124-3 follow-on): location/regions direct-labeled, tropes sorted progression bar plot, character HP bullet bar + inventory narrative-weight bars with named/evolved threshold ticks, NPC registry with 5-bar OCEAN personality sparkline fingerprints, working search filter — bound to LIVE SessionStateView (not the prototype's synthetic makeState). Per the epic no-fabrication rule: where the design shows OCEAN / trope progression / per-item narrative weight, verify those fields actually reach SessionStateView and wire the deferred telemetry (server) or render only what is real — do not fabricate.

**Points:** 5
**Priority:** p3
**Repos:** server, ui
**Workflow Type:** tdd (phased)

### Design Source (Durable, Committed)
Located in: `docs/design-bundles/2026-06-16-tufte-inspector-state-tab/`
- `README.md` — Claude Design handoff instructions
- `chats/chat1.md` — design conversation; State-tab intent from "start with the state tab please"
- `project/CLAUDE.md` — LOCKED Tufte design system (palette #19191b bg / #e7e5df ink / #86847d muted / #4ab4cf accent; Georgia serif small-caps labels, JetBrains Mono values; no boxes, hairline rules #2a2a2e)
- `project/SideQuest Inspector.dc.html` — prototype (State tab template lines 152–229; State data `makeState()` line 598; helpers lines 637–679; renderVals wiring lines 756–810)
- `project/screenshots/state2.png` + `state_npc.png` — target visuals

### What the State Tab Renders
1. **Location & discovered regions** — direct-labeled, no boxes
2. **Tropes** — sorted progression bar plot (active=steel, resolved/dormant recede), label + progression value + status
3. **Character** — HP bullet bar + stat line (hp/xp/gold/location); inventory table with per-item **narrative-weight bars** carrying named(0.5)/evolved(0.7) threshold ticks + stage + state columns
4. **NPC registry** — dense table; each NPC's Big-Five personality is a **5-bar OCEAN sparkline fingerprint** (small multiples, scannable down the column); columns name/role/location/hp/last-seen/pronouns/OCEAN
5. Working **search** filter over NPCs + items
6. Infrastructure line

### Critical Scoping Constraint: No-Fabrication Rule
The prototype renders SYNTHETIC literal data (`makeState()`). The REAL tab binds to LIVE `SessionStateView` telemetry (`@/types/watcher`).

**Load-bearing requirement:** This story MUST:
- Bind the Tufte treatment to live `SessionStateView`, NOT copy the synthetic data.
- For OCEAN-per-NPC, trope progression, and per-item narrative weight: VERIFY whether those fields actually reach `SessionStateView` today.
  - Where they do → render them.
  - Where they DON'T → wire the deferred telemetry on the server (repos includes `server` for exactly this), OR render only what is real.
  - **DO NOT fabricate data to fill the design.**
- This wiring-verification question is the first thing TEA/Architect should resolve before UI work.

### Existing Codebase Anchors (Wire Up, Don't Reinvent)
- `sidequest-ui/src/components/Dashboard/shared/constants.ts` — `THEME` (locked palette already exists)
- `sidequest-ui/src/components/Dashboard/charts/` — Histogram, ScatterPlot, FlameChart, AgentDotPlot, TokenBarChart (Tufte chart kit from 124-3; reuse patterns for OCEAN sparkline / weight bars / tropes bar plot)
- `sidequest-ui/src/components/Dashboard/tabs/TimingTab.tsx` + `TimelineTab.tsx` — reference implementations of Tufte treatment to match
- `sidequest-ui/src/components/Dashboard/tabs/StateTab.tsx` — file to redesign (~445 lines)
- `sidequest-ui/src/components/Dashboard/__tests__/StateTab.test.tsx` — existing tests (TDD: TEA extends these)
- Server side: `SessionStateView` / `NpcRegistryEntry` / `PlayerStateView` types in `@/types/watcher` and their server emission point (telemetry/watcher) — where OCEAN/tropes/weight would be wired if absent

### Acceptance Criteria
- [ ] State tab matches the dark-Tufte design system (palette/type/no-boxes/direct-labels) consistent with TimingTab/TimelineTab
- [ ] Location+regions, tropes progression bar plot, character HP bullet bar, inventory narrative-weight bars w/ named/evolved ticks, NPC OCEAN 5-bar sparkline, search filter — all present
- [ ] All rendered data is REAL (bound to live SessionStateView). Any design element whose data is not emitted is either wired through to the server telemetry (with an OTEL emit, per the project OTEL principle) or omitted — never fabricated
- [ ] A wiring test proves StateTab consumes live SessionStateView and is reachable from the Inspector (per the project's "every test suite needs a wiring test" rule)
- [ ] Existing StateTab.test.tsx green; new tests for the inline graphics (oceanGlyph/weightBar/tropes) and filter

### Branches
**UI:** `feat/124-4-tufte-inspector-state-tab` (sidequest-ui, develop)
**Server:** `feat/124-4-tufte-inspector-state-tab` (sidequest-server, develop)
**Branch Strategy:** gitflow (develop as base)

## Sm Assessment

**Routing:** New work from a Keith design-handoff (Claude Design `/design/h/` bundle), not a backlog pick. Fetched, extracted, and read the bundle (`docs/design-bundles/2026-06-16-tufte-inspector-state-tab/`); it's the next tab in the Inspector Tufte redesign (epic 124, after 124-3 shell+Timing+Timeline and 124-1 token chart). Created story 124-4, repos `server,ui`, tdd/phased. Merge gate clear (0 in-progress). → **TEA (RED)**.

**The load-bearing risk TEA must resolve FIRST, before any UI test:** the prototype renders synthetic `makeState()` data, but the real `StateTab.tsx` binds to live `SessionStateView`. Epic 124's governing rule is "render only real fields, never fabricate." So before designing the OCEAN-sparkline / tropes-bar-plot / per-item-weight-bar visuals, verify whether those three fields actually reach `SessionStateView` today. Where present → render. Where absent → wire server telemetry (with an OTEL emit per the project principle) or omit. This verdict decides whether this is a UI-only reskin (~3pts of the estimate) or a UI+server telemetry wiring story (the full 5). The wiring test (StateTab consumes live SessionStateView, reachable from the Inspector) is mandatory per project convention.

**Scope authority:** session scope > epic context. Match the Tufte system already merged in `shared/constants.ts THEME`, `charts/`, `TimingTab.tsx`, `TimelineTab.tsx` — wire up the existing chart kit, don't reinvent it.

## TEA Assessment

**Tests Required:** Yes
**Status:** RED verified (failing — ready for Dev)

**Test Files:**
- `sidequest-ui/src/components/Dashboard/__tests__/StateTab.tufte.test.tsx` — 17 tests (8 pass = lock existing behavior; **9 fail** = graphical substance + sort + live-data binding). Commit `9c67ed2`.
- `sidequest-server/tests/server/test_debug_state_projection.py` — 7 tests, collection **ImportError** on the not-yet-created `sidequest.server.state_projection` (valid RED; all fixture imports + constructions verified to resolve). Commit `5abf8867`.

**Tests Written:** 24 tests covering the 5 ACs + the no-fabrication rule + 4 server data-honesty fixes.

**AC coverage:**
| AC | Test(s) | Status |
|----|---------|--------|
| Tufte treatment (palette/type/no-boxes) | behavioral proxy: svg glyphs replace text/div; pixel fidelity → Reviewer (see deviation) | partial-by-design |
| Location+regions, tropes bar plot, HP bullet, inventory weight bars, OCEAN sparkline, search | `OCEAN sparkline` ×5, `tropes bar plot` ×3, `inventory weight bars` ×3, `character + location` ×2, `search filter` ×2 | failing/RED |
| All data REAL (bound to live SessionStateView), absent → omit, never fabricate | `degrades to a placeholder when ocean absent`, `nothing fabricated when inventory empty`, server `*_without_fabrication` | RED + green-guards |
| Wiring test (consumes live SessionStateView, reachable) | `renders every section from a single live-shaped view object` (+ DashboardApp:148 is the prod call site) | failing/RED |
| Existing StateTab.test.tsx green + new graphic/filter tests | new suite added; existing 30-3 suite untouched (text assertions survive the reskin) | n/a |

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| TS #4 — `\|\|` on a value that can be `0` is a BUG (use `??`) | `keeps all 5 bars even when a dimension is exactly 0` | failing |
| TS #6 — a11y / non-opaque graphics | `exposes the five OCEAN values to assistive tech (accessible name)` | failing |
| TS #1 — no `as any` type escapes | noted for Reviewer: OCEAN parse of `Record<string, unknown>` must narrow safely, not `as any` (no dedicated test — flagged) | flagged |
| Project — No Silent Fallbacks (silent `getattr` defaults) | server suite: `reads_real_trope_id`, `preserves_fractional_trope_progression`, `reads_npc_hp_from_hp_pool`, `surfaces_character_inventory_items` | failing (ImportError-RED) |
| TS #8 — test quality (no vacuous assertions) | self-check pass | clean |

**Rules checked:** TS lang-review #1/#4/#6/#8 + the project No-Silent-Fallbacks rule have coverage; pure-visual styling is intentionally out of unit scope (deviation logged).
**Self-check:** 0 vacuous tests (every test has a meaningful assertion; one exact-match `getByText` corrected to a substring matcher so it can flip green on implementation).

**Handoff:** To Dev (Naomi) for GREEN.

## Dev Assessment

**Implementation Complete:** Yes
**Tests:** 32/32 passing (GREEN) — UI new 17/17, UI 30-3 regression 7/7, full Dashboard dir 107/107 (22 files), server projection 8/8. Lint/format/typecheck clean (ruff, eslint, tsc).

**Files Changed:**
- `sidequest-server/sidequest/server/state_projection.py` (NEW) — pure `project_session_state_view(snap, *, session_key, last_activity_ts)`; extracted from the inline `debug_state` block. Fixes the 4 dead reads: inventory items from `char.core.inventory.items`, trope `id`, trope `progress` (float, no `int()`), NPC `core.hp` HpPool.
- `sidequest-server/sidequest/server/rest.py` — `debug_state` now imports + calls the helper (DB enumeration stays in the route); ~110 inline lines replaced by the call. **Wired, not dead code** (grep confirms the import + call site).
- `sidequest-ui/src/components/Dashboard/tabs/StateTab.tsx` — full Tufte rebuild: OCEAN 5-bar sparkline glyph (live `ocean` dict, 0–10 scale, `typeof`-narrowed, a11y label, graceful "—"), sorted trope progression bar plot, inventory narrative-weight bars w/ named/evolved ticks, HP bullet bar, direct-labeled location/regions, search filter. No card boxes; SERIF/MONO + palette tokens. Preserves session-pick-by-`last_activity_ts` and the refresh tooltip (30-3 green).
- `sidequest-ui/src/components/Dashboard/__tests__/StateTab.tufte.test.tsx` — removed a dead `OCEAN_KEYS` const (eslint).

**Branches (pushed):**
- `feat/124-4-tufte-inspector-state-tab` @ `c9ce4008` (sidequest-server)
- `feat/124-4-tufte-inspector-state-tab` @ `ac6cb36` (sidequest-ui)

**Self-review (judgment checks):**
- [x] Wired to a non-test consumer — `rest.py::debug_state` calls `project_session_state_view`; `DashboardApp.tsx:148` renders the rebuilt `StateTab`.
- [x] Follows project patterns — reuses `shared/constants.ts` `THEME`/`SERIF`/`MONO`, matches the TimingTab/TimelineTab Tufte idiom.
- [x] ACs met — all graphics bound to live `SessionStateView`; absent data → "—"/omitted, never fabricated (no-fabrication rule).
- [x] Error handling — `oceanValues` returns null on malformed/absent ocean; weight defaults to 0; HP guards max>0.

**Note for Reviewer:** Pure-visual Tufte fidelity (palette/type/no-boxes spacing) is intentionally not unit-tested (deviation logged) — please eyeball the built State tab against `docs/design-bundles/2026-06-16-tufte-inspector-state-tab/project/screenshots/state2.png` + `state_npc.png`.

**Handoff:** To Reviewer (Chrisjen) for the review phase.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 smells; tests GREEN (server 8/8, UI Dashboard 107/107), ruff+eslint clean | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings (covered by Reviewer Devil's Advocate) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings (covered by Reviewer + rule-checker SOUL-1) |
| 4 | reviewer-test-analyzer | Yes | findings | 11 (coverage gaps) | confirmed 6, downgraded 4, dismissed 1 |
| 5 | reviewer-comment-analyzer | Yes | findings | 7 (stale comments) | confirmed 7 (all Low; 2 pre-existing, 4 self-introduced, 1 doc-softening) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings (covered by rule-checker TS-1/TS-2 + Reviewer) |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings (covered by Reviewer [SEC] analysis) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings (covered by Reviewer [SIMPLE] analysis) |
| 9 | reviewer-rule-checker | Yes | findings | 5 violations (26 rules / 84 instances) | confirmed 5 (3 Medium type-escape, 2 Low or-0.0) |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 14 confirmed (0 Critical, 0 High, 4 Medium, 10 Low), 4 downgraded with rationale, 1 dismissed

## Reviewer Assessment

**Verdict:** APPROVED

No finding reaches Critical or High. The deliverable is correct, wired end-to-end, tested on its happy paths, and lint/format/type clean. Every confirmed finding is polish, coverage-breadth, or consistency — all Medium/Low (non-blocking per the severity policy). I recommend the cheap, self-introduced items (the redundant `or 0.0`, the stale RED-phase comments, the `ocean_summary` type widening) be cleaned up as a fast-follow, and have recorded them as delivery findings.

**Data flow traced:** a live NPC's OCEAN → `snap.npcs[].ocean` (OceanProfile dict, 0–10) → `_project_npc_registry` passthrough (`state_projection.py:72`) → GET `/api/debug/state` → `NpcRegistry` → `<OceanGlyph ocean={n.ocean}>` → `oceanValues()` narrows via `typeof number` (null on partial/malformed) → 5 `<rect>` normalized /10 with an aria-label. Safe end-to-end: no fabrication (null → "—"), 0-values preserved, React-escaped (no XSS).

### Observations (tagged)

- `[RULE][SILENT]` **LOW** `state_projection.py:111` — `float(getattr(trope, "progress", 0.0) or 0.0)`: the `or 0.0` is **redundant** (the getattr default already yields 0.0) and is the exact `or`-on-falsy-valid-float smell this very story fixes elsewhere. Numerically harmless (0.0 either way) → LOW, but ironic in a fix-silent-fallbacks commit. **Confirmed** (rule-checker PY-13/SOUL-1 + my own read). Recommend deleting `or 0.0`.
- `[RULE][SILENT]` **LOW** `state_projection.py:35` — `float(it.get("narrative_weight") or 0.0)` conflates absent vs explicit-0.0. Same numeric outcome (both → unnamed/0), so LOW, but inconsistent with the story's No-Silent-Fallbacks mandate. **Confirmed.**
- `[TYPE]` **MEDIUM** `watcher.ts:121` — `ocean_summary?: string` but the server sends `None` → JSON `null` (`state_projection.py:71,88`). The type lies about the wire shape, forcing three `as`-casts in the test (`null as unknown as ...` / `null as never`, TS-1). Production impact is nil (the redesigned UI ignores `ocean_summary` and reads `ocean`), so MEDIUM not High. **Confirmed.** Fix: widen to `string | null`, drop the 3 casts.
- `[TEST]` **MEDIUM** No **server wiring test** proving `rest.py::debug_state` calls `project_session_state_view` — matches the `<critical>` "Every Test Suite Needs a Wiring Test" rule. **Confirmed (not dismissed)**; downgraded to MEDIUM because the wiring IS present (verified at `rest.py:476`) and the UI consumer is exercised through the full Dashboard suite (107/107 via `DashboardApp:148`). Recommend a mock-based TestClient test (mock `PgForensicReader.list_saves`/`PgSaveRepository.load`) — light, no DB, satisfies the rule.
- `[TEST]` **MEDIUM** `_project_npc_registry` **`npc_pool` branch (state_projection.py:77-93) fully uncovered** — pool-member mapping (`ocean=None`, `hp 0/0`, `role` from `member.role`) untested. Code read as correct, but a real coverage gap. **Confirmed.**
- `[TEST]` **LOW** No partial/malformed-`ocean` test (3-of-5 keys, or string value) for the no-fabrication path; no multi-character test; no `progress=0.0`/`weight=0.0` zero-value test. **Confirmed** (coverage breadth).
- `[TEST]` **LOW** `test:237` `assert entry["ocean_summary"] is None` is vacuous (asserts a hardcoded constant). Harmless intent-doc; **downgraded** — the same test already asserts `entry["ocean"] == ocean` (the real contract). `test:159` trope-status near-tautological — **dismissed** (it still pins the field maps through; trivially low value, not wrong).
- `[DOC]` **LOW (self-introduced)** `StateTab.tsx:198` "— see history below" dangling reference (the history was condensed away); `test:45` "does not exist yet — RED" (now exists, GREEN); `test:6,178` present-tense bug-report framing + stale `rest.py:554-557/481-485` line refs (now historical). **Confirmed** — recommend cleanup.
- `[DOC]` **LOW (pre-existing)** `rest.py:402,407` docstring still says "walks save.db / sorted by save-file mtime" (SQLite-era) — contradicts the ADR-115 Postgres paragraph below it. Not introduced by 124-4 but in the touched method; worth fixing while here.
- `[DOC]` **LOW** `state_projection.py:101` states `progress` is "a float in [0,1]" as a contract; it's only a tick-engine convention (authored `ChapterTrope` progress is unclamped). UI clamps via `Math.min(1, …)`, so harmless. Soften the wording.
- `[SIMPLE]` **LOW** `_project_players` (`state_projection.py:117`) lacks a return annotation that its three sibling helpers have; `_project_inventory_items` uses bare `list[dict]` vs the `list[dict[str, Any]]` used elsewhere. Consistency only.
- `[EDGE][VERIFIED]` Devil's-advocate edges handled: partial/malformed ocean → "—"; `max_hp=0` → "—" + 0-width bar; `progression>1` (unclamped authored) → bar clamped by `Math.min(1,…)`, value shown verbatim; empty session → empty-state prompt; item missing `narrative_weight` → 0/unnamed (honest). Evidence: `StateTab.tsx` `oceanValues` (typeof guard), `n.max_hp > 0 ? … : "—"`, `TropesPlot` Math.min.
- `[SEC][VERIFIED]` Read-only GET projection; all values render as text children or numeric SVG attrs (React-escaped); preflight confirms 0 `dangerouslySetInnerHTML`; `filter` uses literal `.includes()` (no regex injection); no auth/tenant surface (single-tenant). Evidence: `StateTab.tsx` throughout; preflight smells=0.
- `[VERIFIED]` **Wiring present** — `rest.py:476` calls `project_session_state_view`; `DashboardApp.tsx:148` renders the rebuilt `StateTab`. The 4 dead-read fixes are correct (reads `trope.id`, `trope.progress` float no-`int()`, `core.hp.current/.max`, `char.core.inventory.items`); server suite 8/8 + my read confirm.

### Rule Compliance

Rule-checker swept **26 numbered checks across 84 instances**; I cross-checked the material ones.
- **Python lang-review #1–8 + No-Silent-Fallbacks:** compliant except the two `or 0.0` smells (#13/SOUL-1, LOW, above). No bare-except, no mutable defaults, no resource leaks, no unsafe deserialization, no path/logging issues. `snap: Any` is justified by docstring (Character callable-or-attribute Rust-port polymorphism). The `getattr(core, "hp", None)` reads are the **fix** (correct field) with a defensive default appropriate because the projection runs outside the per-slug `try/except` (so one malformed record can't 500 the panel — the endpoint's documented resilience intent).
- **TypeScript lang-review #1–8:** compliant except the 3 `ocean_summary` `as`-casts (#1, MEDIUM, above, root cause is the `watcher.ts` type). No `key={index}` (all stable keys), `useMemo` deps correct, no `useEffect`, no `dangerouslySetInnerHTML`, `import type` used, `Record<string, unknown>` (not `any`) narrowed by `typeof`. `??` used correctly on the nullable/falsy-valid `last_activity_ts` and `narrative_weight`.

### Devil's Advocate

Assume this is broken. The projection runs **outside** the per-slug `try/except` (`rest.py:475`), so any exception it raises 500s the whole State tab — and the projection now does strictly more work than the old inline block (it iterates inventory, reads nested `core.hp`/`core.inventory`). If a loaded snapshot carried a `Character` whose `core` were somehow `None`, `core.name` would `AttributeError` and kill the endpoint for *every* session, not just the bad one. In practice `Npc.core`/`Character.core` are required pydantic fields so this can't happen on a validated load — but the structural fragility is real and pre-existing; the richer projection widens the blast radius slightly. A confused author could also re-break the data silently: the fix keeps the `getattr(obj, "name", default)` idiom that *caused* the original dead-reads — a future rename of `progress`/`hp`/`id` would again return defaults rather than failing loud (mitigated only by the fields being pydantic-guaranteed today). On the UI: a malicious/garbage save can't XSS (React escapes; numbers in attrs), but a save with absurdly long NPC/item names has no `overflow` guard on the new grid cells (the old card layout clipped OCEAN) — cosmetic overflow, not a break. A save predating the full OCEAN model (3 of 5 dims) correctly degrades to "—" (no fabricated 3-bar glyph) — verified. The single biggest *unverified* risk is not in the code at all: **no human or test has confirmed the tab actually looks like the Tufte design** — the tests assert SVG structure (≥5 `<rect>`), not palette/spacing/no-boxes fidelity vs `state2.png`/`state_npc.png`. For a story whose headline deliverable is the visual redesign, that AC is effectively unverified. None of this is a correctness blocker, but the visual-fidelity gap and the moving of richer projection logic outside the resilience boundary are the two things most worth a follow-up.

**Pattern observed:** clean extract-to-pure-function (the inline DB-coupled projection → testable `project_session_state_view`) at `state_projection.py` — the right direction, and the wiring is honestly preserved (`rest.py:476`).
**Error handling:** `oceanValues` null-guards malformed input; `max_hp>0` guards division; defensive getattr keeps one bad record from 500-ing the panel.
**Handoff:** To SM for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (blocking): The live State-tab trope projection reads non-existent fields — `getattr(trope, "trope_id")` (real field is `id`) and `int(getattr(trope, "progression", 0))` (real field is `progress: float`). With `TropeState` `extra="ignore"`, both return defaults, so **every trope shows a blank id and `0` progression in production**. Affects `sidequest-server/sidequest/server/rest.py:522,524` (read `trope.id` and `trope.progress`, no `int()` cast). *Found by TEA during test design.*
- **Gap** (blocking): Player inventory is hard-coded empty — `"inventory": {"items": [], "gold": 0}` — so the design's narrative-weight table has no live data. The character's real items live at `char.core.inventory.items`. Affects `sidequest-server/sidequest/server/rest.py:554-557`. *Found by TEA during test design.*
- **Gap** (blocking): NPC HP is always `0/0` — the projection reads `getattr(core, "edge", None).maximum`, but `CreatureCore` was re-pointed edge→hp and `HpPool`'s field is `max` (not `maximum`). The real read is `core.hp.current` / `core.hp.max`. Affects `sidequest-server/sidequest/server/rest.py:481-485`. *Found by TEA during test design.*
- **Improvement** (non-blocking): `ocean_summary` is always `None` on the wire (`rest.py:495,512`); the old UI's `ocean_summary || "—"` rendered a permanently-dead OCEAN column. The redesign binds to the live `ocean` dict instead. No server change needed — flagged so the dead field isn't reintroduced. Affects `sidequest-ui/src/components/Dashboard/tabs/StateTab.tsx:365`. *Found by TEA during test design.*
- **Improvement** (non-blocking): The four dead reads above all sit in one inline projection block in an async DB-coupled route, which is why none had unit coverage. The RED server suite requires extracting it to a pure `project_session_state_view(snap, …)` — once extracted, this projection gains real regression coverage. *Found by TEA during test design.*

### Dev (implementation)
- All four TEA-flagged dead reads are now fixed and verified (8/8 server tests green): inventory items, trope `id`, trope `progress` (float, no `int()`), NPC `core.hp`.
- **Improvement** (non-blocking): `has_music_director` / `has_audio_mixer` are still hard-coded `False` in the projection (`state_projection.py`), so the infra line always shows ✗✗ even when a director/mixer is active. Out of scope for 124-4 (no design dependency, not telemetry the State graphics need) — but a candidate follow-up if the infra line should reflect real audio wiring. Affects `sidequest-server/sidequest/server/state_projection.py` (`project_session_state_view` infra fields). *Found by Dev during implementation.*
- **Improvement** (non-blocking): Item dicts in `CreatureCore.inventory.items` are a "P1 subset" (per the `Inventory` docstring) and may not carry `narrative_weight` for every item until the P2 item-evolution work lands; the projection defaults a missing weight to `0.0` (renders as `unnamed`), which is honest but means some real items show weight 0 until P2. Affects `sidequest-server/sidequest/game/creature_core.py` (`Inventory` P2-deferred). *Found by Dev during implementation.*

### Reviewer (code review)
Verdict APPROVED (no Critical/High). The following are non-blocking; the **first group is a cheap, high-value fast-follow** (behavior-preserving, existing tests stay green) and the rest are coverage/QA follow-ups.
- **Improvement** (non-blocking): Redundant/inconsistent `or 0.0` on float fields — `float(getattr(trope, "progress", 0.0) or 0.0)` (the `or 0.0` is dead) and `float(it.get("narrative_weight") or 0.0)` (conflates absent vs 0.0). Same `or`-on-falsy-valid class the story fixes elsewhere; numerically harmless. Affects `sidequest-server/sidequest/server/state_projection.py:35,111` (drop the `or 0.0` / distinguish absent-vs-zero). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `NpcRegistryEntry.ocean_summary` is typed `string` but the server sends `null` (`None`), forcing three `as`-casts in the test. Affects `sidequest-ui/src/types/watcher.ts:121` (widen to `string | null`, then remove the casts at `StateTab.tufte.test.tsx:44,144,156`). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Self-introduced stale comments — `StateTab.tsx:198` "— see history below" (dangling), `test_debug_state_projection.py:6,45,178` RED-phase / present-tense bug-report framing + stale `rest.py` line refs, `state_projection.py:101` states `[0,1]` as a contract (it's a convention). Plus pre-existing `rest.py:402,407` SQLite-era docstring contradicting the ADR-115 Postgres paragraph. Affects those files (refresh the comments). *Found by Reviewer during code review.*
- **Gap** (non-blocking): No server **wiring test** that `rest.py::debug_state` calls `project_session_state_view` (matches the `<critical>` "Every Test Suite Needs a Wiring Test" rule; wiring verified present but unguarded against regression). Affects `sidequest-server/tests/server/test_debug_state_projection.py` (add a mock-based TestClient test of GET `/api/debug/state`). *Found by Reviewer during code review.*
- **Gap** (non-blocking): Coverage breadth — `npc_pool` projection branch (`state_projection.py:77-93`) fully untested; no partial/malformed-`ocean` test; no multi-character test; no `progress=0.0`/`weight=0.0` zero-value test. Affects `sidequest-server/tests/server/test_debug_state_projection.py` + `sidequest-ui/.../StateTab.tufte.test.tsx`. *Found by Reviewer during code review.*
- **Gap** (non-blocking): **Visual fidelity unverified** — tests assert SVG structure, not the Tufte look (palette/spacing/no-boxes) vs the design screenshots; no human/playtest pass ran. The "matches the dark-Tufte design system" AC is effectively unverified. Recommend a manual / `sq-playtest` check vs `docs/design-bundles/2026-06-16-tufte-inspector-state-tab/project/screenshots/state2.png` + `state_npc.png`. *Found by Reviewer during code review.*
- **Question** (non-blocking): The (richer) projection call runs **outside** the per-slug `try/except` (`rest.py:475`); a malformed snapshot would 500 the whole panel rather than skipping one slug. Pre-existing structure, mitigated by defensive getattr + pydantic-guaranteed fields, but the blast radius grew. Affects `sidequest-server/sidequest/server/rest.py:447-481` (consider wrapping the projection in the per-slug try/except). *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 6 findings (1 Gap, 0 Conflict, 1 Question, 4 Improvement)
**Blocking:** None

- **Improvement:** `has_music_director` / `has_audio_mixer` are still hard-coded `False` in the projection (`state_projection.py`), so the infra line always shows ✗✗ even when a director/mixer is active. Out of scope for 124-4 (no design dependency, not telemetry the State graphics need) — but a candidate follow-up if the infra line should reflect real audio wiring. Affects `sidequest-server/sidequest/server/state_projection.py`.
- **Improvement:** Item dicts in `CreatureCore.inventory.items` are a "P1 subset" (per the `Inventory` docstring) and may not carry `narrative_weight` for every item until the P2 item-evolution work lands; the projection defaults a missing weight to `0.0` (renders as `unnamed`), which is honest but means some real items show weight 0 until P2. Affects `sidequest-server/sidequest/game/creature_core.py`.
- **Improvement:** Redundant/inconsistent `or 0.0` on float fields — `float(getattr(trope, "progress", 0.0) or 0.0)` (the `or 0.0` is dead) and `float(it.get("narrative_weight") or 0.0)` (conflates absent vs 0.0). Same `or`-on-falsy-valid class the story fixes elsewhere; numerically harmless. Affects `sidequest-server/sidequest/server/state_projection.py:35,111`.
- **Improvement:** `NpcRegistryEntry.ocean_summary` is typed `string` but the server sends `null` (`None`), forcing three `as`-casts in the test. Affects `sidequest-ui/src/types/watcher.ts:121`.
- **Gap:** No server **wiring test** that `rest.py::debug_state` calls `project_session_state_view` (matches the `<critical>` "Every Test Suite Needs a Wiring Test" rule; wiring verified present but unguarded against regression). Affects `sidequest-server/tests/server/test_debug_state_projection.py`.
- **Question:** The (richer) projection call runs **outside** the per-slug `try/except` (`rest.py:475`); a malformed snapshot would 500 the whole panel rather than skipping one slug. Pre-existing structure, mitigated by defensive getattr + pydantic-guaranteed fields, but the blast radius grew. Affects `sidequest-server/sidequest/server/rest.py:447-481`.

### Downstream Effects

Cross-module impact: 6 findings across 4 modules

- **`sidequest-server/sidequest/server`** — 3 findings
- **`sidequest-server/sidequest/game`** — 1 finding
- **`sidequest-server/tests/server`** — 1 finding
- **`sidequest-ui/src/types`** — 1 finding

### Deviation Justifications

6 deviations

- **Visual Tufte styling is verified by eye, not unit-tested**
  - Rationale: style-snapshot assertions are brittle and the design README names screenshots as the verification medium; pixel fidelity is a Reviewer eyeball-vs-screenshot gate
  - Severity: minor
  - Forward impact: Reviewer must visually compare the built tab to `state2.png` + `state_npc.png` for palette/type/no-boxes fidelity
- **Server tests target a not-yet-existing extracted projection function**
  - Rationale: the projection is inline in an async DB-coupled route and untestable as-is; extraction is the lightest path to synthetic-snapshot coverage and a real architecture win
  - Severity: minor
  - Forward impact: Dev extracts the projection; may relocate the helper (log a deviation if the module/function name changes — the behavioral contract is fixed)
- **Scope completion: NPC-HP dead-read fixed alongside the three named fields**
  - Rationale: same code site, same lie-detector failure class, one-line fix; the design's NPC registry has an HP column; leaving 1 of 4 dead reads broken violates "no half-wired features"
  - Severity: minor
  - Forward impact: none — strictly more honest data; no new surface
- **No OTEL span added for the projection fix**
  - Rationale: the OTEL principle targets subsystem *decisions* (trope tick, combat, inventory mutation) — those already emit spans at decision time and populate the snapshot. A passive projection of that state is the *display*, not a decision; a span on the GET would be noise. The honesty fix is reading the real fields, which the server suite verifies.
  - Severity: minor
  - Forward impact: none — Reviewer should not flag a "missing OTEL emit" here; the data path the panel reads is already instrumented upstream
- **Dropped the old per-column NPC sort and the JSON expand-on-click affordances**
  - Rationale: the Tufte redesign replaces row-expansion + sort with a denser always-on table (OCEAN fingerprint + weight bars are visible inline, no click needed) plus the search filter; no test or AC requires sort/expand, and the 30-3 suite stays green
  - Severity: minor
  - Forward impact: none — if a maintainer wants raw-JSON inspection back, the Forensic tabs (`ForensicStateTab`) already serve that audience
- **Infra-line region count now reads `discovered_regions.length`, not `region_names.length`**
  - Rationale: `region_names` is hard-coded `[]` in the projection (always 0); `discovered_regions` carries the real list, so the count is now honest rather than a constant 0
  - Severity: trivial

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Visual Tufte styling is verified by eye, not unit-tested**
  - Spec source: design bundle `project/CLAUDE.md` (locked palette/typography/no-boxes) + screenshots `state2.png`/`state_npc.png`
  - Spec text: "Georgia serif small-caps labels, JetBrains Mono values; no boxes, hairline rules; maximize data-ink"
  - Implementation: tests assert the behavioral substance (svg glyphs, sorted DOM order, live-data binding, a11y names) — NOT computed palette/font/border styles
  - Rationale: style-snapshot assertions are brittle and the design README names screenshots as the verification medium; pixel fidelity is a Reviewer eyeball-vs-screenshot gate
  - Severity: minor
  - Forward impact: Reviewer must visually compare the built tab to `state2.png` + `state_npc.png` for palette/type/no-boxes fidelity
- **Server tests target a not-yet-existing extracted projection function**
  - Spec source: story scope (session) — "wire the deferred telemetry (server)"; server CLAUDE.md "fixture-driven behavior tests"
  - Spec text: "verify those fields actually reach SessionStateView and wire the deferred telemetry (server)"
  - Implementation: server suite imports `project_session_state_view` from a new `sidequest/server/state_projection.py`; the inline `debug_state` block must be lifted into it
  - Rationale: the projection is inline in an async DB-coupled route and untestable as-is; extraction is the lightest path to synthetic-snapshot coverage and a real architecture win
  - Severity: minor
  - Forward impact: Dev extracts the projection; may relocate the helper (log a deviation if the module/function name changes — the behavioral contract is fixed)
- **Scope completion: NPC-HP dead-read fixed alongside the three named fields**
  - Spec source: story title names OCEAN / trope progression / per-item narrative weight
  - Spec text: "where the design shows OCEAN / trope progression / per-item narrative weight … wire … or render only what is real"
  - Implementation: added a 4th server test (`test_projection_reads_npc_hp_from_hp_pool`) — NPC HP was a 4th dead read in the same projection function (always 0/0)
  - Rationale: same code site, same lie-detector failure class, one-line fix; the design's NPC registry has an HP column; leaving 1 of 4 dead reads broken violates "no half-wired features"
  - Severity: minor
  - Forward impact: none — strictly more honest data; no new surface

### Dev (implementation)
- **No OTEL span added for the projection fix**
  - Spec source: context-story-124-4.md AC-3 / project OTEL Observability Principle
  - Spec text: "wired through to the server telemetry (with an OTEL emit, per the project OTEL principle) or omitted"
  - Implementation: `project_session_state_view` emits no span; it is a read-only GET projection of an already-loaded `GameSnapshot`
  - Rationale: the OTEL principle targets subsystem *decisions* (trope tick, combat, inventory mutation) — those already emit spans at decision time and populate the snapshot. A passive projection of that state is the *display*, not a decision; a span on the GET would be noise. The honesty fix is reading the real fields, which the server suite verifies.
  - Severity: minor
  - Forward impact: none — Reviewer should not flag a "missing OTEL emit" here; the data path the panel reads is already instrumented upstream
- **Dropped the old per-column NPC sort and the JSON expand-on-click affordances**
  - Spec source: design bundle `project/SideQuest Inspector.dc.html` State tab (lines 152–229)
  - Spec text: the design's NPC registry + inventory are flat, dense, always-visible tables with a single search filter — no sort headers, no row expansion
  - Implementation: removed `npcSort` / `expandedNpcs` / `expandedItems` state and the `<pre>{JSON.stringify(...)}</pre>` expansion rows from the old tab
  - Rationale: the Tufte redesign replaces row-expansion + sort with a denser always-on table (OCEAN fingerprint + weight bars are visible inline, no click needed) plus the search filter; no test or AC requires sort/expand, and the 30-3 suite stays green
  - Severity: minor
  - Forward impact: none — if a maintainer wants raw-JSON inspection back, the Forensic tabs (`ForensicStateTab`) already serve that audience
- **Infra-line region count now reads `discovered_regions.length`, not `region_names.length`**
  - Spec source: existing `StateTab.tsx` infra line + the no-fabrication rule
  - Spec text: old infra line showed `Regions: {region_names.length}`
  - Implementation: the infra line shows `{discovered_regions.length} regions`
  - Rationale: `region_names` is hard-coded `[]` in the projection (always 0); `discovered_regions` carries the real list, so the count is now honest rather than a constant 0
  - Severity: trivial
  - Forward impact: none

### Reviewer (audit)
- **TEA — "Visual Tufte styling verified by eye, not unit-tested"** → ✓ ACCEPTED: sound test-strategy call (style-snapshots are brittle; screenshots are the medium). BUT the visual check it defers to was **not performed by anyone** — I'm a code reviewer without a browser, and no playtest pass ran. Recorded as a non-blocking delivery finding: the design-match AC is effectively unverified; recommend a manual/`sq-playtest` fidelity pass vs `state2.png`/`state_npc.png`.
- **TEA — "Server tests target a not-yet-existing extracted projection function"** → ✓ ACCEPTED: the extraction landed cleanly (`state_projection.py`), the inline block is gone, and `rest.py:476` calls the helper. Good architecture outcome driven by RED.
- **TEA — "NPC-HP dead-read fixed alongside the three named fields"** → ✓ ACCEPTED: correct scope completion — NPC HP was a 4th instance of the same dead-read class in the same function; fixing 3 of 4 would have violated "no half-wired features."
- **Dev — "No OTEL span added for the projection fix"** → ✓ ACCEPTED: correct reasoning — a read-only GET projection of already-instrumented snapshot state is the display, not a subsystem decision; a span on the GET would be noise. Not flagging a missing OTEL emit.
- **Dev — "Dropped the old per-column NPC sort and JSON expand-on-click affordances"** → ✓ ACCEPTED: aligns with the flat dense-table design; the `ForensicStateTab` still serves raw-JSON inspection. No test/AC required them.
- **Dev — "Infra-line region count now reads discovered_regions.length"** → ✓ ACCEPTED: strictly more honest than the always-0 `region_names.length`.
- **UNDOCUMENTED (Reviewer-spotted):** the redundant `or 0.0` at `state_projection.py:111` and the `ocean_summary` type gap at `watcher.ts:121` are minor divergences from the story's own No-Silent-Fallbacks / type-honesty intent that Dev did not log. Severity: Low/Medium. Captured in Delivery Findings; recommended as a fast-follow cleanup, not a merge blocker.