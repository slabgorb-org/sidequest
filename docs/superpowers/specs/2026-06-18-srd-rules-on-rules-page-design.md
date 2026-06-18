# SRD Rules on the Rules Page — Shared Ruleset Reference (Phase 1)

- **Date:** 2026-06-18
- **Status:** Design (brainstorming output) — awaiting review
- **Related ADRs:** ADR-135 (Reference Pages Are a Public Table Tool), ADR-145 (SRD-Sourced Inventory — per-ruleset reproduce-vs-derive licensing), ADR-142 (Without Number Core Extraction), ADR-144 (Fate Core binding)
- **Discovered:** during a headed Gulliver (wry_whimsy / Fate Core) playtest, 2026-06-18 — "the players are going to need help with this stuff… players [need to] understand what is happening in the chargen."

## Problem

A player creating a character has no way to learn the system they are playing. The
character-creation flow throws Fate aspects, the Fate ladder, a skill pyramid, stunts (or, in
the Without Number packs, attributes / skills / foci / saves / the d20+skill check) at the
player with **zero explanation** — no tooltips, no "what is an aspect?", no link to any rules.
The chargen UI never even tells the player which ruleset they are in.

The Rules reference page (`/reference/rules/<pack>`, titled *"Rules of play"*) *looks* like it
should help, but its "Rules → Fate" / "Rules → Wwn" subsections are **raw YAML config dumps**
(the pack's skill list, refresh, stunts, gear / attribute_map, effort, initiative). They show
the pack's mechanical *knobs* and explain **nothing** about how the system actually works. A
player reading the page today learns no rules.

There is **no human-readable rules text anywhere in the repo** — not in content YAML, not in the
ruleset modules (which carry mechanical code + SRD section citations in comments, but no prose).

## Decisions (settled during brainstorming, 2026-06-18)

| Decision | Choice |
|---|---|
| **Depth** | Full **verbatim** SRD reproduction (not a hand-authored primer) |
| **Scope** | **Player-facing chapters only** — character creation, attributes/skills/foci, core resolution (d20+skill / 4dF), saves, combat, equipment, magic/psionics, advancement. **Excludes** GM-only material (running the game, factions, adventure/sandbox design, bestiary, GM advice). Fits ADR-135's player-tool framing. |
| **Surface** | **Phased.** Phase 1 (this spec): the Rules reference page. Phase 2 (separate later spec): in-chargen drawer + deep-links. |
| **Coverage** | **All five rulesets** — Fate + WWN + CWN + SWN + AWN. |
| **Architecture** | **Ruleset-tier shared content** + a new rules-document section type & prose renderer. The shared sections for Fate and the Without Number family **are the work.** |

## Goals

1. Reproduce the player-facing chapters of all five SRDs, verbatim, as **shared ruleset-tier**
   content — authored **once per ruleset**, not copied per pack.
2. Render that content on the existing Rules reference page as a readable rules document, slotted
   into the page's existing Table-of-Contents + anchor framework.
3. Stamp every reproduced section with provenance and the correct attribution per ADR-145, with
   **no implied Sine Nomine / Evil Hat endorsement**.
4. Lay the anchor groundwork so Phase 2 (chargen deep-links) is purely additive.

## Non-Goals (Phase 1)

- **No chargen integration** (drawer, deep-links, "ⓘ what is an aspect?"). Phase 2.
- **No GM-only chapters.**
- **No rewriting/paraphrasing** the SRD into our own words — this is faithful reproduction.
- **No removal** of the existing per-pack config sections — they coexist (see "Coexistence").
- **No new licensing model** — ADR-145 already rules reproduction permitted; we apply it.

## Ruleset → pack binding (the sharing payoff)

| Ruleset | Shared document | Packs served |
|---|---|---|
| **Fate** | one Fate Core doc | pulp_noir, spaghetti_western, tea_and_murder, wry_whimsy (4) |
| **WWN** | WN core + WWN overlay | caverns_and_claudes, elemental_harmony, heavy_metal (3) |
| **CWN** | WN core + CWN overlay | neon_dystopia, road_warrior (2) |
| **SWN** | WN core + SWN overlay | space_opera (1) |
| **AWN** | WN core + AWN overlay | mutant_wasteland (1) |

The WN **core** is shared by **7** packs; the one Fate doc serves **4**. Authoring is per-ruleset
(5 documents, one of them a core+overlays family), surfaced by 11 packs.

## Content model & tier

New ruleset-tier content layer in `sidequest-content`, sibling to `genre_packs/`:

```
sidequest-content/rulesets/
  fate/srd/
    01-the-basics.md
    02-aspects-and-fate-points.md
    03-skills.md
    04-stunts.md
    05-actions-and-outcomes.md
    06-challenges-contests-conflicts.md
    ...
  without_number/
    core/srd/            # shared WN player chapters
      01-attributes.md
      02-skills.md
      03-saving-throws.md
      04-the-skill-check.md      # 2d6+attr+skill core resolution
      05-effort.md
      06-combat.md
      07-equipment.md
      ...
    wwn/srd/             # WWN-only player chapters / overrides (foci, Arts/magic, classes)
    cwn/srd/             # CWN-only deltas
    swn/srd/             # SWN-only deltas (psionics, ship basics)
    awn/srd/             # AWN-only deltas
```

**Sub-decision A — chapter format = Markdown + YAML front-matter.** Verbatim chapter prose
(headings, tables, lists) is what Markdown is for; the existing card/node-tree projection is
wrong for long prose. Each file:

```markdown
---
srd: wwn                      # wwn | cwn | swn | awn | fate
srd_ref: "WWN §1.3 Skills"    # the SRD section this reproduces
license: wn-free              # wn-free | ccby
order: 2
anchor: wn-skills             # stable id for ToC + Phase-2 deep-links
title: Skills
---

<verbatim SRD prose, headings, tables>
```

**WN core sharing (ADR-142).** A pack binding `wwn` composes `without_number/core/srd/*` +
`wwn/srd/*`, ordered by `order`; `swn` composes core + `swn/srd/*`; etc. One core, thin per-game
overlays — no copy-paste across the four WN games. Composition order and any per-game *override*
of a core chapter (same `anchor` ⇒ overlay wins) is resolved at projection time.

**Fate** is wholly separate — `rulesets/fate/srd/*`, no core/overlay split.

## Extraction (one-time, offline, checked-in)

The SRD sources live on disk, **outside** the repo, under `~/Documents/DriveThruRPG/`:

| Ruleset | Source file | Format | Extraction |
|---|---|---|---|
| Fate Core | `Evil Hat Productions/Fate Core System/Fate_Core_ePub_Edition.epub` | epub (XHTML) | clean structural parse |
| CWN | `…/Cities Without Number System Reference Document/CitiesWithoutNumberSRDv1.0.html` | HTML | clean structural parse |
| WWN | `…/Worlds Without Number System Reference Document/WorldsWithoutNumber_SRD_1.0.pdf` | PDF | text extract + proof |
| SWN | `…/Stars Without Number_ Revised … /StarsWithoutNumberRevised-FreeEdition-122917.pdf` | PDF | text extract + proof |
| AWN | `…/Ashes Without Number_ Free Edition/AshesWithoutNumber_FreeVersion_071025.pdf` | PDF | text extract + proof |

- Extraction is an **offline authoring step**, agent-assisted, run **per ruleset**. Its output —
  the `.md` chapter files — is what gets committed. Extraction is **not** a runtime dependency.
- **Verbatim is a real claim.** epub (Fate) and HTML (CWN) parse cleanly. The three PDFs
  (WWN/SWN/AWN) have columns/tables/headers-footers and need a **manual proofing pass** against
  the source before the `license`/`srd_ref` front-matter is stamped. No file ships claiming
  `verbatim` provenance until it has been proof-read.
- **Player-chapter selection happens here:** the extractor pulls only the player-facing chapters
  (per Scope); GM-only chapters are not extracted.

## Server projection

Extend the existing reference pipeline (`reference_projection.py`, `reference_routes.py`,
`reference_renderer.py`):

- `GET /reference/api/rules/{pack}` resolves the pack's `ruleset` (from `rules.yaml`), composes
  the ruleset's chapter set (core + overlay for WN; flat for Fate), and emits a **new
  `rules_document` section** appended to the pack's existing sections.
- The `rules_document` section carries: an ordered list of chapters (`title`, `anchor`,
  rendered body), plus a **provenance block** (`source`, `license`, `attribution` string).
- **ADR-145 attribution** (rendered, public):
  - WN: *"Reproduced from the {Worlds|Cities|Stars|Ashes} Without Number System Reference Document
    under its free-use terms."*
  - Fate: the **CC-BY** notice (Fate Core System, Evil Hat Productions, licensed CC-BY 3.0) with
    the required attribution line.
  - **MUST NOT** imply endorsement, partnership, approval, or review by Sine Nomine / Kevin
    Crawford / Evil Hat (ADR-145 §D4a).
- **Visibility firewall (ADR-135)** still runs over the section via `classify()`. SRD
  player-chapters are public by definition, so it is a pass-through — but the section is not
  exempt from the firewall.
- A pack with a **native** (non-bound) ruleset emits **no** `rules_document` section (no source to
  reproduce) — silently absent is correct here, not a fail-loud, because it is a true "nothing to
  show," not a misconfiguration. (Contrast: a *bound* ruleset with a *missing* chapter set IS a
  fail-loud load error — see Testing.)

## UI rendering

New **`RulesDocument`** section renderer in `sidequest-ui/src/components/reference/sections/`,
registered in `SectionDispatch`:

- Long-form **prose** treatment (not cards / not node-tree): chapter headings, body, tables,
  each chapter with a stable **anchor id** (`#fate-aspects`, `#wn-skill-check`) matching the
  content front-matter `anchor`.
- Feeds the existing **sticky Table of Contents** (ADR-135 redesign) so SRD chapters appear in
  the ToC alongside the pack sections, with the same "Link to X" anchor affordance that already
  works on the page.
- A **provenance footer/banner** rendering the attribution + license string from the projection.
- Themed via the existing `useThemeTokens()` (parchment for wry_whimsy, terminal for neon_dystopia,
  etc.) — no new theme work.
- **Markdown rendering:** render the chapter Markdown safely (existing markdown path if one
  exists in the reference renderers; otherwise a vetted markdown component). Tables and headings
  must render; raw HTML in content is not permitted (content is authored Markdown, not HTML).

### Coexistence & placement

The new shared SRD section **coexists** with the existing per-pack config sections — they do
different jobs:

- **SRD section** (new, shared, verbatim): *how the ruleset works* — what an aspect is, how the
  ladder reads, how a check resolves.
- **Existing config sections** (`Rules → Fate` / `Rules → Wwn`, Archetypes, Classes, Equipment,
  etc.): *this pack's chosen knobs* — which skills/gear/stunts this pack offers.

Placement: the SRD document is the foundational "what is happening" content, so it renders as its
own clearly-headed top-level section — **"The Rules of Fate Core"** / **"Worlds Without Number —
Player Reference"** — placed prominently (near the top of the document, before or just after
Archetypes). The per-pack masthead stays *"Rules of play… every world of the pack"*; the SRD
section's own heading makes clear it is the underlying **ruleset**, shared across packs.

## Phase 2 preview (out of scope here, designed-for)

Chargen integration is a separate later spec. Phase 1 makes it cheap by giving every chapter a
stable `anchor`. Phase 2 will map chargen steps → anchors (e.g. the `fate_aspects` step →
`#fate-aspects`) and add an in-chargen drawer / "ⓘ" deep-link. No Phase-1 decision forecloses it.

## Testing & wiring

- **Content (fail-loud load gate):** a validation check that for every pack with a **bound**
  ruleset, the composed chapter set is non-empty and **every chapter carries complete provenance
  front-matter** (`srd`, `srd_ref`, `license`, `anchor`, `title`, `order`). Missing source set
  for a bound ruleset, or an unstamped chapter, ⇒ **loud failure** (No Silent Fallbacks). This is
  the guard that no unstamped reproduction ever ships.
- **Server:** projection unit tests — a `ruleset: fate` pack yields a `rules_document` with the
  Fate chapters + CC-BY provenance; a `wwn` pack composes core+wwn in `order`; a `swn` pack
  composes core+swn; a native pack yields **no** section. Plus a **wiring test** that the live
  `GET /reference/api/rules/{pack}` endpoint actually emits the section (not just that the
  composer works in isolation) — per the project's "every test suite needs a wiring test" rule.
- **UI:** `RulesDocument` renders chapters + anchors + provenance footer; the ToC includes the SRD
  chapters; a pack with no `rules_document` section renders the page unchanged (native packs).
- **Anchor stability test:** the set of `anchor` ids a ruleset exposes is asserted (a snapshot/contract
  test) so Phase 2's deep-link targets don't silently drift.

## ADR note

This introduces (a) a **new ruleset-tier content directory** (`sidequest-content/rulesets/`) — the
first content that is neither genre- nor world-tier — and (b) a **new `rules_document` reference
section type**. Both are architectural. **Recommendation:** accompany implementation with either a
new ADR ("Ruleset-Tier SRD Reference Content") or an **amendment to ADR-135** (adding the
`rules_document` section type and noting the ruleset-tier source), cross-referencing ADR-145
(licensing) and ADR-142 (WN core composition).

## Risks & open questions

1. **PDF verbatim fidelity (WWN/SWN/AWN).** The largest risk. Mitigation: proofing pass before
   provenance stamp; prefer the cleaner sources where a choice exists (CWN HTML over CWN PDF).
2. **Volume.** Five rulesets × player chapters is a lot of content and a long page. Mitigation:
   ToC + collapsible chapters (UI) keep it navigable; per-ruleset extraction parallelizes.
3. **SWN/AWN "Free Edition" vs "SRD" nuance.** WWN and CWN ship explicit *System Reference
   Documents*; SWN Revised and AWN ship *Free Editions* of the full book. ADR-145 §D4 already
   rules all four WN games `wn-free` / reproduce-verbatim under Sine Nomine's standing policy, and
   §D4b restricts `srd_ref` to SRD sections. Confirm the SWN/AWN free-edition section references
   are cited as the free edition, consistent with ADR-145, during extraction.
4. **Markdown rendering path.** Confirm whether the reference renderers already have a safe
   Markdown component to reuse; if not, adding one is part of the UI work.

## Decomposition & sequencing

- **This spec = Phase 1** (Rules page). Phase 2 (chargen) is a later, additive spec.
- Within Phase 1 the work splits cleanly:
  1. Content model + composition + fail-loud load gate (server/content scaffolding).
  2. `rules_document` projection + endpoint wiring (server).
  3. `RulesDocument` renderer + ToC/provenance (UI).
  4. **Per-ruleset extraction × 5** — the bulk, parallelizable (Fate, WWN, CWN, SWN, AWN each an
     independent extraction job feeding the shared renderer). WN core is authored once; the four
     WN overlays layer on it.
- A natural first vertical slice for the implementation plan: **Fate end-to-end** (extract →
  compose → project → render → provenance) to validate the whole pipeline on the cleanest source
  and the world currently in playtest, then fan the WN family through the same pipeline.
