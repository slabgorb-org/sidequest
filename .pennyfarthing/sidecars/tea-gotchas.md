## TEA Gotchas

### Read the TARGET SOURCE before writing any RED test — an already-present implementation citing the story number means it already shipped via a parallel clone (126-10, 2026-06-18)
- 126-10 (trim `build_fate_projection` for the Fate router prompt) came to RED looking like normal p2 work. But the *first* thing I did was read the injection site (`sidequest/server/intent_router_pass.py`) and the projection module (`sidequest/game/ruleset/fate_projection.py`) — and BOTH already contained the fix: `trim_fate_projection_for_router()` + `_ROUTER_DROP_KEYS = ("character_aspects","scene_aspects")`, wired into the `ruleset=="fate"` branch (lines 376–392) with a dedicated `intent_router_fate_vocabulary_span` OTEL emit. The docstrings literally said *"Story 126-10."* That is the loudest possible tell that the work is done.
- **Confirmed it wasn't my own stale state:** `git log --all | grep 126-10` → one commit `2a704e38 feat(126-10): … (#946)`; `gh pr view 946 --json state,mergedAt` → **MERGED 10:17Z** (this clone's SM picked the story from `backlog` ~12:30Z); `git rev-list --count origin/develop..HEAD` → **0** (branch had no commits beyond develop, fix is an ancestor of HEAD). A parallel oq clone shipped it; only the sprint tracker on this clone still said `backlog`. Second occurrence of this exact pattern (118-8 was 2026-06-15) — it is systemic, not a fluke. See [[project_backlog_story_already_shipped]].
- **What to do instead of authoring RED tests you can't make fail:** verify the *existing* tests are GREEN and that they include the coverage a paranoid RED phase would have demanded, then close via SM finish. Here testing-runner returned 18/18 GREEN across `tests/game/ruleset/test_fate_projection.py` (trim contract + narrator-untouched invariant) and `tests/server/test_fate_classifier_enrichment.py` — the latter carrying the **wiring** test (`test_pre_narrator_pass_ships_trimmed_fate_block`), the **OTEL evidence** test (`test_fate_vocabulary_span_fires_with_trim_evidence`), and the **non-Fate isolation** test (`test_router_omits_fate_block_for_non_fate_pack`). Writing redundant tests, or worse hand-routing to Dev for a no-op GREEN, both manufacture work that doesn't exist.
- **Don't auto-progress the TDD phase machine on an already-shipped story.** The normal red→exit hands to Dev (green); that destination is wrong here. Record the finding (Delivery Finding: tracker drift, non-blocking) + a "Tests Required: No — already shipped" TEA Assessment, then escalate to SM for the finish ceremony (`pf sprint story finish` handles `backlog`→`done` and prints "No PR to merge"; the empty feature branch gets deleted after `git checkout develop`).

### Bind synthetic ruleset packs to the REAL production ruleset, not vestigial `dial` — `dial` is bound by no live pack and silently masks binding-specific validation (126-2, 2026-06-18)
- Re-verifying router-driven **table_resolution** poker seating, I copied the existing `tests/server/test_table_resolution_wiring.py` fixture, which builds `RulesConfig(ruleset="dial", ...)`. All 4 tests passed. But **no live pack binds `dial`** (CLAUDE.md: it's the vestigial schema default; every one of the 11 packs binds a Without-Number or Fate ruleset). The live poker table ships in `spaghetti_western`, which binds **`fate`**. Testing under `dial` verified a path production never takes.
- **The tell + the fidelity check:** when a contract runs "under a ruleset," grep `genre_packs/*/rules.yaml` for `ruleset:` to find which binding the real feature uses, and bind the synthetic pack to THAT. Here: poker/auction → `fate` (spaghetti_western, tea_and_murder); war_rig_crew → `cwn` (road_warrior).
- **What it exposed:** flipping the fixture to `ruleset="fate"` first *failed* — but only on `RulesConfig` validation (`ruleset 'fate' requires rules.fate (FateConfig …); none authored — no silent default`, ADR-144 F4a), NOT on the engine. Supplying `fate=FateConfig()` (all fields default; the `_validate_fate` model-validator only checks presence-not-None) made all 4 pass. So **`dial` masked a fail-loud binding requirement** the production path enforces. Lesson: a green test under `dial` is not evidence the path works under the real binding — the binding can have its own required-content validators (`_validate_fate`, the swn/cwn/wwn `attribute_map` validators) that `dial` doesn't.
- **Why it was still green under fate (don't over-claim a break):** table resolution is ruleset-agnostic by design — `FateRulesetModule` does NOT override `deal_table`/`resolve_table`; they're concrete on the base `RulesetModule` and delegate to `game/table/engine.py` ("orthogonal to combat resolution — every ruleset inherits it"). So the transient "fails under fate" was a *fixture* gap (missing FateConfig), not an engine regression. Read the ruleset module for an override before concluding a binding changes behavior.
- **Re-verification bugs come back GREEN — that's legitimate, don't manufacture a RED.** 126-2's "card game broken" was downstream of the intent-router blocker fixed in 126-9; the seating engine never regressed. The RED-phase deliverable is then a **regression lock** (passing by design), and the story closes "verified, no fix" off the `tests_fail` gate. Per playtesting cadence (Keith): playtest-fix stories routinely fix the root upstream, so a sibling re-verify lands green — write the lock, document the upstream fix, don't fake a failure.

### Ground a story's ACs against the migration that ACTUALLY SHIPPED, not the title's premise — a "depends on whichever lands" story can be half-void on arrival (119-4 RED, 2026-06-16)
- 119-4's title said "depends on whichever migration lands (119-2 or 119-3)" and named three ACs: (1) swap the static `ANTHROPIC_AUTH_TOKEN` env token for an auto-refreshing `ant auth login` profile + fail loud on expiry; (2) OTEL span tagging credit-vs-PAYG billing pool; (3) monitor the "200 monthly credit + 50.52 prepaid overflow buffer before it silently bills PAYG." If you write tests straight off that, you test **fiction**: 119-2 (static token) never shipped — **119-3 (claude-agent-sdk) did**, and its transport already resolves the host's auto-refreshing OAuth login (no static token exists in that path; `assert_subscription_auth()` *requires* the token UNSET). AND the epic was reframed 2026-06-15: the "Agent SDK credit" was CANCELLED, so there is no $200 credit and no $50.52 buffer, and 119-3 fails loud (no silent PAYG to monitor "before"). ~2 of 3 headline ACs referenced a dead premise.
- **The tell:** the story title predates the epic reframe / the sibling migration that won. Before designing RED, read (a) the epic context's `## Overview` for any "REFRAMED <date>" / "CANCELLED" / "VOID" language, (b) `git log` of the dep to see which mutually-exclusive sibling actually merged (PR #908 = 119-3 here), and (c) the dep's design spec for an explicit "119-N owns X" boundary (the 119-2 spec §6 literally scoped 119-4 as the token-swap — but only *if 119-2 had shipped*). Grep the live code for the AC's named mechanism (`grep auth_path|ratelimit|credit`) — if the thing the AC says to "swap/monitor" isn't there, the premise moved.
- **Don't silently reinterpret — surface the fork to the user, THEN log deviations.** When a money/infra story's ACs are half-void, that's a scope decision the user owns (I used AskUserQuestion: "build the real subset" vs "minimal" vs "re-spec"). After they pick, log each descope/reframe as a 6-field Design Deviation (severity major for a dropped headline AC) and capture the residuals as Delivery Findings. Writing tests against the void premise, OR quietly swapping the AC without telling them, both violate No Silent Fallbacks — applied to your own communication.
- **Watch your OWN option text for unverified claims:** I pitched AC3' as "monitor from the anthropic-ratelimit headers we already capture" — then grep proved we DON'T capture them (`llm_request_span` documents `llm.ratelimit_input_tokens_remaining` but no code populates it; the agent-SDK is a subprocess returning a `ResultMessage`, not HTTP headers). The honest available signal was `ResultMessage.total_cost_usd` (surface as `sdk_reported_cost_usd`). Verify the mechanism exists in code before you offer it as an option.

### A dependency that looks "missing" is usually a STALE LOCAL CHECKOUT — `git fetch` + check `origin/<base>` before you declare it absent (121-2 RED, 2026-06-15)
- 121-2 (F4b) depended on 121-1 (F4a engine spine). It looked entirely absent on the local `sidequest-server` working tree: no `FateConfig` in `genre/models/rules.py`, no `seed_chargen_resources` on `FateRulesetModule`, no `ChargenResources.fate_sheet`, no F4a test file. I (TEA) checked `git log --oneline -8`, local branches, and stash — all came up empty — and wrongly concluded F4a never merged (blamed the `merge_pr` no-op gotcha). **That was wrong.** SM then checked the remote: PR #884 was `MERGED` into `origin/develop` (commit `f527ddb7`); local `develop` was simply **3 commits behind** (0 ahead, 3 behind). A `git pull --ff-only` brought every F4a symbol in. The dependency was satisfied the whole time.
- **The miss:** `git log --all` and `git branch -a` only see refs you've already fetched. A story can merge on GitHub minutes before you look; your local mirror won't show it until you `git fetch`. Checking the working tree proves what YOU have, not what `origin` has.
- **RED precondition check for any story with `depends_on`/"dep live" ACs — do this FIRST, before grepping symbols:** `git fetch origin && git rev-list --left-right --count <base>...origin/<base>` (nonzero "behind" ⇒ pull before judging), then if still unsure `gh pr list --repo <repo> --state all --search "<dep keywords>"` to see if the dep PR merged. Only after you're current should "symbol absent in working tree" mean anything. The fast tell I should have used: `git grep -l "class FateConfig" origin/develop -- <path>` checks the REMOTE ref directly.
- **The real escalation rule still holds, but gate it on being current:** only after confirming you're synced with origin AND the dep symbols are genuinely absent do you record a *blocking* finding and hand back to SM (and even then, don't rebuild the dep from the downstream lane). Don't stop the line on a stale checkout.

### Creation-seed lore links are NOT 1:1 with the PC — filter by choice_label (93-4 RED, 2026-06-10)
- `seed_lore_from_char_creation` (sidequest-server/sidequest/game/lore_seeding.py:206) seeds **one fragment per choice in EVERY scene — including choices the player did NOT pick**, all into one shared per-session `LoreStore` (`_SessionData.lore_store`, default_factory). Fragment id is `lore_char_creation_<scene_id>_<choice_index>` — **not player-scoped**. So "this character's lore" is NOT "all CharacterCreation fragments in the store."
- The only correct per-PC discriminator is the answer the PC actually gave: `fragment.metadata['choice_label'] == Character.creation_answers[].value` (for `kind=="choice"`). That value-match IS the cross-character firewall (AC6 / ADR-104-105 intent) — two PCs answering the same scene differently must not see each other's pick. Build the firewall test by seeding ONE shared store and asserting each PC's surfaced titles ⊆ its own answers.
- `CreationAnswer` (protocol/models.py:403) records the chosen LABEL in `.value`, not the choice_index — so you can't reconstruct the fragment id directly; you match on `choice_label` metadata. Freeform answers have NO seed fragment (seeder only iterates `scene.choices`) — a freeform miss must NOT warn; only an unresolvable CHOICE answer is the loud-skip case.
- OTEL emit pattern for sheet-build: chargen already does `_watcher_publish("lore_retrieval", {...}, component="rag")` at chargen_mixin.py:1467. For a sync emit captured in an async test, use the `tests/integration/test_lore_wiring.py` harness: `watcher_hub.bind_loop(get_running_loop())` + clear `_subscribers` + `subscribe(_Sock())`, drive the sync `party_member_from_character`, `await asyncio.sleep(0.05)`, then filter `captured`.

### Orbital intent error seam is incomplete server-side (found in 98-3 RED, 2026-06-09)
- `OrbitalIntentHandler.handle` (sidequest-server/sidequest/handlers/orbital_intent.py) catches only `OrbitalContentUnavailableError` (→ ERROR code `orbital_unavailable`). The 98-2 fail-loud `OrbitalContentMissingError` (orbital/loader.py — unauthored `systems/<region>.yaml`) is NOT caught there, so a drill into an unauthored system likely surfaces as an unhandled exception, not a typed ERROR the UI can render. Logged as a Delivery Finding on 98-3; AC5's UI test pins the widget seam (`lastOrbitalError` prop) regardless.
- When RED-testing a UI seam fed by server errors, read the server handler's actual `except` clauses before assuming an error code exists on the wire — the loader raising loudly does not mean the handler forwards it.

### Confrontation resolution has MULTIPLE overlapping resolvers — find the incumbent before writing outcome tests (59-31)
- The per-turn sweep at the bottom of `_apply_narration_result_to_snapshot` runs resolvers IN ORDER, each short-circuiting on `enc.resolved`: `_resolve_if_no_opponent_remains` (4350, → `opponent_withdrew`) then `_resolve_dial_threshold_and_phase` (4359). The location-change handler (~2790) resolves EARLIER in the same call (→ `abandoned_on_location_change` / `player_victory` via `dial_threshold_outcome()`). So an "all opponents withdrawn" state already has an incumbent label (`opponent_withdrew`) — a new outcome story must RELABEL/REPLACE the incumbent, not add a resolver after it (the incumbent wins by running first).
- When writing outcome-label tests, drive the real entry `_apply_narration_result_to_snapshot(snap, NarrationTurnResult(...), player_name=, room=room_for(snap))` (no pack needed for the sweep), not the internal helper — survives whichever helper the Dev edits, and proves wiring.
- Confrontation OTEL is emitted via `_watcher_publish(event, fields, *, component="confrontation")` (sibling events: `confrontation_resolved_on_location_change`, `confrontation_deactivated_on_location_change`). Capture in tests by `monkeypatch.setattr(narration_apply, "_watcher_publish", _capture)` — the `component=` kwarg is how you filter confrontation events. `encounter_resolved_span` (the dial sweep's emit) is a separate OTEL-span channel that does NOT take `component=`; don't conflate the two when picking an assertion target.
- `dial_threshold_outcome()` (encounter.py:243) is a METHOD on StructuredEncounter, gated to `win_condition=="dial_threshold"`. An "alongside" helper the Architect asks for should also be a method; decide deliberately whether it inherits the win_condition gate (opponent-yield should NOT — a surrender is a win in combat too).

### The wiring failure class (the dominant bug category in this project)
- **Don't reinvent — wire up what exists.** Before building anything new, grep the codebase. Many systems are fully implemented but not wired into the server or UI. CLAUDE.md rule #3.
- **No half-wired features.** Connect the full pipeline or don't start. If something needs 5 connections, make 5 connections. Shipping 3 and calling it done is the exact failure mode Epic 15 was created to clean up.
- **Wire it, don't just define it.** Adding fields to a struct is not wiring. Adding props to a component is not wiring. Data must actually flow from source → consumer. If no code populates and transmits the field, the feature isn't done.
- **Never rationalize unwired code.** When `/sq-wire-it check` reports FAIL (no non-test consumers), the answer is **wire it**. Do not write paragraphs explaining why this time is different. If I catch myself typing "this is acceptable because" — STOP. That sentence is the bug. The wiring usually takes 5 minutes; the rationalization takes longer.
- **"Wiring means dashboard."** Internal data flow without OTEL visibility is not wired. A missing `WatcherEventBuilder::new(...)` call on a subsystem's dispatch path is a blocking wiring bug, never a "non-blocking improvement." Labeling an OTEL gap as non-blocking in my own audit is the exact self-compounded failure I hit in the 2026-04-09 Map fix.
- **No agent rationalization.** Dev/Architect/TEA/Reviewer are all Claude — they don't get to split blame across personas. "The Architect said it was fine" is not a defense. If a wiring gap is identified in any phase, the only valid response is "fix the code now," never "clarify the spec" or "file a follow-up story."
- **Verify wiring before claiming done.** `grep` for non-test consumers on the merged branch before marking a fix as complete. Don't wait for Keith to ask. A playtest with the GM panel open is the acceptance test.
- **Verify end-to-end before claiming fixed.** Code review is not verification. Trace the full wire path: source → channel → writer task → WebSocket → client handler → DOM. Session 7 had six consecutive "fixed" claims on the turn-lock bug, each found a real issue, none verified the message actually arrived at the browser.
- **Wiring gaps require action, not acknowledgment.** Finding a wiring gap and saying "yep that's a wiring gap" is worthless. Fix it. Log it. Check for siblings (if one compute-then-ignore exists, grep for the pattern). Verify OTEL. Don't move on.
- **Kitchen-sink gate failure is real** (story 16-1): nine agents approved unwired code because every phase rationalized it as "scope boundary" and "wiring comes in subsequent stories." The wiring-check gate exists in `.pennyfarthing/gates/` — every agent must enforce it, not just the reviewer as a backstop.

### No stubs, no fallbacks
- **No stubs. Ever.** When I hit a scope error or type mismatch, solve the actual problem. Don't substitute `Default::default()`, placeholder values, or restructure the design to avoid the issue. CLAUDE.md line 124: "Never say 'the right fix is X' and then do Y." Do X. If `snapshot` isn't in scope, move the code to where it is.
- **No silent fallbacks.** If a path/config/resource isn't where it should be, fail loudly. No `if not exists: try_other_thing`, no `unwrap_or_default()` that papers over missing data, no `Option::None` degradation on required fields.
- **No layered fallback design.** If the LLM is down, the system is down. Keyword intent classification "working" while narration is broken is not meaningful resilience — it's dead code with delusions of usefulness.
- **No reading `~/.pennyfarthing`.** Stay within the project directory tree. Global pennyfarthing config pulls in work-project settings that don't apply to SideQuest.

### Deferral is not an option
- **Never defer fixes.** When auditing and fixing gaps, fix every one in the current session. No "deferred to separate session," no "future work," no "needs porting first." There is no future session; there is only now.
- **Never suggest deferring work to Keith.** Never say "park it," "post-X problem," "follow-up story." He decides priorities, not me. If something's broken, fix it; if I can't, say what I've tried and what I'd try next.
- **Just execute.** Don't deprioritize or editorialize by task type ("this is a feature gap," "this needs X fixed first"). Route tasks for execution without commentary.
- **No "pre-existing" excuse.** Never dismiss broken tests as pre-existing and move on. If the suite isn't fully green at handoff, I failed. Don't check "does develop have the same bug" as a way to excuse not fixing it.
- **No baseline as insight.** "Most bugs are wiring bugs" is the central thesis of sq-wire-it, CLAUDE.md, and nine feedback memories — it's the assumed operating environment, not a discovery. Don't write retrospective bullets that restate documented fundamentals. Save insight slots for things that are actually surprising *given* the baseline.
- **Fix what you see, in this story.** If I find a test that lies about what it covers, a vacuous assertion, or a missing edge case in code I'm writing tests for — fix it NOW. Every "defer to follow-up" is debt compounding on Keith. Don't catalog problems; fix them.
- **No dressed-up scope shields — the 2026-04-14 incident.** Forbidden phrases: "out of this branch's scope," "days of forensic rewrite work," "honest green via #[ignore]," "real fix is X but for now Y," "incremental retirement path," "future work." Marking 39 broken integration tests `#[ignore = "tech-debt"]` is not an "honest green" — it's silencing failures with prettier framing. Disabling a wiring test disables the wiring detector for every subsystem it covered.
- **Two-step check before any `#[ignore]`:** (a) grep for the assertion substring — if it exists in current source, the fix is a one-path update, not "days of work"; (b) if it exists nowhere, the choice is implement-or-delete, never ignore.

### No weasel words in test design
- **"Cleanest / simplest / proper test approach" are weasel words.** State (1) WHAT the test covers, (2) WHY this shape is correct (cite the behavior or boundary). A test that "checks the happy path cleanly" isn't justified — specify exactly what the assertion proves.

### Trust Keith's instincts on timing
- **When Keith says a test is slow or a suite is misbehaving, he's right.** Investigate first, explain second. Dismissing his reads is gaslighting.

### Git gotchas
- **Never use `git stash`.** Ever. Pop causes conflicts, leaves orphans, loses visibility. Use temp branches for context switches, or re-apply manually.
- **Never run destructive git ops without explicit permission:** `reset --hard`, `reset --soft`, `checkout -- <file>`, `clean -f`, `branch -D`, `push --force`, `rebase -i`. Each of these has destroyed work in a past incident.
- **Never checkout `main` in a subrepo.** All subrepos use gitflow with `develop` as base. Checking out main cascades into pushing to the wrong branch and divergent history.
- **Never edit files in `/Users/keithavery/Projects/oq-1`.** OQ-1 is a parallel workspace with in-progress uncommitted changes. Treat it like another developer's machine. Remote branch deletes are fine; local state is hands-off.
- **Push before reorganizing.** Get work on remote FIRST. Then if you want pretty commits, do it on a new branch.
- **"Actually simpler" means you're about to improvise.** Stop. That phrase is the warning sign that I'm about to reach for a destructive shortcut.
- **When git is messy, one command at a time.** State the command, state what it does, wait. Don't chain recoveries.
- **If I fucked up, STOP.** Don't reach for more commands to fix it. State what happened and ask Keith what to do.

### Build / test gotchas
- **Build verification happens on OQ-2, not OQ-1.** All edits live in OQ-1/sidequest-api; after merge, pull on OQ-2 and `cargo build -p sidequest-server` there. The workspace-root build is a placeholder.
- **Test compile cascade:** Never spawn two cargo processes on the same workspace at once. Cargo's build lock queues them and a 2-minute timeout + new spawn creates zombie-compile cascades (4 competing cargos, 10+ minutes, zero results). Use `timeout: 300000` (5 min), `cargo build` first, `cargo test` second.
- **No duplicate test runs while testing-runner is active.** After spawning testing-runner, do not touch cargo on the same workspace with any build/test command. "Let me also check this other test file" = another full recompile. Wait for completion.
- **Don't rerun full test suites on every loop tick.** Full `cargo test` takes 90-300+ seconds. For playtest bugfix branches, `cargo build` is the gate; full test runs once at the end. Targeted `cargo test -p <crate> -- <filter>` for anything touching test-adjacent code.
- **No live LLM calls in the default suite.** Tests in sidequest-agents that call real `claude -p` burn tokens and cost 90+ seconds per run. Mock `ClaudeClient`. Live-LLM integration tests belong in `--ignored`.
- **0.02s cargo build means nothing changed.** If the build is suspiciously fast, your fix isn't in the binary. Look for "Compiling sidequest-server" in the output as proof the change landed.
- **Server logs exist and are informative.** Check `/tmp/sq-api.log` before speculating about causes.

### Playtest gotchas
- **Playtest mode is debugging, not building.** When Keith reports a bug, the infrastructure exists. Find the small break; don't rebuild pipelines from scratch. Prompt subagents with "diagnose and fix" not "build and wire."
- **Playtest focus is systems, not narration quality.** The prose has been solid for a long time — don't comment on writing quality, only log it when it indicates a system bug.
- **Don't stop at partial success during a trace.** "There it is!" followed by "but wait" is confusing. Complete the trace to the end, then report.
- **Don't restart the daemon.** It warms up ML models — restart is expensive. Leave it running across sessions.
- **Context discipline: thoroughness over speed.** Context pressure is not my problem — the system manages it via TirePump, relay, `/clear`. Don't rush an assessment, skip subagent results, or abbreviate a handoff to save tokens. Cutting corners to save context costs more context than doing it right the first time.

### Environment / process gotchas
- **Session files live in `.session/{story-id}-session.md`**, never in `sprint/` directly. Sprint is for archives after `pf sprint story finish`.
- **Skip architect + spec checks for SideQuest.** Personal project — streamlined RED → GREEN → VERIFY → REVIEW → FINISH. No architect spec validation, no spec-check/spec-reconcile.
- **No AI self-judgment.** Don't design automated Claude-judges-Claude validators for game decisions. Surface rich telemetry for human inspection instead.
- **Theme list tags are benchmark grades**, not storage locations. `[S] [A] [B] [C] [D] [U]` = superior/A/B/C/D/unknown tier. `[U]` ≠ "user-level," `[B]` ≠ "built-in."
- **`claude -p` fully supports tool use**, including `--allowedTools Bash(...)`. Never claim pipe mode doesn't support tools — the bug is somewhere else (prompt construction, binary paths, env vars).

### sm-setup can hand off to TEA without the story/epic context docs (2026-06-03, story 80-1)
- **What happened:** On TEA activation for 80-1, `pf validate context-story 80-1` failed (exit 2 — file not found). sm-setup had created `.session/80-1-session.md` (with technical approach + ACs inline) but **not** `sprint/context/context-story-80-1.md` or `context-epic-80.md`. Every sibling story (81-x, 82-x) had its context doc; 80-1 did not. The SM `resolve-gate` had reported `ready` during setup anyway, and the `gate-recovery` context-creation cascade never fired.
- **How to apply:** TEA's on-activation context gate (`pf validate context-story {id}`) is load-bearing — honor the "STOP on exit 1/2, do not auto-create" rule, but the clean recovery is to run `/pf:context create epic {N}` then `create story {N-N}` (cascade: epic first; if the story has no epic, the epic still needs a context doc because the story-context skill validates the parent exists). The story-context skill expects fixtures the plan may mis-name — read the real test files for fixture helper names before writing tests (80-1: `makePack`/`makeWorld`, `renderConnect`/`GENRES`, not the plan's `mockPack`/`renderConnectScreen`). Log the gap as a non-blocking Delivery Finding so the setup gate gets hardened.

### Historical incident log (things I've personally gotten wrong in this project)
- **2026-03-30 OTEL stub incident.** Said the right fix, then hacked `GameSnapshot::default()` when `snapshot` was out of scope. Re-read feedback_no_stubs_ever before ever reaching for a default value.
- **2026-03-31 git catastrophe.** Used `reset --soft`, `checkout -- .`, and a direct merge-to-develop in one session. Each "oh I'll just..." made things worse. Re-read feedback_git_discipline before any destructive op.
- **Story 19-8 Automapper rationalization.** Wiring check said FAIL, I wrote paragraphs explaining why it was fine. The wiring took 5 minutes. Re-read feedback_never_rationalize_unwired.
- **Story 16-1 kitchen-sink rationalization.** All 9 agents approved unwired code by calling it a "scope boundary." Re-read feedback_wiring_gate_failure.
- **2026-04-08 TurnRecord field-add incident.** Added struct fields, declared fixed — nobody was constructing TurnRecords. Re-read feedback_wire_not_define.
- **2026-04-09 Map OTEL self-correction.** Ran sq-wire-it on my own Map fix, found no OTEL spans, labeled it "non-blocking" and declared wiring PASS. Keith corrected: "this means it is not wired." Re-read feedback_wiring_means_dashboard.
- **2026-04-09 baseline-as-insight.** Wrote a retrospective bullet saying "every fix was a wiring bug" as if it were a synthesis. It's the project's central thesis. Re-read feedback_no_baseline_as_insight.

### testing-runner can clobber the session file (2026-05-30)
- **What happened:** During 72-3 verify, a `testing-runner` subagent invoked for a full-suite regression run wrote a "Test Result Cache" markdown over `.session/72-3-session.md`, destroying the entire session (all assessments, deviations, findings, ACs). `.session/` is gitignored → no git recovery; reconstructed from the in-session conversation record.
- **Why it bit:** The RUN_ID was `72-3-tea-verify` and the runner apparently derives a cache path from story id under `.session/`, colliding with `.session/{story}-session.md`.
- **How to apply:** When spawning `testing-runner`, (1) explicitly instruct it to ONLY run tests and report — "do not write any files, do not cache results to disk, do not touch `.session/`"; and (2) after it returns, `ls -la .session/{story}-session.md` to confirm size/mtime are sane before continuing. If clobbered, reconstruct from context immediately (the conversation holds every read+edit) and add a transparency recovery-note header. Consider snapshotting the session file to `/tmp` before a full-suite run as a cheap backup.

### Verify simplify-agent claims before applying — high-confidence ≠ correct (2026-06-01, story 65-8 verify)
- **What happened:** The three haiku simplify teammates returned two **high-confidence** findings that were both factually wrong, and rated the one genuinely valuable finding only *medium*.
  - reuse (high): "import `scripts/r2_manifest.py::load_manifest` instead of reimplementing the loader." Impossible — `scripts/` is in the **orchestrator** repo (`../scripts/`), not the `sidequest-server` package, so it isn't importable; and its contract differs (`list[dict]` vs `frozenset[str]`). A 2-command check (`ls scripts/r2_manifest.py` → not found; `grep ':func:' sidequest/` → 105 hits) debunked it.
  - quality (medium→dismiss): "`:func:` Sphinx role is inconsistent with peers." False — `:func:` is used 105× in the package; it IS the house style. Applying the "fix" would have introduced inconsistency.
  - efficiency (high): "cache `world_key_count` instead of recomputing per render." Technically a redundant walk, but the lore page is a cold path and the suggested fix *adds* a cache — anti-simplify. Declined.
  - The actually-valuable one was rated **medium** by reuse: the POI image key was built as two independent f-strings (gate vs presenter `<img src>`) — a silent drift hazard. Upgraded and applied (one shared `poi_image_key`).
- **How to apply:** Treat simplify-agent confidence as a *prompt to investigate*, not a verdict. Before applying ANY finding: (1) verify the factual premise with a quick grep/ls (is the import real? is the "inconsistency" actually inconsistent?); (2) reject "simplify" suggestions that ADD state/caching on cold paths — they betray the pass's purpose; (3) re-rank by *correctness impact*, not the agent's confidence — a medium "two strings must stay in lockstep" finding outranks a high "micro-optimize a cold path." The leader's judgment is the product, not the agents' raw output.

### simplify-reuse rates PRE-EXISTING / out-of-diff duplication "high confidence" — verify it's actually in THIS story's diff before applying (2026-06-03, story 80-1 verify)
- **What happened:** On a UI story (lobby grouped picker) that rewrote `OptionList.tsx`, simplify-reuse returned two *high*-confidence findings: "radio-button class string duplicates ModePicker — extract a shared util" and (medium) "localStorage try-catch boilerplate duplicated across App.tsx/ConnectScreen." Both real *duplication*, but **neither was introduced by the story.** `git diff develop...HEAD` showed the OptionList radio `className` ternary byte-identical on `+`/`-` (only re-indented in the rewrite) — carried over unchanged; `ModePicker.tsx` wasn't in the diff at all; the storage logic wasn't touched. Applying them would have edited out-of-scope files (`ModePicker`) for zero in-scope benefit and real regression risk.
- **How to apply:** The simplify pass is scoped to **the diff**, not the whole file. For every reuse finding, run `git diff <base>...HEAD -- <file>` and confirm the flagged duplication is *introduced or modified by this story* — a `+` line whose identical `-` twin exists (a move/re-indent) is pre-existing, decline it. Cross-component "extract a shared util" suggestions that pull in files outside the diff are scope creep; decline and note as pre-existing. Same root cause as the 65-8 entry (confidence ≠ correctness), different tell: **in-diff vs pre-existing.**

### context-story line numbers drift — confirm seams before testing (73-4)
- context-story-73-4 cited `narration_apply.py:~3199` as the "beat_applied" emit; that line is actually **inventory consume** code now. The real `beat_applied` watcher emits are TWO sites: `~4070` (beat_selection path) and `~5792` (opposed_check path — the one the 73-4 repro hit). Always `grep -n "beat_applied\|apply_beat"` to locate the live seam; the context doc's line numbers are advisory and drift.
- **Player-bound confrontation payload SSoT:** `build_confrontation_payload` (`sidequest/server/dispatch/confrontation.py`), called from `websocket_session_handler.py:~1632`. The `beat_applied`/`beat_no_op` emits in narration_apply are **dev/OTEL watcher** events, NOT player-facing. To get a per-beat descriptor to the UI, the carrier is the **encounter** (shared snapshot state between narration_apply's apply_beat and the handler's payload build) — `build_confrontation_payload` already does this for the `win_condition`/`player_hp` legibility keys (the precedent to mirror).
- **opposed_check applies a beat per side** (player then opponent). A singular `enc.last_beat_*` is clobbered by the opponent's beat UNLESS the player's beat resolved the encounter (then opponent's apply_beat early-returns `skipped_reason="encounter_resolved"`). For player-facing per-beat readouts, store **per-side** (`dict[side, ...]`) so the player's beat survives a later opponent beat in the same turn.

### Confrontation actor SEATING — traps when testing who's-in-the-fight (59-35)
- **`withdrawn` is an `EncounterActor` field, NOT an `Npc` field** (`game/encounter.py:125` vs `game/session.py` `Npc`). Specs that say "seat scene-present, not-withdrawn NPCs" reference a field a `snapshot.npcs` roster entry doesn't have. Don't write a test pinning `npc.withdrawn` — it's vacuous. Flag the spec ambiguity as a finding.
- **The opponent location-fallback conscripts EVERY same-location NPC as `side="opponent"`** with no disposition filter (`_npc_fallback_at_location`, `adversarial=True`, `encounter_lifecycle.py:466`). It fires ONLY when `npcs_present` is empty. So an empty-`npcs_present` combat with a co-located friendly ally seats that ally as the *enemy*. To isolate a friendly/ally-seating test from the opponent path, pass an EXPLICIT opponent in `npcs_present` (non-empty ⇒ opponent fallback skipped). The empty-`npcs_present`-with-mixed-dispositions case is its own RED collision test — assert the friendly ends `side="player"` and the hostile `side="opponent"`.
- **`participant.joined` hardcodes `source="seat"` for ALL `side=="player"` actors** (the participant-join loop in `instantiate_encounter_from_trigger`); opponents use `seating_source` (`router_named`/`location_fallback`/`materialized`). Any NEW player-side seating source (e.g. `friendly_fallback`) must be distinguished from PC seats — assert the new `source` value explicitly; today it can only ever read `"seat"`.
- **Disposition fixtures:** `Npc(disposition=N)` coerces an int. `> 10` ⇒ FRIENDLY, `< -10` ⇒ HOSTILE, else NEUTRAL (defaults). Use `disposition=25` for FRIENDLY. `armor_class` defaults to 10 on `CreatureCore` — an NPC built without one still has a resolvable AC.
- **No hp_depletion confrontation in `test_genre`** — its `combat` is `dial_threshold`. For an hp_depletion path, load real `space_opera` via `tests/_helpers/genre_paths.find_pack_path` + `@pytest.mark.skipif(not GENRE_PACKS_DIR.is_dir())`, and give the PC a full SWN stat block (`Physique/Reflex/...`) so the seam can roll 1d8+DEX initiative. Pattern: `test_72_8_presence_last_seen_stamp.py`.

### Dice-path / WWN cast seam testing (102-2 RED)
- **`monkeypatch.setattr("random.randint", ...)` pins EVERY module's rolls at once** — `narration_apply`, `dispatch/damage_roll`, downed seam, reprisal all do `import random` and share the one module object. Use the global pin when the implementation might move which module rolls (e.g. a spine extraction story); use the module-path pin (`sidequest.server.dispatch.damage_roll.random.randint`) only when isolating one roll site from another in the same test.
- **`Stat` (protocol/types.py) is an open RootModel[str], not a closed enum** — any non-blank string uppercases and validates. Synthetic packs with flavor stat names (Lore/Might) pass `Stat(beat.stat_check)` in `dispatch_dice_throw`; don't waste time mapping to STR/DEX.
- **`build_confrontation_payload` has NO pack/catalog param** — it derives the recipient's WWN `SpellcastingState` (Task 5 gate) but cannot resolve spell display names. A spellcasting projection contract can only carry what the state has: prepared spell-id strings + casts. If a story needs names on the wire, that's a signature change — flag it, don't silently spec it into a RED test.
- **`session_handler_factory(genre=...)` loads any real pack by slug** (real search paths at call time) — heavy_metal works for handler-level wiring tests; guard with `GENRE_PACKS_DIR.is_dir()` skipif. The factory's char is "Rux"/Fighter with EMPTY stats — hydrate `char.stats` AND `core.spellcasting` yourself before driving a WWN seam.
- **MagicMock packs break `dispatch_dice_throw`** (it iterates `pack.classes` for the WWN warrior gate; a MagicMock attr isn't iterable). The synthetic-pack rig from `test_wwn_cast_dispatch.py` only works for direct spine calls (`_resolve_wwn_cast_for_beat`); for the dispatch seam use a REAL pack.
- **UI App-level beat-commit harness:** `combat-player-echo-wiring.test.tsx` is the canonical copy source (GameBoard stubbed to a vi.hoisted prop trap + jest-websocket-mock + CHARACTER_CREATION/SESSION_EVENT boot). No R3F mocks needed as long as the stub keeps App off the canvas. Assert outbound frames via `server.messages.filter(type === MessageType.DICE_THROW)`.
- **Wire-shape regression direction that matters:** old-client frame WITHOUT the new optional field must validate (server-side `model_validate` on the keyless dict), and new non-cast frames must NOT grow the key (`"spell_id" in payload === false` client-side). Pin both ends; pydantic `extra_forbidden` makes the missing-field RED loud.
- **RED tests can pass by kill-coincidence — check pins against TODAY's behavior, not just target behavior.** 102-4: "no opponent reprisal on a sealed commit" pinned rng MAX so the player's 2d6=12 killed the 10-HP opponent in today's immediate-resolution flow → reprisal skipped → test vacuously GREEN in RED. Pin MIN instead: the player misses, today's reprisal still emits `encounter.opponent_attack_resolved` (it records miss math), and the span assertion becomes the genuine RED driver. Rule: for every new RED test, trace what TODAY's code does under the pinned rng before trusting the failure list — testing-runner reports tell you WHICH tests failed, you must ask why one passed.

### Fixtures that dispatch during setup must DEPEND on otel_capture (102-4, 2026-06-10)
- pytest instantiates fixtures in signature order: `(my_fixture, otel_capture)` runs the dispatch before the in-memory exporter installs, making span assertions structurally unsatisfiable while a sibling test asserting the same span inline passes. Put `otel_capture` in the fixture's own parameter list. Symptom: `finished_spans: []` for one consumer, spans present for another.
- Rework rounds can mix ONE true RED driver with green-by-design regression locks (ledger reset, double-commit rejection, MP wire proof) — document which is which in the docstrings so the tests-fail gate and Dev both know the contract.

### Chargen handler-walk wire tests: beneath_sunden connect reaches the real SDK — use flickering_reach (106-1, 2026-06-13)
- Driving `_chargen_confirmation` through `handle_message` (45-2 shape) for `caverns_and_claudes`: the WWN megadungeon world `beneath_sunden` runs ADR-106 connect-time init that constructs the real Anthropic SDK → the autouse `conftest.py::_no_real_anthropic_sdk` guard raises `LlmClientError` on `handle_message(connect_msg)` BEFORE chargen even starts. Use `flickering_reach` (the proven-hermetic world `test_45_2_chargen_to_playing_wire` walks). Safe to swap when the behavior under test is GENRE-tier (chargen loadout, kit-roll, inventory armor_class all live in the genre pack, not the world) — note the world is incidental in the test docstring.
- Hermetic chargen walk recipe: seed an empty MP save via `_build_pg_repos_for_slug`, `RoomRegistry()` + `attach_room_context`, SESSION_EVENT connect (assert `payload.event=='connected'`), PLAYER_SEAT, then loop CharacterCreationMessage choosing `"1"` on choice scenes / a name on freeform / `phase="continue"` on auto-advance until `builder.is_confirmation()`, then `phase="confirmation"`.

### "Already-delivered" stories: write a characterization test FIRST, then reframe as coverage (107-1, 2026-06-13)
- 107-1 ("dungeon scene/location advance: discovered_rooms/scene_id/region_transitions frozen, render under-fires") turned out to be ALREADY FIXED. Its forensics were dated the SAME DAY as `be4f7464` (#835, "in-dungeon movement for region-mode worlds") — the fix that made the procedural navigator reachable in-dungeon, which unfroze `current_region` → the render gate fires → the descent stops reading as one scene. **Always diff the story's forensics date against recent merges in the touched subsystem before writing RED tests.**
- The story named the WRONG fields. The procedural ADR-106 dungeon is REGION-based: a move advances `discovered_regions` / `current_region` / `region_transitions` (via `apply_world_patch` consensus-sync `session.py:1546` + `frontier_hook.notify_region_transition`). `discovered_rooms` is a separate room-graph field only filled at chargen, and **`GameSnapshot` has NO `scene_id` field at all** (`list_npcs_in_scene.py`/`query_scene_state.py` say so). Don't pin RED tests to a field name from the story title without grepping that the field exists and is the one the mechanism uses.
- The render chain for a PROCEDURAL room: materializer `dungeon/room_yaml_emit.py::write_room_yaml` writes `<world>/rooms/<region_id>.yaml` (region ids like `exp001.r1`) → `_maybe_emit_location_description` Path 1 (`load_room_payload`) sources it → fresh LOCATION_DESCRIPTION. The helper's two sources are static room YAML + `cartography.regions`; procedural rooms ride the FIRST via the materializer's YAML emit (NOT cartography — procedural ids aren't authored regions).
- When verification comes back GREEN, the genuine gap is usually TEST COVERAGE, not behavior — the deliverable becomes the regression tests themselves. Drive real components (real `run_movement_dispatch`; real `write_room_yaml` → real `load_room_payload` → real `_maybe_emit_location_description`), assert DISTINCT per-room output (region_id + prose differ) so the test actually catches "one frozen scene reused". Ask the user the disposition (cancel vs ship-as-coverage) — don't unilaterally cancel a sprint story.
- Content-free movement fixture: synthetic `RegionGraph` (add_node/add_edge) + a fake store exposing `load_map(entrance_id=)`/`load_frontier()` + a fake palette whose `.get(theme_id)` returns `display_name`+`narrator.{register,flavor,motifs}`. Mirrors `tests/agents/subsystems/test_movement_dispatch.py`. `run_movement_dispatch` success applies the per-PC patch so discovered_regions/region_transitions/current_region all advance as a side effect — assert them (the old tests only asserted `pc_regions`).

### Coverage-test docstrings must not overclaim — the Reviewer treats it as a lying-docstring (107-1 rework, 2026-06-13)
- The 107-1 integration test's docstring said it "verifies the full per-room render chain **end-to-end**" and "the per-room render **is wired**". Avasarala REJECTED: the test calls `_maybe_emit_location_description` directly with `room_id_override`, bypassing the production turn-handler gate (`_is_region_mode_world` + `_region_changed` at websocket_session_handler.py:2257-2287). Green only proved the helper can SOURCE a procedural-room YAML. In a lie-detector-culture project the comment-analyzer flags overclaiming docstrings with high confidence and the Reviewer cannot dismiss them. **Write docstrings that state what GREEN proves AND what is out of scope/deferred** (here: the gate firing per room → epic live playtest). A direct-helper-call test is fine; calling it "end-to-end" is not.
- **`assert <list>` (truthy) violates the meaningful-assertion rule (lang-review #6 / CLAUDE.md A4).** Use `assert len(x) == N` to lock the count. The Reviewer cannot dismiss a rule-matching finding (only downgrade severity), so a truthy-list assert WILL bounce the review. Always count.
- **A `MagicMock` world fakes a cartography region and masks no-source tests.** `_maybe_emit_location_description`'s fallback does `world.cartography.regions.get(room_id)` — on a `MagicMock` world that returns a truthy MagicMock, so `sourced=True` and it EMITS even for a room that doesn't exist. For a no-source/negative test set `world.cartography = None` (mirror `test_location_description_emit.py::test_emit_fires_no_source_when_neither_path_resolves`). The POSITIVE test is safe with a default MagicMock world only because `load_room_payload` succeeds and the fallback is never reached.
- **Split-party negative for current_region:** two seats, one moves, one stays → `region_for()` (no perspective) returns None (no consensus) → the apply_world_patch consensus-sync (session.py:1546) does NOT advance `current_region`; but the per-PC move STILL appends `discovered_regions` + logs `region_transitions` (shared fog-of-war, frontier_hook line 152 is unconditional). Assert both halves — it's the negative contract a single-PC test structurally cannot show.

## 108-6 WWN dying window (2026-06-14)

- **Weak-test trap on incapacitation gates.** A "downed soloist can still act" wiring
  test can pass *today* for the wrong reason: the current WWN dying-window status is
  minted NON-incapacitating, so `find_incapacitating_status` returns None and the gate
  trivially lets it through. The real solo-halt only exists once the window is
  *incapacitating*. Fix: assert `window.incapacitating is True` as the test premise, so
  the test actually exercises the gate carve instead of a degenerate fall-through.
- **`apply_post_resolution_lethality` early-returns** unless `encounter` is resolved with
  a PC-down outcome (`post_resolution_lethality.py:208-211`). Any per-turn clock/expiry
  homed there will NOT fire on a normal player-action turn (a stall) — so "clock can't be
  paused" must be wired on the player-action path. The handler has cfg via
  `session._session_data.genre_pack` (`player_action.py:429`), so the bound
  `cfg.trauma.*` is reachable at the gate. Test the OUTCOME via `PlayerActionHandler.handle`,
  not the function, to avoid coupling and to force the requirement onto the right path.
- **Grounded harnesses for WN lethality tests:** span capture = local `InMemorySpanExporter`
  + `_tracer=` (test_142_wn_lethality_spans.py); `resolve_downed` = `WwnRulesetModule()` +
  `WwnConfig(attribute_map=...)` + `CreatureCore` (test_wwn_lethality.py); downed seam =
  reuse `_make_reprisal_pack`/`_make_snapshot_and_encounter` from
  test_reprisal_wn_downed_seam.py (ablate the opponent core to 0 HP for the no-live-hostile
  case); gate = `_playing_session`/`_action_msg`/`_ReachedNarrationPath` sentinel from
  test_player_action_incapacitated_gate.py; stabilize tool = `pg_store_with` +
  `default_registry._tools[...]` direct-handler call.
## Verify pack disk-state before trusting a design's "the packs are migrated" claim (114-10)

The 114-9 design said "apply the Fate gear model to the four packs" and its migration
section assumed all four were already `ruleset: fate`. On disk only **pulp_noir** was —
spaghetti_western / tea_and_murder / wry_whimsy were still native d20 (point-buy,
`stat_ranges`, `typical_classes`), and their fate migrations (121-3/4/5) + the
Fate-archetype shape (121-7) were all backlog. Always `grep ^ruleset:` the real
`rules.yaml` (and check `archetypes.yaml` shape) before writing migration tests; a
"5-point apply" story can hide a ~30-point absorbed migration. Surface it as a blocking
Delivery Finding + ask the Operator the scope question — don't silently pick.

## Pin validator invariants as PURE functions when the model they validate doesn't exist yet

114-10's refresh-invariant / dangling-id checks validate a Fate-archetype shape that is
121-7 territory and undefined on disk. Writing `check_refresh_invariant(*, authored_refresh,
base_refresh, free_stunts, total_stunts) -> str|None` over primitives (not over an archetype
object) kept the tests refactor-stable and let Dev choose field names. Prove the wiring
separately via an integration test that runs the real validator on real content.

## "Closes the F2b deferral" means the deferred work IS in scope — don't let an Explore scout's reading of the EARLIER story's "stateless" docstring shrink it (118-5 RED, 2026-06-16)

118-5 ("F3e — compel accept/refuse round-trip; *closes the F2b deferral*") flagged that
F2b's `propose_fate_compel`/`offer_compel` fires `fate.compel.offered` but **persists
nothing** (the flow is stateless). A server Explore scout read F2b's docstring ("no economy
change happens here … acceptance lands with the F3 UI round-trip") and concluded **118-5 is
also stateless — no PendingCompel needed.** That was wrong: the *whole point* of "closes the
deferral" is that the deferred PendingCompel persistence lands in THIS story. The session
AC (highest spec authority) + the epic's "reactive FATE_STATE projection" mandate both
require it (the UI can't show a compel the server doesn't remember). **Tell:** when a title
says "closes the X deferral / picks up the F-something follow-up," the earlier story's
"stateless"/"deferred" docstring describes the EARLIER story, not yours — the deferred work
is your deliverable. Trust the session ACs over a sub-agent's scope inference.
- **Concrete anchors for the compel round-trip (what already existed vs the real gaps):**
  `FateRulesetModule.accept_compel` ALREADY existed (earn +1 FP + `fate.compel.accepted`
  span, `ruleset/fate.py:314`) — "wire up what exists," don't re-author it. The genuine
  gaps were: `refuse_compel` (spend 1 FP via the existing fail-loud `spend_fate_point` +
  a new `fate.compel.refused` span), `offer_compel` persistence (it takes no `encounter`
  today), `FateConflictEntry.pending_compels` on the projection (`fate_projection.py`
  `build_fate_state_payload`), the `compel_accept`/`compel_refuse` members on the
  `FateActionPayload.action` Literal (`protocol/fate.py:45`), a `fate_point_delta` field on
  the frozen `FateDispatchResult`, and the dispatch routing (route early like `concede`).
- **Refuse-at-0 is the load-bearing fail-loud test:** `spend_fate_point` already raises
  `FateEconomyError` at 0 (validate→mutate→emit), so `refuse_compel` must reuse it and the
  `fate.compel.refused` span must NOT fire on a rejected refusal. Pin both (raises + no span).
- **The UI compel control inherits the surface's existing `ruleset!=="fate"` / no-active-
  conflict empty-DOM gate** (`FateConflictSurface.tsx:98-100`) — so the epic's required
  "never co-renders with ConfrontationOverlay" paired negative is satisfied by the gate
  already; the new negatives to add are "no control when `pending_compels` empty." The
  board-level production-path wiring test reuses the `renderBoard` harness from
  `GameBoard-fate-tab.test.tsx` (no R3F mocks needed if you don't pass a `fateRoll`).

## When a Reviewer offers an either/or fix for a dishonest error path, pin the STRONG option by ERROR ORIGIN, not exception type (119-4 RED rework, 2026-06-16)

119-4's broad `except Exception` in `complete_with_tools` re-raised ANY in-loop error
(a parse `IndexError`, a `CLINotFoundError`, a timeout) as
`AgentSdkAuthUnavailable("subscription login absent or expired")` + a
`narrator.auth_unavailable` event — a false "login expired" on the very GM panel the
story exists to make honest. The Reviewer offered an **OR**: narrow the catch *or* keep
it broad with a non-committal message. Two RED-design lessons:

- **Forbid the weak option deliberately.** "Keep it broad + soften the *message*" still
  leaves the event NAME (`narrator.auth_unavailable`) and the exception TYPE
  (`AgentSdkAuthUnavailable`) asserting auth — the panel still shows an auth event for a
  parse bug. So the honest contract is: a non-auth/internal error must emit **no auth
  event and no `AgentSdkAuthUnavailable` at all.** Pin that (assert NOT isinstance auth +
  assert the event never fired). It forces the strong fix and rules out the cosmetic one.
- **Discriminate by ORIGIN (transport vs our loop body), not by exception TYPE.** The
  existing fakes raise a bare `RuntimeError` to mean "the `query()` transport failed = an
  absent login (OQ-5 → maps to auth)." A *type*-narrowed catch (`except ClaudeSDKError`)
  would stop catching that `RuntimeError` and break the AC1' query-raised test. The
  reconcilable contract: **transport boundary raises → auth+event (AC1'); our own
  message-processing raises → propagates raw, no auth signal.** To pin "our body raised,"
  monkeypatch the first per-message call (`_is_agent_result_message`) to raise a sentinel
  `ValueError` — an unambiguously INTERNAL fault the transport-catch must let escape. This
  also tells Dev the fix is a **loop restructure** (separate `__anext__` from body
  processing), not a type-narrow.
- **Comment-honesty fixes are NOT test-pinnable** (no source-text grep — house rule). Flag
  them as a Delivery Finding so Dev applies the Reviewer's [LOW] DOC cluster by hand; a
  green suite will not catch a stale comment.
- **Assert cause survival robustly:** `isinstance(raised, ValueError) or
  isinstance(raised.__cause__, ValueError)` accepts either a raw propagate or an honest
  `raise NonAuthError(...) from exc` wrap — don't over-pin the exact wrapper type.

### A fully-scripted plan's test code carries APPARITION SIGNATURES — ground every call against the canonical harness before trusting it (126-8 RED, 2026-06-18)
126-8 arrived with an 8-task server plan that wrote out *complete* test code per task. Convenient, but ~4 of its API shapes did not match the real codebase, and copying them verbatim would have produced tests that fail at fixture construction (wrong reason), not on missing production:
- `ThrowParams(position=.., velocity=.., angular=.., spin=0.0)` — **no `spin` field**; real shape is `velocity:(f,f,f)`, `angular:(f,f,f)`, `position:(f,f)` in `sidequest.protocol.dice` (plan said `protocol.models`). `ProtocolBase` is `extra="forbid"` so the bogus `spin` would have ValidationError'd.
- `StructuredEncounter(encounter_type="conflict")` alone — **`player_metric`/`opponent_metric` are REQUIRED** (no defaults). The ledger tests would have failed on validation, masking the real "no `pending_defenses` field" RED.
- Handler/wiring tests calling `session.handle_message(throw_msg)` — the canonical Fate harness (`tests/server/test_fate_throw_handler_wiring.py`) drives `HANDLER.handle(session, msg)` directly on a **`SimpleNamespace` session double** (`_state=_State.Playing`, `_session_data=sd`, `_room=SessionRoom`) and drains the room's `asyncio.Queue`; the registry wiring is a SEPARATE reflection assertion (`WebSocketSessionHandler._message_handler_for("FATE_THROW") is HANDLER`). A SimpleNamespace has no `handle_message`.
- `_build_turn_context(session, sd)` — real signature is `_build_turn_context(sd, *, room=...)` and it reads `sd.genre_pack.rules.confrontations` (so the SimpleNamespace `sd.genre_pack.rules` needs `confrontations=[]`, not just `ruleset="fate"`).
- **Tell:** the plan author writes the test against the API they *intend* to build, not the one on disk. For every constructor/call in a handed-down plan, run one of (a) `grep` the real model/signature, (b) read the nearest sibling test that already drives that seam. The canonical sibling for Fate dice-path handler tests is `test_fate_throw_handler_wiring.py`; for dispatch-layer, `test_fate_conflict.py` + `tests/game/ruleset/_dispatch_fixture.py`.

### Fate opponent targeting is DETERMINISTIC — a 1-PC/1-healthy-NPC fixture reliably parks (126-8)
`decide_opponent_action` (`game/fate_opponent.py:129`) picks the highest-threat live PC (finish-the-wounded → retaliate → highest-threat, seating-order tiebreak) and returns an attack — it never random-targets. So at REVEAL `_seat_opponent_commits` seats the NPC attacking the PC every time, and the DEFEND barrier parks deterministically with NO rng pin needed. To build the *immediate-resolve* (no-park) variant, seat NO live opponent and have the PC `overcome` a passive difficulty — nothing targets a PC, so `_build_pending_defenses` returns `[]`. Healthy vs depleted opponent is the park/no-park switch: a fresh `FateSheet()` survives REVEAL and attacks; the `_depleted_thug` (all stress checked + consequences filled) gets taken out and the conflict resolves instead.

### `sanitize_player_text(None)` returns "" — the optional-field sanitize landmine (118-9)
`protocol/sanitize.py::sanitize_player_text` starts `if not text: return ""`. So `sanitize_player_text(None)` returns `""`, NOT `None`, with no crash. When the field being sanitized is `Optional[str]` (e.g. Fate `payload.target`, where `None` means "passive action, no opponent"), a naive `sanitize_player_text(payload.target)` silently coerces `None → ""`, flipping a passive action into a broken active one downstream (`_opposition_total` treats a non-None target as a real defender → `find_creature_core("") → raises`). When a sanitize fix lands on an optional field, ALWAYS write a TRIPWIRE test asserting the `None` input is preserved as `None` (`test_passive_action_preserves_none_target`). It's green today and goes red the instant Dev does the naive thing. Don't trust the happy-path injection test alone.
