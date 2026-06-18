---
id: 149
title: "Ruleset-Tier SRD Reference Content and the rules_document Reference Section"
status: accepted
date: 2026-06-18
deciders: ["Keith Avery", "Architect"]
supersedes: []
superseded-by: null
related: [135, 145, 142, 144]
tags: [core-architecture, frontend-protocol]
implementation-status: live
implementation-pointer: "sidequest-server sidequest/genre/ruleset_reference.py (load/compose/gate) + sidequest/server/reference_projection.py (prepends the section); sidequest-content rulesets/fate/srd/*.md; sidequest-ui RulesDocument.tsx"
---

# ADR-149: Ruleset-Tier SRD Reference Content and the rules_document Reference Section

> Extends (does not replace) **ADR-135**. ADR-135 governs the audience doctrine
> and public projection for all reference pages — one fixed public projection, no
> GM mode. This ADR adds a new *kind* of reference section to that surface: prose
> derived from the bound SRD itself, rendered by a dedicated React component
> (`RulesDocument`). Everything in ADR-135's Decision still holds; this ADR records
> the content tier, the front-matter contract, the fail-loud load gate, and the
> licensing/attribution rules for that section.

## Context

The four Fate genres (`pulp_noir`, `tea_and_murder`, `wry_whimsy`,
`spaghetti_western`) bind Fate Core (ADR-144). The Without Number family binds four
SRDs (ADR-142/143). In both cases the binding's value is that the ruleset is
*already balanced* — we never re-author or re-tune the math. But a player at the
table still has to know the rules. Today they have no in-app source: the reference
page (ADR-135) surfaces rules *stubs* derived from the genre YAML, not the full
SRD prose. There is no page on the surface where a player can read "here is how
Overcome works" or "here is how an attack roll resolves" without leaving the app.

The only complete, authoritative source for those rules is the SRD documents
themselves. Both Fate Core and the Without Number line carry permissive terms (see
ADR-145 for the licensing specifics): Fate Core under CC-BY 3.0 (Evil Hat
Productions), the WN family under the "free for any use" WN SRD policy (Sine
Nomine Publishing). Both can be reproduced verbatim in the app; neither requires
compensation or approval; both require attribution.

The gap is content, not plumbing: the reference projection already prepends
structured sections from server data; the projection pipeline can prepend one more
section whose *body* comes from versioned SRD prose files rather than from game
state. The render substrate (ADR-135 Amendment, epic 100) already routes that JSON
payload to a React renderer per section `type`.

## Decision

### 1. New content tier: `rulesets/<ruleset>/srd/*.md`

SRD prose lives in a new first-class content tier under
`sidequest-content/rulesets/<ruleset>/srd/`.

- **This is the first content that is neither genre-tier nor world-tier.** Genre
  and world files govern packs and worlds; this tier governs the *ruleset* itself
  — a shared resource across all packs that bind the same module. The path is
  parallel to the `sidequest-content/genre_packs/` tree, not nested inside it.

- **Phase 1: Fate.** The initial content tree is
  `rulesets/fate/srd/*.md` — 7 player-facing chapters: The Basics, Character
  Creation, Aspects and Fate Points, Skills and Stunts, Actions and Outcomes,
  Challenges/Contests/Conflicts, and The Long Game (advancement). These are the
  chapters a player needs to understand play; the GM-only chapters (Running the
  Game; Scenes, Sessions, and Scenarios) and the Game Creation and Extras
  chapters are out of scope for Phase 1.

- **Plan B: Without Number.** The Without Number family (wwn, cwn, swn, awn) shares
  a common resolution spine, so WN content would live in
  `rulesets/without_number/core/srd/*.md` with per-game overlay directories
  (e.g., `rulesets/without_number/cwn/srd/*.md`). Overlays override core by
  matching `anchor` key (see §2). WN is not gated (not in `RULESETS_WITH_REFERENCE`
  — §4) for Phase 1; it is a content-only follow-on requiring no engine changes.

### 2. Front-matter contract

Every SRD `.md` file MUST carry YAML front-matter with these six keys:

```yaml
---
srd: fate                                 # ruleset slug; must match a registered RulesetModule
srd_ref: "Fate Core System — The Basics"  # descriptive per-chapter SRD reference (for attribution)
license: ccby                             # license slug: ccby (Fate, CC-BY 3.0) | wn-free (Without Number)
anchor: fate-basics                       # stable machine key — identifies this chapter globally
title: "The Basics"                       # human-readable heading shown in the ToC
order: 1                                  # integer; controls display order within the ruleset
---
```

The server fails **loud** (`GenreLoadError`) on any of these six keys missing or
blank. Partial/malformed front-matter is an error, not a skip. This upholds the No
Silent Fallbacks principle: if SRD content is present but unstamped, the pack must
not load silently with a broken reference section.

The `anchor` key doubles as the overlay merge key for the WN overlay model: a WN
overlay file with `anchor: stress` replaces the core file with the same anchor
rather than appending a second section.

### 3. The `rules_document` reference section

The projection pipeline (`build_rules_projection` in `reference_projection.py`)
gains a new section type prepended before the existing rules stubs:

```json
{
  "id": "ruleset_reference",
  "type": "rules_document",
  "label": "The Rules of Fate Core",
  "ruleset": "fate",
  "chapters": [
    { "anchor": "fate-basics", "title": "The Basics", "order": 1, "srd_ref": "Fate Core System — The Basics", "body_markdown": "..." },
    ...
  ],
  "provenance": { "source": "Fate Core System (Evil Hat Productions)", "license": "ccby", "attribution": "..." }
}
```

Discriminator: `type: "rules_document"`. The top-level `label` is the static
human-readable ruleset title (from `RULESET_LABEL[ruleset]`), and licensing lives
in the nested `provenance` object (`source`/`license`/`attribution`). The React
renderer dispatches on this discriminator to the `RulesDocument` component, which
renders each chapter's `body_markdown` via **react-markdown** and emits one
`<article id={anchor}>` per chapter. The ToC is derived externally by
`buildToc` (`screens/reference/buildToc.ts`), which maps the section's `chapters`
to one navigable ToC entry each — so the ADR-135/100 ToC/anchor framework applies
without modification.

The section is prepended (it leads the page) so a first-time player lands on the
rules before the genre-derived stubs. The existing stubs follow; they are not
removed.

### 4. Fail-loud load gate: `RULESETS_WITH_REFERENCE`

A server-side set — `RULESETS_WITH_REFERENCE` — names the rulesets for which SRD
reference content is *required*:

- **Phase 1:** `RULESETS_WITH_REFERENCE = {"fate"}`

Rules at load time (`ruleset_reference.py`, called from the pack loader):

1. If the bound ruleset is in `RULESETS_WITH_REFERENCE` and no SRD files are
   found, or any discovered file fails the front-matter check → raise
   `GenreLoadError` immediately. The pack does not load.
2. If the bound ruleset is **not** in `RULESETS_WITH_REFERENCE` (e.g., `wwn`,
   `cwn`, `swn`, `awn`, `native`) and no SRD files are present → emit no
   `rules_document` section (no section gap, no error). This is Plan B's no-break
   path.
3. If SRD files are present for an ungated ruleset → load and surface them
   normally (permissive: content authors can add WN content before the gate is
   promoted).

This gives a two-speed rollout: Fate ships with a hard invariant enforced at load
time; WN follows as a content PR with no engine change needed.

### 5. ADR-145 attribution and non-endorsement rule

Both SRDs may be reproduced verbatim. Both carry attribution requirements. The
`srd_ref` front-matter field and the `attribution` field in the projection section
carry the required notice. The rendered `RulesDocument` component displays the
attribution string in a styled attribution block below the ToC.

**Non-endorsement invariant** (required by both licenses and stated policy):

> Attribution MUST NOT imply endorsement, partnership, approval, or review by Evil
> Hat Productions (Fate Core / CC-BY 3.0) or by Sine Nomine Publishing / Kevin
> Crawford (Without Number SRD / free-use policy). The attribution block states
> the source and license; it does not claim any relationship beyond "content
> reproduced under [license]."

This is a hard content rule: no marketing copy, no "official," no "endorsed by" in
any SRD-attributed text in the app.

Concretely, Phase 1 attribution text for Fate:

> *Fate Core System* is a product of Evil Hat Productions, LLC.
> © 2013 Evil Hat Productions, LLC. Licensed under Creative Commons Attribution
> 3.0 Unported (CC-BY 3.0). This content is reproduced under that license; it is
> not affiliated with, approved, or endorsed by Evil Hat Productions.

## Consequences

**Positive:**

- Players can read the rules they are playing under without leaving the app — the
  most direct answer to Sebastien/Jade's "we want to know the rules" mandate
  (CLAUDE.md player-facing legibility).
- SRD prose is versioned as content (YAML + Markdown), not engine code — authors
  can update it via PR with no server change, consistent with the homebrew thesis.
- The fail-loud gate (`RULESETS_WITH_REFERENCE`) makes the Fate reference section
  an invariant of the pack load: a Fate genre pack without SRD content is an error,
  not a missing feature.
- The Phase 1 / Plan B split lets the Without Number family follow as a pure
  content addition — no engine promotion required.
- The React renderer (`RulesDocument` + react-markdown) composes with the existing
  ToC/anchor framework; no new navigation infrastructure.

**Negative / accepted:**

- A new content tier (`rulesets/`) adds a second content root alongside
  `genre_packs/`. Authors must understand the distinction: genre/world files go in
  `genre_packs/`, ruleset-level SRD prose goes in `rulesets/`. Mitigated by the
  fail-loud gate catching misplaced/unstamped files at load time.
- The six-key front-matter requirement is strict — a missing key errors the entire
  pack load, not just the individual chapter. This is the intended behavior
  (No Silent Fallbacks), but it means a partial/in-progress SRD migration fails
  loudly. Mitigation: the gating set (`RULESETS_WITH_REFERENCE`) is the rollout
  dial; ungated rulesets can have partial content without blocking load.
- WN content (Plan B) is deferred. Sebastien/Jade's Without Number table has no
  in-app rules reference until WN content is authored. Accepted — it's a content
  PR, not an engine gap.

## Phasing

**Phase 1 (this ADR, live):**
- Engine: `ruleset_reference.py` (load / compose / gate), `reference_projection.py`
  (prepend `rules_document` section), `RulesDocument.tsx` (React prose renderer).
- Content: `rulesets/fate/srd/*.md` — 7 chapters, Fate Core CC-BY 3.0.
- Gate: `RULESETS_WITH_REFERENCE = {"fate"}`.
- Tests: fixture-tests for the load/compose pipeline; `RulesDocument` Vitest
  snapshot; integration test verifying Fate pack loads with the section present.

**Plan B (content-only follow-on, no gate promotion required):**
- `rulesets/without_number/core/srd/*.md` + per-game overlays.
- Add `wwn`/`cwn`/`swn`/`awn` to `RULESETS_WITH_REFERENCE` once content is
  complete.
- No engine changes; content PR only.

## Cross-references

- **ADR-135** (Reference Pages Are a Public Table Tool): this ADR extends the
  reference projection with a new section type. ADR-135's audience doctrine
  (one fixed public projection, no GM mode) applies unchanged to this section.
- **ADR-145** (SRD-Sourced Inventory): establishes the verbatim-reproduce licensing
  basis for both the WN and Fate SRDs used here. The attribution/non-endorsement
  rule in §5 carries forward ADR-145's "free to reproduce; do not imply
  endorsement" principle from inventory to reference prose.
- **ADR-142** (Without Number Core Extraction): the core+overlay composition model
  for Plan B WN content mirrors the WN module structure described there.
- **ADR-144** (Fate Core Binding): Phase 1 Fate content is the reference companion
  to the Fate ruleset binding. Together they make the bound ruleset legible
  end-to-end: engine knows the math, players can read it.
