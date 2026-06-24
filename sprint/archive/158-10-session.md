---
story_id: "158-10"
jira_key: ""
epic: ""
workflow: "trivial"
---
# Story 158-10: Replace static 'crack in the hillside' chargen establishing template — off-geography for a winch-shaft world

## Story Details
- **ID:** 158-10
- **Jira Key:** (none — no Jira integration)
- **Workflow:** trivial
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-24T00:12:22Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-23T23:58:20Z | 2026-06-24T00:00:20Z | 2m |
| implement | 2026-06-24T00:00:20Z | 2026-06-24T00:07:22Z | 7m 2s |
| review | 2026-06-24T00:07:22Z | 2026-06-24T00:12:22Z | 5m |
| finish | 2026-06-24T00:12:22Z | - | - |

## Sm Assessment

**Story type:** Content-only bug (trivial workflow, 1pt, p3). Single repo: `content` (sidequest-content), targets `develop`.

**What's wrong:** The chargen "establishing" narration for `caverns_and_claudes/worlds/beneath_sunden` opens with a static "crack in the hillside" template. That geography is wrong for this world — beneath_sünden is entered by a *winch-shaft* (mechanical descent), not a natural fissure. Surfaced in the 2026-06-22 full-stack /sq-playtest sweep (epic-158 follow-ups).

**Acceptance criterion:** Chargen establishing text no longer reads "crack in the hillside" and instead reflects the winch-shaft descent, consistent with beneath_sünden's geography. Verify the override actually loads (content layering / world resolution), not just that a file exists — no half-wired feature.

**Approach pointer (for Dev — not a mandate):** sm-setup located the source as the `the_mouth` chargen scene narration, pack-level default in caverns_and_claudes. The likely fix is a world-scoped override at `genre_packs/caverns_and_claudes/worlds/beneath_sunden/char_creation.yaml`. Dev owns confirming the exact static string and the correct layering point.

**Routing:** Phased trivial workflow → hand off to Dev (Hephaestus the Smith) for the implement phase. No design/architecture phase needed.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-content/genre_packs/caverns_and_claudes/char_creation.yaml` — rewrote the `the_mouth` chargen establishing narration: replaced the off-geography "crack in the hillside" (and the off-geography "the town is already forgetting your name" — Ropefoot is canonically "not a town") with the winch-shaft descent — the Dropmouth collar, the rope/drum/pawl of the winch, and Ropefoot's fire and board of burned-in names. Grim closing cadence preserved.

**Acceptance criterion met:** Chargen establishing text no longer reads "crack in the hillside" and now reflects the winch-shaft descent, consistent with beneath_sünden's canon geography (Dropmouth / Ropefoot / winch — cross-checked against world.yaml + openings.yaml + npcs.yaml).

**Wiring verified (not just existence):**
- YAML parses; pack validator `validate pack caverns_and_claudes` → PASS (0 errors; 13 pre-existing warnings).
- End-to-end through the server's real loader: `load_genre_pack()` + `resolve_char_creation_scenes(pack, 'beneath_sunden')` returns all 5 scenes intact and resolves the **new** `the_mouth` narration via pack fallback (beneath_sünden has no world override). Old string no longer resolves; "Dropmouth"/"Ropefoot" present.

**OTEL:** N/A — pure content-prose change, no subsystem decision logic (CLAUDE.md exempts cosmetic/content from the OTEL-on-every-subsystem rule).

**Tests:** Trivial workflow — no TEA RED suite. Verification is the validator + end-to-end resolve above.
**Branch:** `feat/158-10-winch-shaft-chargen` (sidequest-content, targets `develop`) — pushed.

**Handoff:** To review phase (Hermes Psychopompos).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (pack validates 0 errors; YAML parses; tree clean) | N/A |
| 2 | reviewer-edge-hunter | Yes | clean | none (UTF-8 ü/em-dash round-trip OK; block-scalar indent + blank line + trailing newline all preserved) | N/A |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | Yes | clean | none (no security surface; static authored content, not user input) | N/A |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings |

**All received:** Yes (3 enabled subagents returned, all clean; 6 disabled via `workflow.reviewer_subagents` settings)
**Total findings:** 0 confirmed, 0 dismissed, 0 deferred

## Reviewer Review

### Rule Compliance

Diff governs exactly one entity: the `the_mouth` chargen scene's `narration` block scalar. Enumerating every applicable project rule against it:

- **SOUL.md "The Test" (player never does something they didn't ask to):** COMPLIANT. The narration is pure world/scene description ("The mouth of Sünden Deep is the Dropmouth…", "Behind you, Ropefoot keeps its small fire"). It never narrates a player action, thought, or feeling. The removed line ("the town is already forgetting your name") was also world-description; the replacement preserves that stance. — evidence: char_creation.yaml:126–132.
- **SOUL.md "Agency":** COMPLIANT. Describes the world, not the player's response to it.
- **SOUL.md "Crunch in the Genre, Flavor in the World":** Geography (winch-shaft) is world flavor and now lives in content that is functionally beneath_sünden's (broker = Brecca Half-Hand, a beneath_sünden NPC). The pack-tier placement is the subject of Dev's audited-and-accepted deviation. COMPLIANT in spirit given the sole-world reality; forward-impact tracked.
- **SOUL.md "Diamonds and Coal" (detail scaled to weight):** COMPLIANT. Two short paragraphs, same length/weight as the original establishing scene — not overbaited.
- **SOUL.md "Genre Truth":** COMPLIANT. Grim, terse register matches both the original `the_mouth` scene and beneath_sünden's tone.
- **CLAUDE.md "No Silent Fallbacks":** COMPLIANT — this is the opposite of a fallback; no string/path defaulting introduced.
- **CLAUDE.md OTEL principle:** N/A by exemption — "Not needed for: Cosmetic UI changes." A content-prose string carries no subsystem decision logic. No OTEL owed.
- **CLAUDE.md "No half-wired features":** COMPLIANT — verified end-to-end that the new text actually resolves for beneath_sünden via the real loader (see observations).

### Observations (6)

1. **[VERIFIED] Old off-geography string fully removed** — evidence: `git diff develop...HEAD` shows "crack in the hillside" and "the town is already forgetting your name" both deleted; `grep` for "crack in the hillside" across genre_packs returns nothing. Complies with the AC.
2. **[VERIFIED] New geography is 100% canon, not invented** — every proper noun/term independently grounded in beneath_sünden world files: `Dropmouth` = cartography region `the_dropmouth` (world.yaml:12, cartography.yaml:5); `Ropefoot` (11 files); `pawl`/`drum`/`scoured` (6/8/5 files); `board of burned-in names` = Brecca burning names onto the tally board (npcs.yaml:72–73, 90, 105). No hallucinated geography.
3. **[VERIFIED] Wiring proven end-to-end, not just file-exists** — `load_genre_pack()` + `resolve_char_creation_scenes(pack,'beneath_sunden')` returns all 5 scenes and serves the NEW `the_mouth` via pack fallback (beneath_sünden has no override). Re-confirmed by preflight pack-validate PASS (0 errors).
4. **[EDGE][VERIFIED] Non-ASCII safe** — `ü` (U+00FC) and em-dash `—` (U+2014) round-trip through `yaml.safe_load`; block-scalar 4-space indent, inter-paragraph blank line, and single trailing newline all preserved (clip mode unchanged). Scene `id`/`title`/`choices`/`allows_freeform` untouched.
5. **[SEC][VERIFIED] No security surface** — static authored content, not user input; no injection sink, secret, or unsafe interpolation introduced. Confirmed by reviewer-security (clean).
6. **[SIMPLE][VERIFIED] Minimal, no scope creep** — single 7+/5- line diff, one scene, no new files or abstractions; rejects the heavier world-override path that would have duplicated 4 scenes. Confirmed by Dev's audited deviation.

### Devil's Advocate

Let me argue this change is broken. *First attack — encoding.* The prose introduces a `ü` and an em-dash into a YAML file; if any downstream consumer (a reference page, a prompt template, an export) assumed ASCII or used a non-UTF-8 codec, the chargen scene could render as mojibake or throw a `UnicodeDecodeError` mid-session. *Rebuttal:* the loader is the same one that already serves dozens of `ü`/`—`-bearing strings across these packs (Sünden appears in 14 files); the edge-hunter confirmed clean round-trip, and the_mouth narration is displayed, not slugified into an anchor (so the ASCII-slug reference-page path doesn't touch it). *Second attack — canon contradiction.* The new text asserts "the rope already run to the drum, the winch's pawl holding it fast," but openings.yaml says the winch-keeper has "the drum locked off for the night" — does chargen now contradict the opening? *Rebuttal:* a pawl holding the rope fast IS the drum locked off; these describe the same rigged-but-not-yet-descending state, not a contradiction. The genuine seam — chargen says "Dawn" while the opening is staged at night — is real but pre-existing and out of this story's scope; Dev logged it as a non-blocking finding rather than silently "fixing" it, which is correct. *Third attack — a confused player.* Could "the Dropmouth" read as an unexplained proper noun that disorients a fresh character? *Rebuttal:* it's immediately apposed ("the mouth of Sünden Deep is the Dropmouth — a collar of scoured stone…"), so the term is self-defining in the sentence, and it's the world's cover POI the player will see imaged. *Fourth attack — did we drop something load-bearing?* The old line carried "moss and old tooth-marks in the stone," hinting at a living/monstrous mouth. *Rebuttal:* that hint actively mis-set a *mechanical winch-shaft* world; dropping it removes a false bait (Diamonds and Coal: don't bait empty water), and the grim closing cadence ("swallowed better than you") is preserved intact. Nothing load-bearing was lost; the change strictly improves geographic truth. No new finding surfaces.

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** authored `the_mouth.narration` (char_creation.yaml) → `load_genre_pack()` → `resolve_char_creation_scenes(pack,'beneath_sunden')` → chargen scene served to the player. Safe because the value is static authored content (not user input), resolves via the documented pack-fallback path with all 5 scenes intact, and the pack validates with 0 errors.

**Pattern observed:** minimal in-place content fix at the correct resolution tier (pack-tier file is already beneath_sünden-specific via Brecca) — char_creation.yaml:123–133.

**Error handling:** N/A for a static content string; loader/validator confirm no parse or load error (preflight PASS, 0 errors).

**Subagent dispatch:** [EDGE] clean (encoding/indent/scalar integrity verified) · [SEC] clean (no security surface) · [SILENT] skipped (disabled via settings) · [TEST] skipped (disabled; trivial workflow has no test suite) · [DOC] skipped (disabled; no public API/docs in a content string) · [TYPE] skipped (disabled; no types in YAML prose) · [SIMPLE] skipped (disabled; change is already minimal) · [RULE] skipped (disabled; rule compliance enumerated manually above — all applicable SOUL.md/CLAUDE.md rules COMPLIANT).

**Deviation audit:** Dev's pack-tier-vs-override deviation independently verified and ACCEPTED; no undocumented deviations.

**No Critical/High findings.** AC met, canon-grounded, wired end-to-end.

**Handoff:** To SM (Themis the Just) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Improvement** (non-blocking): The entire caverns_and_claudes pack-tier `char_creation.yaml` (Brecca frame, the_calling→the_mouth) is beneath_sünden-specific content sitting at the genre tier only because beneath_sünden is the sole world. Affects `genre_packs/caverns_and_claudes/char_creation.yaml` (lift the whole Brecca chargen flow into a `worlds/beneath_sunden/char_creation.yaml` override **if/when** a second, generic caverns world is added — not before, to avoid wholesale-replace duplication). *Found by Dev during implementation.*
- **Improvement** (non-blocking): The chargen `the_mouth` scene opens with "Dawn." while the world's turn-1 opening (`worlds/beneath_sunden/openings.yaml`) is staged at night ("drum locked off for the night"). Pre-existing, out of scope for this story (story scope is the hillside-crack geography only). Affects `genre_packs/caverns_and_claudes/char_creation.yaml` + `openings.yaml` (reconcile time-of-day if a future story touches the chargen→opening seam). *Found by Dev during implementation.*

### Reviewer (code review)
- No upstream findings during code review. (Dev's two non-blocking Improvements above are confirmed accurate and sufficient; the time-of-day one is correctly scoped out. Nothing further to add.)

## Impact Summary

**Upstream Effects:** 1 findings (0 Gap, 0 Conflict, 0 Question, 1 Improvement)
**Blocking:** None

- **Improvement:** The entire caverns_and_claudes pack-tier `char_creation.yaml` (Brecca frame, the_calling→the_mouth) is beneath_sünden-specific content sitting at the genre tier only because beneath_sünden is the sole world. Affects `genre_packs/caverns_and_claudes/char_creation.yaml`.

### Downstream Effects

- **`genre_packs/caverns_and_claudes`** — 1 finding

### Deviation Justifications

1 deviation

- **Edited the pack-level `char_creation.yaml` in place instead of creating a world-scoped override**
  - Rationale: `char_creation_resolve.py` resolves world char_creation as a **wholesale replacement** of the pack list (documented: "There is no merge"). A world override would therefore have to duplicate all 5 scenes to change 1. Crucially, the pack-tier chargen is *already* beneath_sünden-specific — its broker NPC is **Brecca Half-Hand, the winch-keeper**, a beneath_sünden world NPC (worlds/beneath_sunden/npcs.yaml), and `beneath_sunden` is the **only** world in the pack (no generic caverns world exists to be harmed). So "Flavor in the World" is already satisfied at the pack tier; an override would add ~110 lines of duplicated Brecca content and real drift debt for zero benefit. Editing in place is the minimal correct fix.
  - Severity: minor
  - Forward impact: minor — if a *second*, genuinely generic caverns_and_claudes world is ever added, `the_mouth` (and the whole Brecca frame) would need lifting into a beneath_sunden world override at that time. Tracked below as a non-blocking Delivery Finding.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Edited the pack-level `char_creation.yaml` in place instead of creating a world-scoped override**
  - Spec source: .session/158-10-session.md → Sm Assessment, "Approach pointer"
  - Spec text: "The likely fix is a world-scoped override at `genre_packs/caverns_and_claudes/worlds/beneath_sunden/char_creation.yaml`." (explicitly flagged "not a mandate"; "Dev owns confirming … the correct layering point")
  - Implementation: Changed the `the_mouth` scene narration directly in `genre_packs/caverns_and_claudes/char_creation.yaml` (the pack-tier default). No world override file created.
  - Rationale: `char_creation_resolve.py` resolves world char_creation as a **wholesale replacement** of the pack list (documented: "There is no merge"). A world override would therefore have to duplicate all 5 scenes to change 1. Crucially, the pack-tier chargen is *already* beneath_sünden-specific — its broker NPC is **Brecca Half-Hand, the winch-keeper**, a beneath_sünden world NPC (worlds/beneath_sunden/npcs.yaml), and `beneath_sunden` is the **only** world in the pack (no generic caverns world exists to be harmed). So "Flavor in the World" is already satisfied at the pack tier; an override would add ~110 lines of duplicated Brecca content and real drift debt for zero benefit. Editing in place is the minimal correct fix.
  - Severity: minor
  - Forward impact: minor — if a *second*, genuinely generic caverns_and_claudes world is ever added, `the_mouth` (and the whole Brecca frame) would need lifting into a beneath_sunden world override at that time. Tracked below as a non-blocking Delivery Finding.

### Reviewer (audit)
- **Dev deviation: pack-tier edit instead of world override** → ✓ ACCEPTED by Reviewer. I independently verified the load path: `resolve_char_creation_scenes(pack, 'beneath_sunden')` returns all 5 scenes from the pack tier (no world override exists), confirming wholesale-replace semantics — a world override would indeed duplicate 4 unchanged scenes. I also confirmed the pack chargen is already beneath_sünden-specific: the broker is **Brecca Half-Hand**, a beneath_sünden world NPC (npcs.yaml). The strict "Crunch in the Genre, Flavor in the World" reading would prefer geography in a world file, but with exactly one world and the pack content already world-bound, an override buys nothing and adds drift debt. Editing in place is the minimal correct fix. The forward-impact (a future generic world needs the lift) is correctly tracked as a non-blocking Delivery Finding. No reversal required.
- No undocumented deviations found: the diff changes only the `the_mouth` narration string; scene `id`/`title`/`choices`/`allows_freeform` are untouched, and no other scene or file diverged from spec.