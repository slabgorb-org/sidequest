# Playtest Phase 0 — "What Changed Since Last Playtest" Manifest

**Date:** 2026-06-04
**Status:** Approved (brainstorming) — built directly (right-sized: read-only script + skill edit, no sprint epic)
**Author:** Orchestrator (DEATH) — meta-tooling for the `sq-playtest` skill

---

## 1. Problem

The `sq-playtest` skill walks the operator into a session **blind**. It launches the
stack and opens the browser, but never answers the two questions that should frame any
playtest: *when did we last play, and what has landed since that we have not yet
exercised?* Untested work is the cheapest debt to accrue and the most expensive to
repay — a charmed-prose narrator can hide a dead subsystem for a whole session if nobody
knew to look at it.

Nothing today records "last playtest" cleanly. Archives are scattered (some in
`~/Projects/sq-playtest-archive/`, the newest loose in `~/Projects/`), the live ping-pong
file resets each session, and "what shipped" is spread across sprint commits, PRs, specs,
plans, and raw subrepo churn.

## 2. Goals / Non-goals

**Goals**
- A **Phase 0** that runs before stack launch and prints a tiered *test manifest*.
- Anchor "last playtest" on the **newest archive file by mtime**, globbing **both**
  scatter locations, excluding the live file.
- Fold in **five** sources, tiered so they do not drown each other.
- Deterministic, read-only, fail-loud. No state mutation, no silent fallbacks.

**Non-goals**
- No new bookkeeping ritual (no marker file, no git tag) — rides on existing artifacts.
- No coupling to the nascent `docs/feature-inventory/*.yaml` generator (future feed).
- No automatic prioritization — the script gathers; the agent judges.

## 3. Architecture

One read-only gatherer + a thin skill phase.

- **`scripts/playtest_manifest.py`** — stdlib-only. Gathers and prints; never writes.
  Text-to-operator by default; `--json` opt-in. Pure parse functions are unit-tested
  against fixtures; IO (git/gh/fs) is thin and defensive.
- **`SKILL.md` → new `## Phase 0`** — "run the script, read the manifest to the operator,
  propose a test order (Tier 2 unverified fixes first, then Tier 1 features touching the
  world about to be played)."

## 4. The anchor (load-bearing correctness)

Archives are scattered. The newest file *inside* `sq-playtest-archive/` is stale (May 31)
while the real most-recent archive (`sq-playtest-pingpong-archive-2026-06-04.md`) sits
loose in `~/Projects/`. The anchor therefore globs a **union**:

- `~/Projects/sq-playtest-archive/*` (the archive dir, any extension)
- `~/Projects/sq-playtest-pingpong*archive*.md` and `~/Projects/sq-playtest-pingpong*.bak` (loose)

…**excluding** the live `~/Projects/sq-playtest-pingpong.md`, and takes the newest by
**mtime**. The mtime's date is the anchor; the filename is parsed **best-effort for a human
label only** (`glenross-coyote`), never for the date. Empty union → **loud non-zero exit**
("no prior playtest archive — first playtest, or archive dir moved"), never a silent
"0 days".

## 5. The five sources, tiered

**Tier 1 — Features to test** (what landed since the anchor)
- **Sprint completions** — `git -C . log --since=ANCHOR --grep='chore(sprint): complete'`.
  Format is stable: `complete {id} — {title} (PR {ref})`. Parse id, title, PR ref.
- **Merged PRs** — per subrepo, `gh pr list -R slabgorb/<repo> --state merged
  --search 'merged:>=ANCHOR' --json number,title,mergedAt`. **Deduped** against PR numbers
  already named by a sprint story; the remainder lists as "PRs without a sprint story."
- **Designs landed** — `docs/superpowers/{specs,plans}/**.md` whose `YYYY-MM-DD` filename
  prefix `>= ANCHOR`, tagged **shipped** (`completed/` subdir) vs **in-flight** (root).

**Tier 2 — Unverified fixes** (verify FIRST) — parse the **live** ping-pong file into task
blocks (`^### [TAG] title` + the `- **Status:**` line); surface every `open` and
`fixed`-awaiting-verify item. These are fixes that landed but were never confirmed in play —
the highest-signal targets.

**Tier 3 — Coverage backstop** — per subrepo, `git log --since=ANCHOR --oneline` **counts**.
Flags subrepos with commits not traceable to a Tier-1 story/PR ("untracked churn, eyeball
this"). Never merged into Tier 1 — it cannot drown the feature list.

## 6. Dedup strategy

Stories, PRs, and specs share identifiers (`77-2`, `#621`, topic slug). Tier 1 keeps three
labelled subsections rather than a fragile full fusion: sprint stories carry their PR ref;
merged PRs are filtered to drop numbers a story already named; designs list separately.
Cross-repo PR-number collision is possible in the dedup filter — accepted, noted in output.

## 7. Error handling — No Silent Fallbacks

- Empty archive union → loud non-zero exit.
- `gh` unavailable/unauthed → PR section prints **`SKIPPED: gh unavailable`**, not an empty
  omission. (`gh` is always invoked under `env -u GITHUB_TOKEN` per the keyring gotcha.)
- Missing subrepo → loud per-repo line; other repos continue.

## 8. Testing

- Unit: anchor selection (scatter + exclude-live + empty→raise), sprint-line parse,
  ping-pong block parse, spec/plan date+location tagging, PR dedup filter — against tmp
  fixtures, stdlib `assert`, runnable as `python3 scripts/test_playtest_manifest.py`.
- Smoke / wiring: run the real script against the repo, assert exit 0 and a non-empty
  manifest with all three tier headers — proves it is reachable and parses live data.

## 9. Out of scope / future

- Feed the `docs/feature-inventory/*.yaml` ledger once that generator matures.
- A `--world <slug>` filter to rank Tier 1 by relevance to the world being played.
