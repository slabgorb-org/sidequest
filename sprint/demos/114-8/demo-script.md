**Total runtime: ~8 minutes**

---

**Scene 1 — Title (Slide 1) | 0:00–0:30**

Open with the slide. Introduce the story in one sentence: "Today we're showing what it took to wire the mutant wasteland setting's gear to its rulebook — and why 'scrap armor giving zero protection' was a silent bug, not a corner case."

---

**Scene 2 — The Problem (Slide 2) | 0:30–2:00**

Show Slide 2 with the three defects.

**Live terminal: show the before state from git history:**
```bash
cd ~/Projects/sidequest-content
git show HEAD~1:genre_packs/mutant_wasteland/inventory.yaml | grep -A 8 "scrap_armor"
```
Expected output: `scrap_armor` entry with no `armor_class` field, no `provenance` block — just flavor text and name.

Then show the GM panel gap signal. Point to the `chargen.armor_unresolved` span name and explain: "This is the lie-detector. Before the fix, every time a wasteland character equipped scrap armor, the GM panel logged this gap span — the engine's way of saying 'I found armor but I have no AC to apply.'"

*Fallback if terminal unavailable: Slide 2 shows the before YAML snippet as a callout box.*

---

**Scene 3 — What We Built (Slide 3) | 2:00–4:30**

**Live terminal: show the fixed content:**
```bash
grep -A 20 "^  - id: scrap_armor" genre_packs/mutant_wasteland/inventory.yaml
```
Point out:
- `armor_class: 15` — the AC from AWN Scrap Mail, p.77
- `provenance: {mode: verbatim, srd: awn, license: wn-free, srd_ref: "AWN SRD Equipment — Scrap Mail"}`

Then show a weapon:
```bash
grep -A 22 "^  - id: sharpened_rebar" genre_packs/mutant_wasteland/inventory.yaml
```
Point out: `trauma_die: 1d8`, `trauma_rating: 3`, `shock: 2`, `shock_ac: 13`.

**Live terminal: run the wiring test:**
```bash
cd ~/Projects/sidequest-server
SIDEQUEST_DATABASE_URL=postgresql://$USER@localhost:5432/sidequest_test \
SIDEQUEST_GENRE_PACKS=~/Projects/sidequest-content/genre_packs \
uv run pytest tests/server/test_114_8_scrap_armor_ac_wiring.py -v 2>&1 | tail -20
```
Expected: `test_equipping_scrap_armor_derives_awn_ac_15 PASSED`, `test_scrap_armor_fires_equipped_span_not_unresolved PASSED`.

*Fallback: Slide 3 shows a screenshot of the passing test output.*

---

**Scene 4 — Why This Approach (Slide 4) | 4:30–5:30**

Refer to Slide 4. Explain the "bind, don't balance" doctrine in one analogy: "We could have hand-written AC 14 for scrap armor because it felt right for the wasteland difficulty. But we'd be implicitly re-balancing a game someone else designed for 200 pages. Verbatim sourcing — with machine-readable attribution — ends that loop permanently."

---

**Scene 5 — Before/After (Before/After Slide) | 5:30–6:30**

Show the Before/After slide. Key callouts for presenter:
- Before: `scrap_armor` → AC 10 (default, unprotected), `chargen.armor_unresolved` fires
- After: `scrap_armor` → AC 15 (AWN Scrap Mail), `chargen.armor_equipped` fires with `armor_class=15` in attrs

"The GM panel now sees a real armor resolution instead of a gap signal. The lie-detector works."

---

**Scene 6 — Roadmap (Roadmap Slide) | 6:30–7:30**

Refer to the Roadmap slide. Walk through what's next in epic 114.

---

**Scene 7 — Questions | 7:30–8:00**

Open for questions.

---