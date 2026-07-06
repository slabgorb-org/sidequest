# Per-World Picker Portrait Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand every world's `player_picker` portrait set to cover its specific gap (culture / archetype / demographic), then deliver per-world render scripts Keith runs at his leisure.

**Architecture:** Content-only authoring into the already-shipped picker mechanism (Epic 66). New `type: player_picker` entries are appended to each world's `portrait_manifest.yaml` following a per-world coverage audit and a floors+variety-fill allocation rule. A parameterized render runbook (`scripts/render_pickers/`) wraps the existing `generate_portrait_images.py → r2_sync_packs.py → r2_manifest_from_bucket.py` pipeline, one invocation per world. **No engine, UI, or daemon code changes.**

**Tech Stack:** YAML content (`sidequest-content`), `yq`/`grep` for audits, `just content-validate` (pydantic `PortraitManifestEntry` validation), POSIX shell for the render runbook, existing Python render tooling run via `uv`.

**Spec:** `docs/superpowers/specs/2026-07-06-picker-portrait-expansion-design.md`

## Global Constraints

Every task implicitly includes these.

- **Repos & base branches** (per `repos.yaml`): picker YAML lives in `sidequest-content` → base `develop`; render scripts + docs live in the orchestrator (`.`) → base `main`. Never checkout `main` in `sidequest-content`.
- **Picker entry schema** (fields on `PortraitManifestEntry`; slug = `entry.id or slugify(entry.name)`):
  ```yaml
  - id: picker_<culture>_<archetype>_<sex><nn>   # explicit canonical slug, lowercase, underscores
    name: picker <culture> <archetype> <sex><nn> # human-spaced mirror of id
    role: <world-appropriate role label>
    type: player_picker
    culture: <culture filename stem — MUST match a real cultures/<stem>.yaml>
    archetype: <real archetype name — world or pack archetype>
    sex: <male | female | nonbinary>
    backdrop_poi: <real POI slug from this world's history.yaml>
    appearance: >-
      <~50 tokens, ONE person, face + upper body only>
  ```
- **`appearance` discipline:** terse (~50 tokens), ONE person, face and upper body only. No POI/scene prose in `appearance` (a second wide description triggers the Z-Image split-montage failure). The backdrop comes from `backdrop_poi`, never from the appearance text. Mutations/nonhuman traits matter-of-fact, warranted by the culture, never horror.
- **Allocation rule (floors + variety fill):** the new set for a world is the union of — **culture floor:** every culture ≥ 3–4 picker faces with a sex mix; **archetype floor:** every distinct chargen archetype appears on ≥ 1 picker face somewhere in the world; **variety fill:** within each culture's faces, deliberately vary apparent age, build, and gender presentation. Not a culture×archetype cross-product. No ceiling — count falls out of the floors.
- **No new archetypes.** `archetype:` must name an archetype that already exists. If a world genuinely lacks a wanted archetype, STOP and flag Keith — authoring archetypes is mechanics/crunch, out of scope.
- **Specificity over cliché.** Reference-stacked, genre-true faces matching each culture's documented aesthetic. Never "generic fantasy man #4."
- **Sex spread & NB:** default to a balanced male/female mix per culture; use `nonbinary` where the culture warrants it (aliens, constructs, the deliberately ambiguous — following the shipped `picker_tsveri_liaison_nb01` precedent).
- **`uv run python`, never bare `python3`** for any render/R2 script (they import `boto3` from the orchestrator `uv` env; bare `python3` fails on non-`--force` runs).
- **Spoiler protection:** only `mutant_wasteland/flickering_reach` is spoilable. Authoring needs only public chargen data (cultures, archetypes, POI slugs) — never read or surface plot secrets for any other world.
- **Validator contract** (`just content-validate <genre>`): picker entry missing `id`/`culture`/`archetype`/`sex` → **warning**; `backdrop_poi` not among the world's `history.yaml` POI slugs → **hard error**.

---

## Shared: Per-World Authoring Procedure

Tasks 2–12 each apply this procedure to their pack's worlds. It is referenced by name; do not paraphrase it per task.

**Step A — Audit the world.** With `GENRE`/`WORLD` set and `C=sidequest-content/genre_packs/$GENRE/worlds/$WORLD`:

```bash
# Cultures available (the culture floor axis):
ls "$C"/cultures/*.yaml 2>/dev/null | xargs -n1 basename | sed 's/\.yaml$//'
# Archetypes the world/pack expose (the archetype floor axis):
yq '.archetypes[].name' "$C"/archetypes.yaml 2>/dev/null
yq '.archetypes[].name' "sidequest-content/genre_packs/$GENRE/archetypes.yaml" 2>/dev/null
# Current picker distribution (what already exists):
yq '.characters[] | select(.type=="player_picker") | .culture'   "$C"/portrait_manifest.yaml | sort | uniq -c
yq '.characters[] | select(.type=="player_picker") | .archetype' "$C"/portrait_manifest.yaml | sort | uniq -c
# Known-valid POI slugs to draw backdrops from (existing valid values, safe reuse set):
yq '.characters[] | .backdrop_poi' "$C"/portrait_manifest.yaml | grep -v '^null$' | sort -u
# Broader POI slug set (authoritative source the validator checks against):
yq '.chapters[].pois[].slug // .history_structure.chapters[].pois[].slug' "$C"/history.yaml 2>/dev/null | sort -u
```

Record: which cultures have < 3 picker faces, which archetypes have 0, and the world's gap type.

**Step B — Read culture look before authoring its faces.** For each culture you will add faces for, read `"$C"/cultures/<stem>.yaml` so appearances match the documented aesthetic (skin, dress, features, naming). Genre truth + specificity.

**Step C — Author the new entries.** Append a commented block to `"$C"/portrait_manifest.yaml` under the existing `characters:` list:

```yaml
  # ═══════════════════════════════════════════════════════════════
  # PLAYER PICKER PORTRAITS — 2026-07 expansion
  # Added to satisfy the culture/archetype/variety floors. One person,
  # face + upper body, ~50 tokens. backdrop_poi = real history.yaml slug.
  # ═══════════════════════════════════════════════════════════════
  - id: picker_<culture>_<archetype>_<sex><nn>
    name: picker <culture> <archetype> <sex><nn>
    role: <role>
    type: player_picker
    culture: <stem>
    archetype: <archetype>
    sex: <male|female|nonbinary>
    backdrop_poi: <slug>
    appearance: >-
      <~50 tokens, one person, face + upper body>
```

Honor the allocation rule: bring every culture to ≥ 3–4 faces, ensure every archetype appears ≥ once, vary age/build/presentation. Keep `<nn>` unique per `picker_<culture>_<archetype>_<sex>` prefix.

**Step D — Validate.** `cd` to orchestrator root, then:

```bash
just content-validate "$GENRE"
```

Expected: **zero** `player_picker backdrop_poi ... does not match any known POI slug` errors, and **zero** `player_picker is missing required fields` warnings for this world's manifest. Fix any before committing (a dangling `backdrop_poi` means the slug isn't in `history.yaml` — pick a real one).

**Step E — Coverage assertion.** Confirm the floors are met:

```bash
yq '.characters[] | select(.type=="player_picker") | .culture' "$C"/portrait_manifest.yaml | sort | uniq -c
```

Every culture from Step A appears with a count ≥ 3. Every archetype appears ≥ 1 (re-run the archetype `uniq -c`).

**Step F — Commit** (in `sidequest-content`):

```bash
cd sidequest-content
git add "genre_packs/$GENRE/worlds/$WORLD/portrait_manifest.yaml"
git commit -m "content($GENRE): expand $WORLD player_picker portraits (2026-07)"
```

---

## Task 1: Feature branches

**Files:** none (git only).

- [ ] **Step 1: Content repo branch off develop**

```bash
cd /Users/slabgorb/Projects/oq-2/sidequest-content
git checkout develop && git pull
git checkout -b feat/picker-portrait-expansion
```
Expected: on `feat/picker-portrait-expansion` tracking `develop`.

- [ ] **Step 2: Orchestrator branch off main**

```bash
cd /Users/slabgorb/Projects/oq-2
git checkout main && git pull
git checkout -b feat/picker-render-scripts
```
Expected: on `feat/picker-render-scripts` tracking `main`.

---

## Task 2: wry_whimsy — oz, wonderland, gulliver

**Files:**
- Modify: `sidequest-content/genre_packs/wry_whimsy/worlds/oz/portrait_manifest.yaml`
- Modify: `sidequest-content/genre_packs/wry_whimsy/worlds/wonderland/portrait_manifest.yaml`
- Modify: `sidequest-content/genre_packs/wry_whimsy/worlds/gulliver/portrait_manifest.yaml`

**Gap notes:** `oz` is the flagship **culture gap** — all 18 pickers are `kansas_1900`; the five Ozian cultures (`emerald`, `gillikin`, `munchkin`, `quadling`, `winkie`) have zero faces. Bring each Ozian culture to ≥ 3–4 faces; keep Kansas. `wonderland` (20) and `gulliver` (18): audit for culture/archetype gaps and top up per the rule.

- [ ] **Step 1: oz** — apply the Per-World Authoring Procedure (Steps A–F) with `GENRE=wry_whimsy WORLD=oz`. Projection 18 → ~26–28.
- [ ] **Step 2: wonderland** — apply the Procedure with `GENRE=wry_whimsy WORLD=wonderland`.
- [ ] **Step 3: gulliver** — apply the Procedure with `GENRE=wry_whimsy WORLD=gulliver`.
- [ ] **Step 4: Pack validation** — `just content-validate wry_whimsy`; expected zero picker errors/warnings across all three worlds.

---

## Task 3: space_opera — coyote_star, perseus_cloud, aureate_span

**Files:**
- Modify: `sidequest-content/genre_packs/space_opera/worlds/coyote_star/portrait_manifest.yaml`
- Modify: `sidequest-content/genre_packs/space_opera/worlds/perseus_cloud/portrait_manifest.yaml`
- Modify: `sidequest-content/genre_packs/space_opera/worlds/aureate_span/portrait_manifest.yaml`

**Gap notes:** `coyote_star` is a **thin world** (10 pickers) — bring to full culture coverage (hegemonic, free_miners, voidborn, broken_drift, tsveri). Use `nonbinary` for tsveri where warranted (shipped precedent). `perseus_cloud`/`aureate_span` (18 each): top up per the rule.

- [ ] **Step 1: coyote_star** — Procedure, `GENRE=space_opera WORLD=coyote_star`. Projection 10 → ~20.
- [ ] **Step 2: perseus_cloud** — Procedure, `GENRE=space_opera WORLD=perseus_cloud`.
- [ ] **Step 3: aureate_span** — Procedure, `GENRE=space_opera WORLD=aureate_span`.
- [ ] **Step 4: Pack validation** — `just content-validate space_opera`; expected zero picker errors/warnings.

---

## Task 4: spaghetti_western — dust_and_lead, five_points, the_real_mccoy

**Files:**
- Modify: `sidequest-content/genre_packs/spaghetti_western/worlds/dust_and_lead/portrait_manifest.yaml`
- Modify: `sidequest-content/genre_packs/spaghetti_western/worlds/five_points/portrait_manifest.yaml`
- Modify: `sidequest-content/genre_packs/spaghetti_western/worlds/the_real_mccoy/portrait_manifest.yaml`

**Gap notes:** `five_points` is a **thin world** (15) — top up to full coverage. `dust_and_lead`/`the_real_mccoy` (18 each): audit and fill per the rule.

- [ ] **Step 1: five_points** — Procedure, `GENRE=spaghetti_western WORLD=five_points`.
- [ ] **Step 2: dust_and_lead** — Procedure, `GENRE=spaghetti_western WORLD=dust_and_lead`.
- [ ] **Step 3: the_real_mccoy** — Procedure, `GENRE=spaghetti_western WORLD=the_real_mccoy`.
- [ ] **Step 4: Pack validation** — `just content-validate spaghetti_western`; expected zero picker errors/warnings.

---

## Task 5: heavy_metal — barsoom, long_foundry, evropi

**Files:**
- Modify: `sidequest-content/genre_packs/heavy_metal/worlds/barsoom/portrait_manifest.yaml`
- Modify: `sidequest-content/genre_packs/heavy_metal/worlds/long_foundry/portrait_manifest.yaml`
- Modify: `sidequest-content/genre_packs/heavy_metal/worlds/evropi/portrait_manifest.yaml`

**Gap notes:** `evropi` (33) is already the high-water mark — audit for any culture/archetype with zero coverage and fill **only** genuine gaps; do not pad. `barsoom` (18)/`long_foundry` (17): fill per the rule.

- [ ] **Step 1: long_foundry** — Procedure, `GENRE=heavy_metal WORLD=long_foundry`.
- [ ] **Step 2: barsoom** — Procedure, `GENRE=heavy_metal WORLD=barsoom`.
- [ ] **Step 3: evropi** — Procedure Steps A–B only, then author faces **only** for cultures < 3 or archetypes at 0; if none, record "already covered" and skip authoring. Validate + commit only if changed.
- [ ] **Step 4: Pack validation** — `just content-validate heavy_metal`; expected zero picker errors/warnings.

---

## Task 6: elemental_harmony — burning_peace, shattered_accord

**Files:**
- Modify: `sidequest-content/genre_packs/elemental_harmony/worlds/burning_peace/portrait_manifest.yaml`
- Modify: `sidequest-content/genre_packs/elemental_harmony/worlds/shattered_accord/portrait_manifest.yaml`

**Gap notes:** `shattered_accord` (16): top up. `burning_peace` (18): fill per the rule.

- [ ] **Step 1: shattered_accord** — Procedure, `GENRE=elemental_harmony WORLD=shattered_accord`.
- [ ] **Step 2: burning_peace** — Procedure, `GENRE=elemental_harmony WORLD=burning_peace`.
- [ ] **Step 3: Pack validation** — `just content-validate elemental_harmony`; expected zero picker errors/warnings.

---

## Task 7: tea_and_murder — glenross, blackthorn_moor

**Files:**
- Modify: `sidequest-content/genre_packs/tea_and_murder/worlds/glenross/portrait_manifest.yaml`
- Modify: `sidequest-content/genre_packs/tea_and_murder/worlds/blackthorn_moor/portrait_manifest.yaml`

**Gap notes:** both at 18 — audit for culture/archetype gaps and fill per the rule (cosy Edwardian; specificity over cliché — no generic "village vicar").

- [ ] **Step 1: glenross** — Procedure, `GENRE=tea_and_murder WORLD=glenross`.
- [ ] **Step 2: blackthorn_moor** — Procedure, `GENRE=tea_and_murder WORLD=blackthorn_moor`.
- [ ] **Step 3: Pack validation** — `just content-validate tea_and_murder`; expected zero picker errors/warnings.

---

## Task 8: mutant_wasteland — seaboard_of_saints, flickering_reach

**Files:**
- Modify: `sidequest-content/genre_packs/mutant_wasteland/worlds/seaboard_of_saints/portrait_manifest.yaml`
- Modify: `sidequest-content/genre_packs/mutant_wasteland/worlds/flickering_reach/portrait_manifest.yaml`

**Gap notes:** `flickering_reach` (18) is the spoilable world — its picker block is the reference form; fill any culture < 3 / archetype at 0. `seaboard_of_saints` (20): fill per the rule.

- [ ] **Step 1: seaboard_of_saints** — Procedure, `GENRE=mutant_wasteland WORLD=seaboard_of_saints`.
- [ ] **Step 2: flickering_reach** — Procedure, `GENRE=mutant_wasteland WORLD=flickering_reach`.
- [ ] **Step 3: Pack validation** — `just content-validate mutant_wasteland`; expected zero picker errors/warnings.

---

## Task 9: caverns_and_claudes — beneath_sunden

**Files:**
- Modify: `sidequest-content/genre_packs/caverns_and_claudes/worlds/beneath_sunden/portrait_manifest.yaml`

**Gap notes:** **volume/demographic** gap — Keith called it "more generic." Add demographic variety (age/build/presentation) across existing cultures/archetypes and cover any archetype at 0.

- [ ] **Step 1: beneath_sunden** — Procedure, `GENRE=caverns_and_claudes WORLD=beneath_sunden`. Projection 19 → ~28.
- [ ] **Step 2: Pack validation** — `just content-validate caverns_and_claudes`; expected zero picker errors/warnings.

---

## Task 10: neon_dystopia — franchise_nations

**Files:**
- Modify: `sidequest-content/genre_packs/neon_dystopia/worlds/franchise_nations/portrait_manifest.yaml`

**Gap notes:** cyberpunk — cliché risk is high (Keith's high-expertise domain-adjacent). Reference-stack specifics; no generic "hacker in a hoodie."

- [ ] **Step 1: franchise_nations** — Procedure, `GENRE=neon_dystopia WORLD=franchise_nations`.
- [ ] **Step 2: Pack validation** — `just content-validate neon_dystopia`; expected zero picker errors/warnings.

---

## Task 11: pulp_noir — annees_folles

**Files:**
- Modify: `sidequest-content/genre_packs/pulp_noir/worlds/annees_folles/portrait_manifest.yaml`

**Gap notes:** 1930s pre-war pulp — fill per the rule; period-specific, genre-true faces.

- [ ] **Step 1: annees_folles** — Procedure, `GENRE=pulp_noir WORLD=annees_folles`.
- [ ] **Step 2: Pack validation** — `just content-validate pulp_noir`; expected zero picker errors/warnings.

---

## Task 12: road_warrior — the_circuit

**Files:**
- Modify: `sidequest-content/genre_packs/road_warrior/worlds/the_circuit/portrait_manifest.yaml`

**Gap notes:** **archetype gap** — Keith flagged `the_circuit` as archetype-rich. Prioritize the archetype floor: ensure every distinct chargen archetype has ≥ 1 picker face; then culture floor + variety.

- [ ] **Step 1: the_circuit** — Procedure, `GENRE=road_warrior WORLD=the_circuit`.
- [ ] **Step 2: Pack validation** — `just content-validate road_warrior`; expected zero picker errors/warnings.

---

## Task 13: Full validation sweep

**Files:** none (validation only).

- [ ] **Step 1: Validate all packs**

```bash
cd /Users/slabgorb/Projects/oq-2
just content-validate-all 2>&1 | tee /tmp/picker-validate-all.log
```
Expected: no `player_picker backdrop_poi ... does not match any known POI slug` errors and no `player_picker is missing required fields` warnings anywhere.

- [ ] **Step 2: Slug-uniqueness check across all expanded worlds**

```bash
cd /Users/slabgorb/Projects/oq-2/sidequest-content
for f in $(find genre_packs -name portrait_manifest.yaml); do
  yq '.characters[] | select(.type=="player_picker") | .id' "$f" 2>/dev/null
done | sort | uniq -d
```
Expected: empty output (no duplicate picker ids). Fix any collisions and re-commit the offending world.

---

## Task 14: Per-world render runbook

**Files:**
- Create: `scripts/render_pickers/render_one.sh`
- Create: `scripts/render_pickers/all.sh`
- Create: `scripts/render_pickers/<genre>__<world>.sh` (one thin wrapper per expanded world)
- Create: `scripts/render_pickers/README.md`

**Interfaces:**
- Consumes: existing `scripts/generate_portrait_images.py` (`--genre`, `--world`; skips images already on R2 on a non-`--force` run), `scripts/r2_sync_packs.py` (`--files`), `scripts/r2_manifest_from_bucket.py`.
- Produces: a runnable per-world render → sync → manifest-rebuild pipeline.

- [ ] **Step 1: Write the parameterized engine `render_one.sh`**

```bash
#!/usr/bin/env bash
# Render only the NEW picker portraits for one world, sync them to R2, rebuild manifest.
# Usage: scripts/render_pickers/render_one.sh <genre> <world>
set -euo pipefail
GENRE="${1:?usage: render_one.sh <genre> <world>}"
WORLD="${2:?usage: render_one.sh <genre> <world>}"
ROOT="/Users/slabgorb/Projects/oq-2"
PORTRAITS_DIR="$ROOT/sidequest-content/genre_packs/$GENRE/worlds/$WORLD/assets/portraits"
cd "$ROOT"
mkdir -p "$PORTRAITS_DIR"

before="$(cd "$PORTRAITS_DIR" && ls -1 2>/dev/null | sort || true)"
# Non-force run: images already on R2 are skipped, so only new pickers render.
uv run python scripts/generate_portrait_images.py --genre "$GENRE" --world "$WORLD"
after="$(cd "$PORTRAITS_DIR" && ls -1 2>/dev/null | sort || true)"

new="$(comm -13 <(printf '%s\n' "$before") <(printf '%s\n' "$after") | grep -E '\.png$' || true)"
if [ -z "$new" ]; then
  echo "[render_pickers] no new portraits for $GENRE/$WORLD (already on R2)"; exit 0
fi
echo "[render_pickers] new portraits for $GENRE/$WORLD:"; printf '  %s\n' $new

# Absolute paths for the sync.
files=""; for n in $new; do files="$files $PORTRAITS_DIR/$n"; done
uv run python scripts/r2_sync_packs.py --files $files
uv run python scripts/r2_manifest_from_bucket.py
echo "[render_pickers] done: $GENRE/$WORLD"
```

- [ ] **Step 2: Make it executable and smoke-test the arg guard**

```bash
cd /Users/slabgorb/Projects/oq-2
chmod +x scripts/render_pickers/render_one.sh
scripts/render_pickers/render_one.sh 2>&1 | head -1
```
Expected: usage error `usage: render_one.sh <genre> <world>` (proves the guard fires without touching the daemon).

- [ ] **Step 3: Generate one thin wrapper per expanded world**

```bash
cd /Users/slabgorb/Projects/oq-2/scripts/render_pickers
# One line per world touched by Tasks 2–12:
while read -r GENRE WORLD; do
  f="${GENRE}__${WORLD}.sh"
  printf '#!/usr/bin/env bash\nexec "$(dirname "$0")/render_one.sh" %s %s\n' "$GENRE" "$WORLD" > "$f"
  chmod +x "$f"
done <<'WORLDS'
wry_whimsy oz
wry_whimsy wonderland
wry_whimsy gulliver
space_opera coyote_star
space_opera perseus_cloud
space_opera aureate_span
spaghetti_western dust_and_lead
spaghetti_western five_points
spaghetti_western the_real_mccoy
heavy_metal barsoom
heavy_metal long_foundry
heavy_metal evropi
elemental_harmony burning_peace
elemental_harmony shattered_accord
tea_and_murder glenross
tea_and_murder blackthorn_moor
mutant_wasteland seaboard_of_saints
mutant_wasteland flickering_reach
caverns_and_claudes beneath_sunden
neon_dystopia franchise_nations
pulp_noir annees_folles
road_warrior the_circuit
WORLDS
ls *.sh | wc -l   # expected: 23 (22 wrappers + render_one.sh)
```

- [ ] **Step 4: Write `all.sh` (full sweep) and `README.md` (index)**

```bash
cd /Users/slabgorb/Projects/oq-2/scripts/render_pickers
cat > all.sh <<'EOF'
#!/usr/bin/env bash
# Render new pickers for ALL expanded worlds, in sequence. Run at leisure.
set -euo pipefail
here="$(dirname "$0")"
for s in "$here"/*__*.sh; do
  echo "=== $s ==="
  "$s"
done
EOF
chmod +x all.sh
```

Then create `README.md` listing each world, its wrapper script, and the run order, plus the standing constraints: **daemon must be warm**, always `uv run` (never bare `python3`), each script renders only new faces (idempotent re-runs), run one world or `all.sh` for everything.

- [ ] **Step 5: Commit the runbook** (orchestrator)

```bash
cd /Users/slabgorb/Projects/oq-2
git add scripts/render_pickers
git commit -m "feat(portraits): per-world picker render runbook (run at leisure)"
```

---

## Task 15: Coverage report

**Files:**
- Create: `docs/portraits/picker-coverage-2026-07.md`

- [ ] **Step 1: Generate before→after counts**

```bash
cd /Users/slabgorb/Projects/oq-2/sidequest-content
for f in $(find genre_packs -name portrait_manifest.yaml | sort); do
  world=$(echo "$f" | sed -E 's#genre_packs/([^/]+)/worlds/([^/]+)/.*#\1/\2#')
  after=$(grep -c 'type: player_picker' "$f")
  printf "%-40s after=%s\n" "$world" "$after"
done
```

- [ ] **Step 2: Write the report** — a markdown table per world: **before** (from the spec's baseline table), **after** (Step 1), **new faces**, **gap type addressed** (culture / archetype / volume), and **cultures now covered**. No plot content — cultures/archetypes/counts only (spoiler rule). Note the total new-face count (the render-cost figure).

- [ ] **Step 3: Commit** (orchestrator)

```bash
cd /Users/slabgorb/Projects/oq-2
git add docs/portraits/picker-coverage-2026-07.md
git commit -m "docs(portraits): picker coverage before/after report (2026-07 expansion)"
```

---

## Self-Review notes (author)

- **Spec coverage:** §method → Step A audit; §allocation rule → Global Constraints + Step C; §authoring discipline/schema → Global Constraints; §backdrop POI → Step A + validator loop (Step D); §deliverable 1 (YAML) → Tasks 2–12; §deliverable 2 (coverage report) → Task 15; §deliverable 3 (render scripts) → Task 14; §non-goals (no new archetypes / no code / no re-render) → Global Constraints + Task 5 Step 3 (only-gaps) + non-`--force` render. All covered.
- **Render idempotency:** non-`--force` skips existing R2 keys; the before/after dir diff isolates new files for sync — no full re-render, no stale-file sync.
- **Two repos, two branches:** content commits land on `feat/picker-portrait-expansion` (develop base); scripts/docs on `feat/picker-render-scripts` (main base). Kept distinct in Task 1.
