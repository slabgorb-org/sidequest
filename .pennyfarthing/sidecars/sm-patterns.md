## SM Patterns

<!-- migrated from Claude auto-memory store, 2026-06-24 -->

### Cross-machine story/epic-id collisions — finish-time renumber recipe (2026-05-04, 45-41)
- Both oq-1/oq-2 pick the next-available id independently when filing, so story AND epic ids collide (observed 3x in epic 45 within ~24h). No locking, no shared backlog reservation.
- Recipe: (1) DETECT AT FINISH, not before — a `git push origin main` rejection ("remote contains work you do not have") on the orchestrator during `pf sprint story finish` is the signature; pull to confirm same id on the other side. (2) RENUMBER THE LOSER (whoever merged to origin/main first wins) — touch only orchestrator sprint YAML entry + archived session file. (3) Distinguish immutable history (branch names `feat/45-NN`, commit msgs, PR titles — leave alone, add a `note:` field) from LIVE forward-references in merged source (code comments, docstrings, YAML `# deferred to epic N`) which MUST be renumbered or they silently misdirect once a different epic claims the freed number — fix with a comment-only PR per repo off develop. (4) Session archive carries the original id throughout — add a tracker-note paragraph under the new id, leave the body. (5) No `git stash`; copy uncommitted changes to `/tmp/*.bak`.
- Epic-119→120 case (2026-06-15): left 7 merged subrepo refs saying "epic 119" that then pointed at the wrong epic; recovered via content PR #464 + server PR #883. "Leave the subrepos alone" means leave the HISTORY alone, not the misleading live refs.

### Coupled server+content stories — merge the server schema PR first; rebase (not revert) on ADR-147 relocations (2026-06-15, 114-15)
- When a story spans content + server and the content references a NEW server-side schema field, merge order is load-bearing because pack models use `model_config = {"extra": "forbid"}`. Trap (114-15): content PR #470 (genre-tier `ship_weapons:`) merged cleanly but server PR #895 (`InventoryConfig.ship_weapons`) conflicted and was held → develop had the YAML but no field → `load_genre_pack("space_opera")` died on `extra=forbid`; develop broken ~8 min.
- Rule 1: merge the server schema PR FIRST (or verify both land together). After landing a coupled story's PRs, run a `load_genre_pack(<pack>)` smoke against develop BEFORE committing the sprint-YAML completion — gate the finish on a real load, not just `gh pr --json mergedAt`.
- Rule 2: the conflict was a mid-flight RELOCATION, not a logic clash. Epic 122 (ADR-147 "honest layering") is relocating pure helpers from `server/` down to `game/` (e.g. 122-2 moved `server/dispatch/inventory_resolve.py` → `game/inventory_resolve.py`, leaving a re-export shim). A server PR editing the old location conflicts as modify-vs-relocate. Fix = REBASE + re-apply the edit to the NEW game-tier file (take develop's shim verbatim for the server path), NOT revert. Import law: `server/` may import from `game/`; `game/` must never import up from `server/`.

### pf sprint new is destructive — clean new-sprint-with-carryover recipe (2026-06-22)
- The sprint is sharded: `sprint/current-sprint.yaml` is a thin index (`epics: ['84','153',...]` string refs) over `sprint/epic-<id>.yaml` shards. Traps: (1) `pf sprint new` overwrites the index to `epics: []` AND DELETES every non-carried `epic-*.yaml` shard from disk (git shows `D`); no auto-rollover/archive; prompts "Continue?" (pipe `printf 'y\n' |`); recoverable from `git HEAD`. (2) `reindex`/writes key off `_is_sharded_on_disk` ("is `epics[0]` a string") — reindexing into an EMPTY index writes inline/monolithic and stays stuck; no CLI converts inline→sharded, hand-write the index back to `epics: ['153']` form (schema-validation Write hook gates it). (3) `pf sprint epic archive` reads the on-disk shard (can be stale vs inline index) AND appends EVERY story incl. `canceled` to `sprint-<new>-completed.yaml` as completed-today — reset that registry to `completed_epics: []`/`completed_stories: []` (must be empty lists not comments: `get_archived_stories` does `extend(None)`→TypeError).
- Clean recipe (cancel open in A/B, carry C): 1) `pf sprint story update <id> --status canceled` for each open story (story-level keeps done=done; `epic cancel` flips done→canceled). 2) `printf 'y\n' | pf sprint new ...`. 3) `git checkout HEAD -- sprint/epic-{A,B,C}.yaml` then `pf sprint epic reindex` each. 4) `pf sprint epic archive A B` (moves shards+context, drops from index). 5) hand-write index to `epics: ['C']`; reset completed-registry to empty lists. 6) verify `pf sprint validate <file>` (needs FILE arg), `status`, `metrics`; commit to orchestrator `main` (rebase-pull then push).

### superpowers design stories finish via `complete`, not `finish` (2026-06, 121-6)
- A `workflow: superpowers` story (Architect design-spec deliverable, e.g. spec in `docs/superpowers/specs/` + an ADR amendment) is finished with `pf sprint story complete <id>` (marks done + ticks the plan checkbox), NOT `pf sprint story finish` — `finish` expects a `.session/<id>-session.md` to archive and a PR to merge, neither of which exists here.
- These run Architect-direct (Keith → `/pf-architect` with the story id, no SM setup, no session/branch/Jira); deliverable is docs committed straight to the orchestrator repo (`main`), no subrepo PR.
- Recipe: `pf sprint story complete <id>` → `git add sprint/<epic>.yaml` + commit `chore(sprint): complete <id>` → `git push origin main`. Orchestrator `main` lags between clones (oq-1/oq-2) — expect a push reject and `git pull --rebase origin main` first (tree clean, no stash). Never reach for `pf sprint story finish` or construct a session/PR.

### How to work with Keith
- **Senior architect, 30-year dev, full product perspective.** He wore every hat at startups. Trust his scope/priority calls. Talk at the architectural abstraction level — pattern names, trade-offs, system decomposition.
- **Procedural generation domain expert** — MUSHcode, populinator, conlang, gotown lineage. SideQuest content systems are mature, not experimental.
- **Velocity calibration: ~20x human dev speed, sustained.** Don't size sprints based on what a human would do. Parallel agents change the math 5-10x on parallelizable work. There is no "too much for one sprint."
- **Dictation artifacts** ("axiom" → "axum", "SERG" → "serde", "playlist" → "playtest"). Parse for intent.

### Handoff CLI protocol (the SM primary workflow)
- **The canonical phase exit sequence:** `pf handoff resolve-gate` → gate check → `pf handoff complete-phase` → `pf handoff marker`. If marker output contains `relay: true`, invoke the named skill (`/pf-dev`, `/pf-tea`, etc.) via the Skill tool. Otherwise output the fallback and EXIT.
- **Nothing after the marker.** Once `pf handoff marker` runs, the phase is closed. Any further output risks racing with the next agent's activation.
- **Session file path:** `.session/{story-id}-session.md`. Read `**Phase:**`, `**Workflow:**`, `**Repos:**` at startup. Never write session files directly into `sprint/` — that's archive territory, populated only by `pf sprint story finish`.
- **Before starting new work, check phase ownership.** `pf workflow phase-check {workflow} {phase}` returns the current owner. If it's not me, run `pf handoff marker $OWNER` and relay instead of forcing my phase.

### Story lifecycle enforcement
- **Story completion is mandatory.** A story is NOT done until: (1) reviewer approves and merges the PR, (2) SM runs `pf sprint story finish` (archive session, update Jira, clean up). Never mark complete on PR approval alone.
- **Never start new work with blocking open PRs.** The merge-ready gate blocks `/pf-sprint work` if non-draft PRs exist for stories not in `in_review` status. PRs for `in_review` stories are OK (awaiting external review). If stuck in "merged but not finished," run `/pf-reviewer` or `/pf-sm` as appropriate.
- **Verify wiring before declaring a story complete.** After `pf sprint story finish`, before the summary message, grep the merged branch for the new exports in non-test production code paths. Report the wiring check result as part of the completion summary. Do this automatically — never make Keith ask.
- **Spec authority:** story scope (session file) > story context > epic context > architecture docs / SOUL / rules. When sources conflict, the session scope wins. Log deviations in the session file's `## Design Deviations` section at the moment of decision, not at phase exit — the deviations-logged gate validates at exit and rushed entries miss fields.
- **Finish flow is fragile.** Session archive and YAML status update are separate steps. If one fails, the other doesn't compensate. Verify both after `pf sprint story finish`.

### Phase-ownership enforcement for wiring stories
- **Wiring stories must name the specific call site in the ACs at setup time.** Not "X is usable by the server" — "X is called from `dispatch_player_action()`, and result flows to the WebSocket as message type Z." If the session file's ACs don't name the call site, reject the setup and send it back to PM/BA.
- **TEA must write a wiring test, not just unit tests.** Before handing off from TEA to Dev, verify at least one test exercises the production code path end-to-end. If every test stops at the component/library boundary, reject the phase exit.
- **Dev must verify non-test consumers before declaring GREEN.** Library functions with no production callers are stubs, not features. Before accepting Dev's assessment, grep for the new exports in non-test code.
- **Reviewer is the backstop, not the primary enforcement.** Every earlier phase must catch wiring gaps — if it reaches reviewer unwired, the whole chain failed and the incident should be logged as a process failure, not just a fix.

### Git / branch patterns
- **Gitflow on every subrepo.** Subrepos target `develop`, only the orchestrator targets `main`. Always check `repos.yaml` before any git op.
- **Additive git ops need no permission** (commit, push non-force, pull --ff-only, checkout existing, checkout -b, fetch, add). Keith explicitly asked me to stop being tentative with these.
- **Destructive git ops always ask first** — `reset`, `clean`, force-push, `branch -D`, `rebase -i`, `stash` (banned outright). Each has destroyed work in a past incident.
- **Dirty work comparison pattern.** When local uncommitted changes conflict with a pull: commit dirty work to a temp branch, pull clean on the default branch, diff each file local-vs-remote side by side, categorize (identical / remote better / local has extra value / no remote change), cherry-pick deliberately. Never stash.
- **When a hook blocks a commit**, the working tree is fine. Run `git status`. Changes are still there. Fix the issue (wrong branch, etc.) and recommit. Don't stash, don't blame a linter, don't assume code was lost.

### Playtest coordination
- **Pingpong cadence: every 2-3 minutes during active playtest.** Read `/Users/keithavery/Projects/sq-playtest-pingpong.md` frequently. New `open` items at the top are new bugs from OQ-1 — don't let them pile up.
- **Update pingpong status immediately when a fix lands** — not in batches. `open` → `in-progress` → `fixed` → `verified`.
- **Rotate the pingpong at natural breakpoints.** When all tasks are fixed/verified and dev is idle, archive to `/Users/keithavery/Projects/sq-playtest-archive/{timestamp}.md` and start fresh.
- **Always pull and test on new commits.** When `git log HEAD..origin` shows new commits during playtest: pull → rebuild → restart → test. No "want me to?" prompts.
- **Always rebuild on restart.** Every service restart during playtest is a full rebuild. Compile time is negligible vs debugging a stale binary.
- **Keep going.** Work through the checklist autonomously during playtest — don't pause to ask "want me to continue." Keith wants momentum.
- **Restart in existing tmux panes** via Ctrl+C + re-run. Don't close/reopen panes.

### Context discipline (SM's particular responsibility during high-ceremony sessions)
- **Thoroughness over speed.** Context pressure is not my problem — the system manages it via TirePump, relay, `/clear`. Don't rush a handoff, skip subagent results, or abbreviate a gate check to save tokens. Cutting corners costs more context than doing it right. If a gate fails because I cut corners, the whole phase repeats.
- **The right response to high context is a clean handoff, not a rushed one.** Complete the assessment, run the exit protocol, trust relay mode.

## Migrated from auto-memory (2026-05-26)

- **SideQuest runs kanban, not scrum — sprints have NO capacity.** Never frame proposals as capacity-budget trades ("we're at 18 pts, drop 2") or invoke velocity/remaining-capacity. Points remain useful as a complexity/effort estimate that informs ordering and flags fat stories to split. The scheduling question is "is this worth doing now?", not "do we have room?"

### Claude Design handoff bundles (`/design/h/` URLs)
- **When Keith gives a `https://api.anthropic.com/v1/design/h/<id>?open_file=...` URL, it's a Claude Design handoff.** WebFetch on it returns a **gzip tarball** (the model sees garbage; the bytes are saved to a `webfetch-*.bin` in the tool-results dir). Extract with `tar -xzf <bin> -C <tmpdir>` — do NOT try to read the raw fetch output.
- **Read order inside the bundle (the README states it):** `README.md` → `chats/chat1.md` (intent lives here — the user's questions-answered + where they landed) → `project/CLAUDE.md` (the LOCKED design system) → `project/<name>.dc.html` (the prototype; `?open_file=` names the primary one) → `project/screenshots/*.png` (target visuals). The `.dc.html` uses `sc-if`/`sc-for`/`x-dc` template syntax + `React.createElement` charts — a PROTOTYPE on synthetic seeded data, not production code.
- **Stash the bundle durably** under `docs/design-bundles/<YYYY-MM-DD>-<slug>/` (tracked; existing convention — `2026-05-23-lore-and-rules` was the first). `/tmp` is ephemeral; Dev needs it committed-adjacent. Put the design path in the session file's Design Source section.
- **The load-bearing scoping trap:** prototypes render fabricated data; the real target binds to LIVE telemetry/state. The story MUST bind the *visual treatment* to real data and either wire missing fields (server) or omit them — **never fabricate to fill the design**. For the Inspector this is epic 124's explicit "render only real fields" rule. Name this constraint in the ACs at setup; it's what decides repos (often server+ui) and story size.
- **My lane stays SM:** fetch + read + scope + stash + create story + sm-setup + route. I do not implement the `.dc.html` myself even when Keith says "implement" — that's Dev. The design read is discovery, not authoring.
