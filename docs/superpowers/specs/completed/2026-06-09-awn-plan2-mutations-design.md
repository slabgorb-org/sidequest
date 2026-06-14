# AWN Plan 2 — Mutations: the bespoke MutationPlugin + tables

**Date:** 2026-06-09
**Status:** Draft — Architect spec for Plan 2 of the AWN epic; plan-author ready
**Author:** Architect (Emmanuel Goldstein), continuing the AWN epic
**Parent:** `completed/2026-06-05-ashes-without-number-mutant-wasteland-design.md` (the "AWN spec"),
decisions D1–D6 locked with Keith 2026-06-05. This spec implements **Plan 2** of its §8 epic
decomposition and resolves the **§7 open item**: the Mutations ↔ `magic.yaml` reconciliation.
**Downstream dependent:** `2026-06-09-seaboard-of-saints-awn-rebase-addendum.md` — Seaboard's
`saints.yaml` curates bundles of the mutation IDs this plan defines. **The ID scheme here is a
public contract.**

**Source of truth (faithful port, do not redesign — D6):**
*Ashes Without Number: Free Edition* — Kevin Crawford / Sine Nomine, 2025. Local PDF:
`~/Documents/DriveThruRPG/Sine Nomine Publishing/Ashes Without Number_ Free Edition/AshesWithoutNumber_FreeVersion_071025.pdf`
(PDF page index = printed page + 4). Mutations: MP economy p.16, Stigma p.17, negative
mutations p.18–19, positive mutations p.20–25.

---

## 1. Problem

Plan 1 shipped: `mutant_wasteland` binds `ruleset: awn`
(`sidequest-content/genre_packs/mutant_wasteland/rules.yaml:14`), the thin
`AwnRulesetModule(CwnRulesetModule)` resolves combat with real ablative HP / Shock / Trauma /
System Strain, and the CWN-family tool guards are capability-gated
(`adjust_system_strain.py` now keys on `isinstance(module, CwnRulesetModule)`).

But the pack's *identity* mechanic — mutation — is still pure prose. The evidence:

- The **"Use Mutation"** combat beat (`rules.yaml:181`) is a `strike` beat with `stat_check: WIS`
  and a `risk:` string. The narrator narrates "mutation instability" with zero mechanical backing —
  no MP pool, no per-mutation state, no Strain cost, no usage limit. This is exactly the
  "winging it" failure mode the OTEL doctrine exists to catch.
- The genre-tier `magic.yaml` (DRAFT, 2026-04-27) declares "mutations ARE this pack's magic
  system" — but the magic pipeline **was never live for this pack** (see §3).
- Sebastien and Jade's missing crunch (the project's named motivation for the whole AWN epic)
  is most visible here: a Mutant-class character has no numbers behind their defining trait.

Plan 2 builds AWN's mutation system as a bespoke subsystem (per locked decision **D5**) and
retires the dormant magic framing. It also defines the stable mutation-ID catalog that
**Seaboard of Saints** is blocked on.

## 2. Decisions

D5 is inherited from the parent spec (locked): **Mutations = bespoke `MutationPlugin`, not the
MagicPlugin/ADR-126 seam.** This spec adds the Plan-2-local decisions:

| # | Decision | Rationale (details in cited section) |
|---|----------|-----------|
| P2-1 | **Replace, don't reconcile:** retire `mutant_wasteland/magic.yaml` (genre tier) and `flickering_reach/magic.yaml.draft`. The mutation subsystem is the *sole* authority on mutation mechanics; narrative-register prose migrates into `mutations.yaml` | §3 — the magic pipeline was never live for this pack; keeping two descriptors of one mechanic recreates the "double-truth" risk the parent spec flagged (§10) |
| P2-2 | **New `sidequest/mutation/` package**, sibling of `sidequest/magic/` — same paired-file shape (`.py` mechanics / YAML content schema), its own state model on `GameSnapshot` | §5 — mirrors the house pattern; mutation state (MP, stigma, usage counters) has no overlap with `MagicState`'s ledger-bar shape |
| P2-3 | **Mutation IDs are `<category>/<snake_case_name>`** (e.g. `structure/crushing_jaws`, `negative/withered_arm`), stable forever | §6.2 — Seaboard `saints.yaml` references these IDs cross-repo; slug stability is the same contract as reference-page anchors |
| P2-4 | **Engine ships schema + resolution; GM authors the catalog.** The 6×10 positive table, the d100 negative table, and the Stigma tables are *content* in `mutations.yaml`, validated by the pack validator — never hardcoded in Python, never asserted in unit tests | content-repo doctrine: content invariants live in the pack validator; engine tests use synthetic fixtures |
| P2-5 | **Strain costs route through the existing `apply_system_strain`** (`cwn.py:131`) with a new `kind="mutation"` — no parallel strain plumbing | Don't Reinvent: the pool, the over-max refusal, and the `cwn.system_strain.delta` span already exist and already serve awn |
| P2-6 | **Random rolls (d100 negative, random-positive spend, Stigma d6×d6×d12) are resume-safe**, following the ADR-128 seeded-randomness pattern | a mid-chargen or mid-scene resume must not reroll a mutation someone already has |
| P2-7 | **The "Use Mutation" beat stays; its resolution gains mechanical backing.** Beat texture is untouched; selecting it now resolves through the mutation subsystem (Strain cost, usage limit, save-vs where the power says so) and emits `awn.mutation.*` spans | beat continuity for saves/UX; OTEL proves the difference between narrated and resolved |

## 3. The Architect call — `magic.yaml` reconciliation (parent §7, resolved)

The parent spec asked: does the bespoke MutationPlugin *replace* the `magic.yaml` framing, or
does `magic.yaml` become a thin descriptor pointing at the plugin? **Answer: replace (P2-1).**
Grounded in four code facts:

1. **The magic pipeline is not live for this pack and never was.** The loader requires *both*
   genre-tier and world-tier `magic.yaml` (`sidequest/genre/loader.py:1314–1321`, "the
   magic_loader requires BOTH"; absent = deliberate silent-skip matching `magic_init.py`).
   `mutant_wasteland`'s only world ships `flickering_reach/magic.yaml.draft` — a draft suffix the
   loader does not read. The genre-tier `magic.yaml` is dormant narrative config; nothing in
   `sidequest-server` consumes mutant_wasteland magic (grep confirms zero references).
2. **The MagicPlugin seam is the wrong shape, as D5 already judged.** `MagicPlugin` is a
   *validator* protocol (`required_attrs()` + `validate_working()` — `magic/plugin.py:22`) over
   narrative `MagicWorking`s and ledger bars; its resolution surfaces are spell-catalog-shaped
   (`innate_v1_cast.resolve_innate_v1_cast` resolves a `Spell` against save branches). AWN
   mutations need: an MP pool spent at chargen, per-mutation usage counters, System-Strain
   per-use costs, d100 random acquisition, and powers that modify AC / Move / attr-mods /
   Trauma Target. None of that fits `MagicState`'s `BarKey`/`WorkingRecord` shape without
   contortion.
3. **Two live descriptors of one mechanic is the double-truth the parent spec warned about**
   (§10: "the pack carries both the old 'mutation = magic' framing and the new awn binding").
   If `magic.yaml` stayed live-but-thin, the intent router would face two candidate authorities
   for "I use my mutation" — the magic pipeline (innate source) and the mutation subsystem.
   Single mechanical authority or fail loud; that's doctrine.
4. **Nothing of value is lost.** What `magic.yaml` actually carries is narrative register
   (visibility `feared`, the excellent `narrator_register` prose, hard limits like
   `choice_of_mutation: forbidden`) and player-options flags. All of it migrates verbatim into
   `mutations.yaml`'s narrator-facing sections (§6.1), where it sits next to the mechanics it
   describes instead of in a file implying a pipeline that isn't there.

**Consequences:**
- Delete `genre_packs/mutant_wasteland/magic.yaml` and
  `worlds/flickering_reach/magic.yaml.draft` in the Plan 2 content story. (Note: the 2026-06-09
  gap-audit GM pass already recorded the `.draft` as deleted, but the file is still present on
  `sidequest-content` develop — the deletion evidently never landed. Plan 2 finishes the job.)
- `docs/design/magic-taxonomy.md`'s claim that mutant_wasteland expresses mutation-as-magic gets
  a one-line correction pointing at this spec.
- The magic system remains untouched for the packs that actually use it. This is a
  mutant_wasteland-scoped retirement, not a magic-system change. **No ADR needed:** the
  mutation subsystem is a genre-layer instance under the existing AWN epic (parent §11.3
  reasoning applies); ADR-126's registry is simply not gaining a plugin it was never going to fit.

## 4. Source mechanics (extracted; implementer need not re-read the PDF)

### 4.1 MP economy (printed p.16)
- A mutant character has an **MP (Mutation Point) pool**, assembled at chargen:
  - **Mutant Edge** grants +2 MP (in pack terms: the Mutant class's mechanical surface; see §5.5).
  - **Mutation Acceleration** (a focus-equivalent pick): +2 MP.
  - Each **negative mutation** taken: +2 MP, **max 3 negatives**.
  - A **concealable Stigma** costs −1 MP (visible Stigma is free).
- **Spending MP:** random positive mutation (roll category, roll within) **−1 MP**; pick any
  positive **−3 MP**; second mutation from the same category **−3 MP**.
- Negatives are **rolled before** positives (you learn your burdens before buying your gifts).
- Unspent MP persists; in-play acquisition (radiation nat-20s, Plan 3) spends from the same pool
  semantics.

### 4.2 Stigma (p.17)
Cosmetic mutation marks: roll **d6 body-part × d6 nature × d12 flavor**. Concealable variant costs
the MP above. Pure narrator texture — no mechanical effect beyond the social register.

### 4.3 Negative mutations (p.18–19)
A **d100 table (~40 entries)**. Attribute penalties **floor at −2** per attribute. Entries are
content rows: id, name, d100 range, effect text, and a small machine-readable effect block
(attr penalties, Move changes, save penalties) where the effect is mechanical.

### 4.4 Positive mutations (p.20–25)
**6 categories × 10 = 60 powers:** Structure / Sense / Hybrid / Cognition / Pseudo-Psychic /
Exotic. Each is bespoke; the recurring mechanical fields are:
- **System Strain cost** on use (0 for passives),
- **usage limit** (at-will / per-scene / per-day),
- **save-vs** clause (target save type + on-success effect, same shape innate_v1 codified),
- **combat-power hooks**: Crushing Jaws / Savage Claws / Venom Glands resolve as Punch attacks
  with Shock and Trauma — these ride the **already-built** CWN attack/Shock/Trauma methods, the
  mutation only contributes the weapon-equivalent `DamageSpec`,
- **passive modifiers**: AC, Move, attr-mods, Trauma Target, HP-on-revive.

## 5. Engine design — `sidequest-server`

### 5.1 Package layout (P2-2)

```
sidequest/mutation/
├── __init__.py
├── models.py        # pydantic: MutationDef, MutationCatalog, StigmaTables, MpLedger rules
├── state.py         # MutationState — pydantic field on GameSnapshot (like MagicState)
├── catalog.py       # YAML → MutationCatalog loader; fail-loud on bad IDs/ranges
├── chargen.py       # MP-pool assembly + negative-first ordering + spend ops
├── use_ops.py       # in-play use: Strain cost via apply_system_strain, usage counters, save-vs
└── acquire_ops.py   # random acquisition (d100 negative, random positive) — resume-safe rolls
```

`MutationState` (per character): `mp_remaining: int`, `stigma: list[StigmaRecord]`,
`negative_ids: list[str]`, `positive_ids: list[str]`,
`usage: dict[str, UsageCounter]` (per-scene/per-day tallies + reset hooks). Serializes on the
snapshot exactly as `MagicState` does (`magic/state.py` precedent).

### 5.2 Resolution seams (reuse-first)

| Mutation need | Existing seam (verify, don't rebuild) |
|---|---|
| Strain on use | `CwnRulesetModule.apply_system_strain` (`cwn.py:131`) + new `kind="mutation"`; over-max refusal semantics already defined |
| Natural-weapon powers | CWN attack resolution + `resolve_shock` / `resolve_trauma`; mutation supplies the `DamageSpec` |
| Save-vs powers | the save-branch shape codified in `innate_v1_cast.py` (stat None → auto-apply; stat set → resolver callable) — reuse the *shape*, not the spell catalog |
| Tool guard | capability gate `isinstance(module, AwnRulesetModule)` — mutation is AWN-only; follows the corrected `adjust_system_strain` pattern, never a slug string |
| Random rolls | ADR-128 resume-safe randomness pattern (seeded, persisted) |

### 5.3 Agent tool

One new tool, `use_mutation` (`sidequest/agents/tools/use_mutation.py`), `ToolCategory.WRITE`,
following `adjust_system_strain`'s structure: resolve actor's `MutationState`, check the mutation
is owned + usage limit not exhausted, apply Strain via the §5.2 seam, resolve save-vs if present,
return the structured result so the narrator describes what *actually happened*. Refusals
(unowned mutation, exhausted use, Strain over max) return reasons for narration — fail loud,
no silent improvisation.

### 5.4 Narrator context

A mutation context block (static: owned mutations + effects summary; volatile: MP, usage
remaining, current Strain) injected per the `build_magic_context_block` precedent
(`magic/context_builder.py`) — bespoke builder in `sidequest/mutation/`, same static/volatile
split so the prompt-zone discipline (ADR-009/112) holds.

### 5.5 Chargen integration

`builder.py` already seeds the System Strain pool from `CwnConfig` (Plan 1 item 4). Plan 2 adds:
for characters whose class grants the mutation surface (the pack's **Mutant** class — ADR-097
class-mechanical-surface is the seam), run `chargen.py`'s MP assembly: negatives first (rolled,
resume-safe), then guided MP spend. `char_creation.yaml` gains the player-facing copy. Non-mutant
classes get no `MutationState` — absence is a valid state, not a default-empty fallback.

### 5.6 OTEL spans (mandatory — the GM panel is the lie detector)

New span file `sidequest/telemetry/spans/awn.py` (the parent spec §7 names this pattern):
- `awn.mutation.acquired` — id, source (chargen/radiation/event), roll, mp_delta
- `awn.mutation.used` — id, strain_cost, usage_remaining, save_stat/save_result if any
- `awn.mutation.refused` — id, reason (limit_exhausted / strain_over_max / not_owned)
- `awn.mutation.mp_spend` — spend kind (random −1 / pick −3 / same-category −3), mp_remaining

Spans `__init__` re-export + routing-completeness test entry, per the PR #520 wiring checklist.

## 6. Content design — `sidequest-content`

### 6.1 `genre_packs/mutant_wasteland/mutations.yaml` (new, genre tier)

Sections: `mp_economy` (the §4.1 numbers — data, not code), `stigma_tables` (d6/d6/d12),
`negatives` (d100 table rows), `positives` (6 categories × 10), and `narrator` — the register
prose, visibility/hard-limits, and player-options content **migrated from `magic.yaml`**
(its `narrator_register` block survives verbatim; it's good).

Per-mutation row shape (machine-readable where mechanical, prose where narrative):

```yaml
positives:
  structure:
    - id: structure/crushing_jaws        # P2-3 contract — never rename
      name: Crushing Jaws
      strain_cost: 0                     # passive natural weapon
      usage: at_will
      attack: { skill: Punch, damage: 1d8, shock: "2/AC15", trauma_die: 1d6, trauma_rating: x2 }
      effect: >-
        Jaw structure rebuilt for crushing force; bite as a Punch attack.
```

### 6.2 The ID contract (P2-3)

`<category>/<snake_case_name>`, stable forever. Three consumers depend on it:
1. **Seaboard `saints.yaml`** — each Saint = curated positive IDs + one negative ID as drawback.
2. **Save files** — `MutationState` persists IDs; renames break loaded games loudly (same
   doctrine as reference-page anchor stability: slug stability is name stability).
3. **OTEL spans** — the GM panel groups by mutation id.

The pack validator (not unit tests — P2-4) enforces: d100 ranges partition 1–100 with no gaps or
overlaps; exactly 10 positives per category; every `attack:` block names an existing skill;
IDs unique and slug-shaped; every save-vs names a real save type.

### 6.3 Retirements

- `magic.yaml` (genre tier) — deleted; content migrated per §6.1.
- `worlds/flickering_reach/magic.yaml.draft` — deleted (finishing the gap-audit GM-pass intent).
- `rules.yaml` "Use Mutation" beat — text untouched; gains a `mutation_resolution: true` marker
  (or equivalent wiring the Dev story defines) so dispatch routes it through `use_ops` instead of
  bare narration.

## 7. Wiring tests (every suite needs one)

1. **Production-path mutation use:** seed a mutant_wasteland combat encounter with a
   Mutant-class character owning a Strain-costed mutation; drive a "Use Mutation" turn through
   the production dispatch path; assert `awn.mutation.used` + `cwn.system_strain.delta` fire and
   the Strain pool moved. Assert spans, not source text.
2. **Chargen smoke:** create a Mutant-class character; assert non-None `MutationState`,
   negatives-before-positives ordering in the acquisition log, MP arithmetic correct; assert a
   non-mutant class character has no `MutationState`.
3. **Resume-safety:** persist mid-chargen after the negative roll; reload; assert the same
   negative (no reroll).
4. **Catalog fail-loud:** synthetic fixture catalogs (engine tests never assert real pack
   content — P2-4) with a d100 gap / duplicate ID; assert loader raises.

## 8. Story split

| Story | Lane | Owner | Depends on |
|---|---|---|---|
| A — `sidequest/mutation/` package: models, state, catalog loader, chargen + use + acquire ops, spans, synthetic-fixture tests | engine | Dev | — |
| B — `use_mutation` tool + dispatch wiring for the beat + narrator context block + production-path wiring test | engine | Dev | A |
| C — `mutations.yaml` catalog (60 positives, d100 negatives, Stigma tables, register migration) + retirements (§6.3) + pack-validator rules | content | GM | A (schema), unblocks Seaboard |

## 9. Non-goals (Plan 2)

- No Radiation/Disease (Plan 3) — `acquire_ops` exposes the entry point
  (`acquire_random_positive` / `acquire_random_negative`) that Plan 3's rad-mutation nat-20/nat-1
  rule will call; the rule itself is Plan 3.
- No Stress/Addiction (Plan 4), no hexcrawl (Plan 5), no bestiary (Plan 6), no enclaves (Plan 7).
- No Seaboard content — Seaboard's `saints.yaml` is the *next* plan, consuming this one's IDs.
- No magic-system changes outside mutant_wasteland's file retirements.
- No new chargen UI; the guided MP spend rides the existing character-builder state machine
  (ADR-015/016) as data-driven steps.

## 10. Risks

- **ID churn after Seaboard lands** — mitigated by P2-3 (contract status) and the pack
  validator's uniqueness check; treat any rename as a breaking change requiring a migration note.
- **Catalog authoring volume** (60 + ~40 + stigma tables is real work) — it's the GM lane's
  marquee deliverable; the schema (Story A) lands first so authoring isn't blocked on engine
  completion.
- **Beat-dispatch regression** — wiring "Use Mutation" into mechanical resolution must not break
  the other strike/brace/angle/push beats; the §7.1 wiring test plus the existing combat-dispatch
  tests gate this.
- **Double-truth window** — between Story A landing and Story C deleting `magic.yaml`, the dormant
  file still exists; acceptable because it was already dormant (§3.1), but Story C must not slip
  the retirement.

## 11. What this unblocks

The Seaboard of Saints world plan (per its 2026-06-09 addendum): Saints become curated bundles
over the §6 catalog (`saints.yaml` → positive IDs + drawback ID, priced in MP), Saint-Marked vs
Wild Mutant become two presets over the same MP economy, and flickering_reach inherits the raw
AWN spend with zero Saint content. Plan 2's ID catalog is the dependency that addendum names.
