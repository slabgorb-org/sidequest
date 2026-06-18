# SRD Rules on the Rules Page — Phase 1 (Pipeline + Fate) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Surface the verbatim, player-facing Fate Core rules on the Rules reference page (`/reference/rules/<pack>`) as shared ruleset-tier content, with provenance and a fail-loud load gate — building the full pipeline (composition supports WN core+overlay) so the Without Number family is later a content-only follow-on (Plan B).

**Architecture:** New ruleset-tier content (`sidequest-content/rulesets/<ruleset>/srd/*.md`, Markdown + YAML front-matter). A server composition module (`sidequest/genre/ruleset_reference.py`) loads + composes chapters (flat for Fate; `without_number/core` + per-game overlay for the WN family) and builds a new `rules_document` section. `build_rules_projection` prepends that section; the genre loader gains a fail-loud gate. A new `RulesDocument` React renderer (react-markdown) displays chapters + provenance, slotting into the existing Rules-page ToC/anchor framework.

**Tech Stack:** Python 3.12 (FastAPI, pytest, uv), React/TypeScript (Vite, vitest), react-markdown + remark-gfm (new UI deps), YAML content.

## Global Constraints

- **Verbatim reproduction only** — chapters are faithful SRD text, never paraphrased. No `verbatim`/`license` front-matter is stamped on a chapter until it has been proof-read against the source (this plan ships Fate, whose epub source parses cleanly).
- **ADR-145 licensing:** Fate Core attribution is the canonical **CC-BY 3.0** notice (Evil Hat). WN rulesets use the free-use line. Attribution text **MUST NOT** imply endorsement, partnership, approval, or review by Evil Hat / Sine Nomine / Kevin Crawford.
- **No Silent Fallbacks:** a ruleset in the required-reference set with missing or unstamped content is a **loud load error** (`GenreLoadError`), never a silently empty page.
- **Player-facing chapters only** — no GM-only material (factions, adventure/sandbox design, bestiary, GM advice).
- **Tests use synthetic fixtures**, never live pack/world slugs (project rule: tests must not point at live content). Live-content verification is the final manual task.
- **Section identity:** the new section's `id` is the literal string `"ruleset_reference"`; its discriminator field is `type: "rules_document"`. Chapter anchor ids come from each file's front-matter `anchor`.
- **Required-reference set this plan:** `RULESETS_WITH_REFERENCE = {"fate"}`. Plan B extends it to the WN family. Rulesets not in the set with no content emit no section (no break for not-yet-authored WN packs).
- Test commands: server `cd sidequest-server && uv run pytest <path> -v`; UI `cd sidequest-ui && npx vitest run <path>`.
- Commit from each subrepo's own root on its feature branch; **land the sidequest-content change before enabling the server gate** (the gate reads content from `sidequest-content/rulesets/`).

---

## File Structure

**sidequest-content (content):**
- Create `rulesets/README.md` — documents the ruleset-tier; what the dir is, the core+overlay model, the front-matter contract.
- Create `rulesets/fate/srd/01-the-basics.md … NN-*.md` — the Fate Core player chapters (verbatim), each with provenance front-matter.

**sidequest-server (genre layer — composition + gate):**
- Create `sidequest/genre/ruleset_reference.py` — `RulesetReferenceError`, slug sets, label/provenance maps, `parse_frontmatter`, `load_ruleset_chapters`, `build_ruleset_reference_section`, `validate_ruleset_reference`.
- Modify `sidequest/genre/loader.py` — call `validate_ruleset_reference(...)` inside `load_genre_pack`.
- Modify `sidequest/server/reference_projection.py` — prepend the ruleset section in `build_rules_projection`.
- Tests: `tests/genre/test_ruleset_reference.py`, `tests/genre/test_ruleset_reference_load_gate.py`, `tests/server/test_rules_projection_ruleset_section.py`.

**sidequest-ui (renderer):**
- Modify `src/types/reference.ts` — `RulesChapter`, `RulesProvenance`, `RulesDocumentSection`; extend `ReferenceSection`.
- Create `src/components/reference/sections/RulesDocument.tsx` — the renderer.
- Modify `src/components/reference/sections/SectionDispatch.tsx` — dispatch `"ruleset_reference"`.
- Modify `src/screens/reference/buildToc.ts` — chapter sub-anchors for the new section.
- Modify `package.json` — add `react-markdown`, `remark-gfm`.
- Tests: `src/components/reference/sections/__tests__/RulesDocument.test.tsx`; update `SectionDispatch.test.tsx`, `buildToc.test.ts`.

**orchestrator (docs):**
- Create an ADR (or ADR-135 amendment) for the ruleset-tier content + `rules_document` section type.

---

## Task 1: Composition module — front-matter parse + chapter loading

**Files:**
- Create: `sidequest-server/sidequest/genre/ruleset_reference.py`
- Test: `sidequest-server/tests/genre/test_ruleset_reference.py`

**Interfaces:**
- Produces:
  - `class RulesetReferenceError(Exception)`
  - `parse_frontmatter(text: str) -> tuple[dict, str]` — returns `(meta, body)`; raises `RulesetReferenceError` if no `---` front-matter.
  - `load_ruleset_chapters(ruleset: str, *, rulesets_root: Path) -> list[dict]` — composed, ordered chapters; each dict has keys `anchor, title, order, srd_ref, body_markdown`. Overlay chapters override core chapters that share an `anchor`. Raises `RulesetReferenceError` on a file missing any required front-matter key.
  - Constants: `BOUND_RULESET_SLUGS`, `WN_FAMILY`, `REQUIRED_FRONTMATTER`.

- [ ] **Step 1: Write the failing test**

```python
# sidequest-server/tests/genre/test_ruleset_reference.py
from pathlib import Path

import pytest

from sidequest.genre.ruleset_reference import (
    RulesetReferenceError,
    load_ruleset_chapters,
    parse_frontmatter,
)


def _write(p: Path, anchor: str, title: str, order: int, body: str, *, srd="fixture", lic="ccby") -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        f"---\nsrd: {srd}\nsrd_ref: \"{title}\"\nlicense: {lic}\n"
        f"anchor: {anchor}\ntitle: {title}\norder: {order}\n---\n{body}\n",
        encoding="utf-8",
    )


def test_parse_frontmatter_splits_meta_and_body():
    meta, body = parse_frontmatter("---\nanchor: x\ntitle: X\n---\nHello **world**.\n")
    assert meta["anchor"] == "x"
    assert body.strip() == "Hello **world**."


def test_parse_frontmatter_missing_delimiter_raises():
    with pytest.raises(RulesetReferenceError):
        parse_frontmatter("no front-matter here")


def test_load_flat_ruleset_orders_by_order_field(tmp_path: Path):
    root = tmp_path / "rulesets"
    _write(root / "fixturefate" / "srd" / "b.md", "asp", "Aspects", 2, "Aspects body")
    _write(root / "fixturefate" / "srd" / "a.md", "basics", "Basics", 1, "Basics body")
    chapters = load_ruleset_chapters("fixturefate", rulesets_root=root)
    assert [c["anchor"] for c in chapters] == ["basics", "asp"]
    assert chapters[0]["body_markdown"].strip() == "Basics body"


def test_missing_required_frontmatter_key_raises(tmp_path: Path):
    root = tmp_path / "rulesets"
    p = root / "fixturefate" / "srd" / "bad.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("---\ntitle: NoAnchor\norder: 1\n---\nbody\n", encoding="utf-8")
    with pytest.raises(RulesetReferenceError):
        load_ruleset_chapters("fixturefate", rulesets_root=root)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/genre/test_ruleset_reference.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'sidequest.genre.ruleset_reference'`

- [ ] **Step 3: Write minimal implementation**

```python
# sidequest-server/sidequest/genre/ruleset_reference.py
"""Ruleset-tier SRD reference content: load, compose, and project player chapters.

Content lives in ``sidequest-content/rulesets/<ruleset>/srd/*.md`` (Markdown + YAML
front-matter). The four Without Number games share ``without_number/core`` and add a
thin per-game overlay; Fate is flat. See ADR-135/145/142 and the 2026-06-18 spec.
"""

from __future__ import annotations

from pathlib import Path

import yaml

BOUND_RULESET_SLUGS = frozenset({"fate", "wwn", "cwn", "swn", "awn"})
WN_FAMILY = frozenset({"wwn", "cwn", "swn", "awn"})
REQUIRED_FRONTMATTER = ("srd", "srd_ref", "license", "anchor", "title", "order")


class RulesetReferenceError(Exception):
    """Raised when ruleset reference content is missing or malformed."""


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split a Markdown file into (front-matter dict, body). Fail loud if absent."""
    if not text.startswith("---"):
        raise RulesetReferenceError("missing '---' front-matter delimiter")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise RulesetReferenceError("unterminated '---' front-matter block")
    meta = yaml.safe_load(parts[1]) or {}
    if not isinstance(meta, dict):
        raise RulesetReferenceError("front-matter is not a mapping")
    return meta, parts[2].lstrip("\n")


def _chapter_dirs(ruleset: str, rulesets_root: Path) -> list[Path]:
    if ruleset in WN_FAMILY:
        return [
            rulesets_root / "without_number" / "core" / "srd",
            rulesets_root / "without_number" / ruleset / "srd",
        ]
    return [rulesets_root / ruleset / "srd"]


def load_ruleset_chapters(ruleset: str, *, rulesets_root: Path) -> list[dict]:
    """Compose the ordered player chapters for ``ruleset``.

    Flat for Fate; core + per-game overlay for the WN family (overlay overrides core
    by shared ``anchor``). Raises ``RulesetReferenceError`` on a file missing any
    required front-matter key.
    """
    by_anchor: dict[str, dict] = {}
    for chapter_dir in _chapter_dirs(ruleset, rulesets_root):
        if not chapter_dir.is_dir():
            continue
        for md in sorted(chapter_dir.glob("*.md")):
            meta, body = parse_frontmatter(md.read_text(encoding="utf-8"))
            missing = [k for k in REQUIRED_FRONTMATTER if k not in meta]
            if missing:
                raise RulesetReferenceError(f"{md}: missing front-matter {missing}")
            by_anchor[str(meta["anchor"])] = {
                "anchor": str(meta["anchor"]),
                "title": str(meta["title"]),
                "order": int(meta["order"]),
                "srd_ref": str(meta["srd_ref"]),
                "body_markdown": body,
            }
    return sorted(by_anchor.values(), key=lambda c: c["order"])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/genre/test_ruleset_reference.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
cd sidequest-server
git add sidequest/genre/ruleset_reference.py tests/genre/test_ruleset_reference.py
git commit -m "feat(rules-ref): ruleset chapter loader + front-matter parse"
```

---

## Task 2: Section builder + provenance/labels

**Files:**
- Modify: `sidequest-server/sidequest/genre/ruleset_reference.py`
- Test: `sidequest-server/tests/genre/test_ruleset_reference.py` (extend)

**Interfaces:**
- Consumes: `load_ruleset_chapters` (Task 1).
- Produces:
  - `build_ruleset_reference_section(ruleset: str, *, rulesets_root: Path) -> dict | None` — returns a section dict `{"id": "ruleset_reference", "type": "rules_document", "label": str, "ruleset": str, "chapters": list[dict], "provenance": dict}`, or `None` for a non-bound ruleset or an empty (not-yet-authored) one.
  - `RULESET_LABEL: dict[str, str]`, `RULESET_PROVENANCE: dict[str, dict]`.

- [ ] **Step 1: Write the failing test**

```python
# append to sidequest-server/tests/genre/test_ruleset_reference.py
from sidequest.genre.ruleset_reference import build_ruleset_reference_section


def test_build_section_none_for_native_ruleset(tmp_path: Path):
    assert build_ruleset_reference_section("dial", rulesets_root=tmp_path / "rulesets") is None


def test_build_section_none_when_unauthored(tmp_path: Path):
    # 'fate' is bound but no content on disk -> None (gate, not builder, enforces presence)
    assert build_ruleset_reference_section("fate", rulesets_root=tmp_path / "rulesets") is None


def test_build_section_shape_and_provenance(tmp_path: Path):
    root = tmp_path / "rulesets"
    _write(root / "fate" / "srd" / "01.md", "fate-basics", "The Basics", 1, "How play works.")
    section = build_ruleset_reference_section("fate", rulesets_root=root)
    assert section is not None
    assert section["id"] == "ruleset_reference"
    assert section["type"] == "rules_document"
    assert section["ruleset"] == "fate"
    assert section["label"] == "The Rules of Fate Core"
    assert section["chapters"][0]["anchor"] == "fate-basics"
    assert section["provenance"]["license"] == "ccby"
    assert "Creative Commons" in section["provenance"]["attribution"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/genre/test_ruleset_reference.py -v`
Expected: FAIL — `ImportError: cannot import name 'build_ruleset_reference_section'`

- [ ] **Step 3: Write minimal implementation**

```python
# append to sidequest-server/sidequest/genre/ruleset_reference.py

RULESET_LABEL: dict[str, str] = {
    "fate": "The Rules of Fate Core",
    "wwn": "Worlds Without Number — Player Reference",
    "cwn": "Cities Without Number — Player Reference",
    "swn": "Stars Without Number — Player Reference",
    "awn": "Ashes Without Number — Player Reference",
}

_WN_ATTRIB = (
    "Reproduced from the {name} System Reference Document under its free-use terms. "
    "Not affiliated with, endorsed by, or reviewed by Sine Nomine Publishing."
)

RULESET_PROVENANCE: dict[str, dict] = {
    "fate": {
        "source": "Fate Core System (Evil Hat Productions)",
        "license": "ccby",
        "attribution": (
            "This work is based on Fate Core System (found at http://www.faterpg.com/), "
            "a product of Evil Hat Productions, LLC, developed, authored, and edited by "
            "Leonard Balsera, Brian Engard, Jeremy Keller, Ryan Macklin, Mike Olson, "
            "Clark Valentine, Amanda Valentine, Fred Hicks, and Rob Donoghue, and licensed "
            "for our use under the Creative Commons Attribution 3.0 Unported license "
            "(http://creativecommons.org/licenses/by/3.0/)."
        ),
    },
    "wwn": {"source": "Worlds Without Number SRD", "license": "wn-free",
            "attribution": _WN_ATTRIB.format(name="Worlds Without Number")},
    "cwn": {"source": "Cities Without Number SRD", "license": "wn-free",
            "attribution": _WN_ATTRIB.format(name="Cities Without Number")},
    "swn": {"source": "Stars Without Number SRD", "license": "wn-free",
            "attribution": _WN_ATTRIB.format(name="Stars Without Number")},
    "awn": {"source": "Ashes Without Number SRD", "license": "wn-free",
            "attribution": _WN_ATTRIB.format(name="Ashes Without Number")},
}


def build_ruleset_reference_section(ruleset: str, *, rulesets_root: Path) -> dict | None:
    """Build the ``rules_document`` section for ``ruleset``, or ``None`` if not applicable."""
    if ruleset not in BOUND_RULESET_SLUGS:
        return None
    chapters = load_ruleset_chapters(ruleset, rulesets_root=rulesets_root)
    if not chapters:
        return None
    return {
        "id": "ruleset_reference",
        "type": "rules_document",
        "label": RULESET_LABEL[ruleset],
        "ruleset": ruleset,
        "chapters": chapters,
        "provenance": RULESET_PROVENANCE[ruleset],
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/genre/test_ruleset_reference.py -v`
Expected: PASS (7 passed)

- [ ] **Step 5: Commit**

```bash
cd sidequest-server
git add sidequest/genre/ruleset_reference.py tests/genre/test_ruleset_reference.py
git commit -m "feat(rules-ref): rules_document section builder + provenance"
```

---

## Task 3: Fate SRD content extraction (sidequest-content)

> This is the verbatim reproduction task. It produces the real Fate Core player chapters. It is the largest task by effort; structurally it is "author the Markdown files + stamp provenance, then verify they parse and compose."

**Files:**
- Create: `sidequest-content/rulesets/README.md`
- Create: `sidequest-content/rulesets/fate/srd/01-the-basics.md`, `02-aspects-and-fate-points.md`, `03-skills.md`, `04-stunts.md`, `05-actions-and-outcomes.md`, `06-challenges-contests-conflicts.md` (chapter list per the Fate Core player content; add/rename as the source dictates)
- Source: `~/Documents/DriveThruRPG/Evil Hat Productions/Fate Core System/Fate_Core_ePub_Edition.epub` (CC-BY)

**Interfaces:**
- Produces: on-disk content that `load_ruleset_chapters("fate", rulesets_root=<content>/rulesets)` composes into ordered chapters, each with complete front-matter.

- [ ] **Step 1: Extract the player chapters from the Fate Core epub**

Convert the epub to text and identify the player-facing chapters (exclude GM-only "Running the Game", "Scenes/Sessions/Scenarios" GM-advice, "The Bronze Rule"/system-hacking appendices). Player chapters: The Basics; Aspects and Fate Points; Skills (and the skill list/ladder); Stunts; Actions and Outcomes (the four actions × four outcomes, the ladder); Challenges, Contests, and Conflicts. Each becomes one `NN-*.md`.

```bash
# one option for clean text from epub (epub is a zip of XHTML):
cd ~/Documents/DriveThruRPG/Evil\ Hat\ Productions/Fate\ Core\ System
mkdir -p /tmp/fate_epub && unzip -o Fate_Core_ePub_Edition.epub -d /tmp/fate_epub >/dev/null
ls /tmp/fate_epub/OEBPS 2>/dev/null || find /tmp/fate_epub -name '*.xhtml' -o -name '*.html' | head
```

- [ ] **Step 2: Author each chapter file with front-matter (verbatim body)**

Each file's body is the verbatim chapter text as Markdown (headings `##`/`###`, tables as GFM tables, lists as `-`). Example shape (body abridged here — the real file carries the full verbatim chapter):

```markdown
---
srd: fate
srd_ref: "Fate Core System — The Basics"
license: ccby
anchor: fate-basics
title: The Basics
order: 1
---
## The Basics

Fate is a game of … <verbatim Fate Core "The Basics" chapter text> …

### The Ladder

| Rating | Name |
| --- | --- |
| +8 | Legendary |
| +7 | Epic |
…
```

Repeat for `02..06`, assigning `order` 2..6 and stable `anchor`s: `fate-aspects`, `fate-skills`, `fate-stunts`, `fate-actions`, `fate-challenges-contests-conflicts`.

- [ ] **Step 3: Author the tier README**

```markdown
<!-- sidequest-content/rulesets/README.md -->
# Ruleset-tier reference content

Verbatim, player-facing SRD rules, authored **once per ruleset** and surfaced on every
pack's Rules page (`/reference/rules/<pack>`) that binds the ruleset. This is the first
content that is neither genre- nor world-tier.

- `fate/srd/*.md` — Fate Core player chapters (CC-BY 3.0, Evil Hat).
- `without_number/core/srd/*.md` — shared WN player chapters (Plan B).
- `without_number/{wwn,cwn,swn,awn}/srd/*.md` — per-game overlays; a file whose `anchor`
  matches a core file overrides it.

Each `.md` carries front-matter: `srd`, `srd_ref`, `license`, `anchor`, `title`, `order`.
All six are required (the server fails loud on a missing key). Bodies are **verbatim** —
never paraphrased — and proof-read before the `license` stamp. Attribution is rendered on
the page; it must never imply endorsement by the publisher (ADR-145 §D4a).
```

- [ ] **Step 4: Verify the content parses and composes**

Run (uses the real content dir, read-only check — not a committed test):
```bash
cd sidequest-server && uv run python -c "
from pathlib import Path
from sidequest.genre.ruleset_reference import build_ruleset_reference_section
root = Path('../sidequest-content/rulesets')
s = build_ruleset_reference_section('fate', rulesets_root=root)
print('chapters:', [c['anchor'] for c in s['chapters']])
print('license:', s['provenance']['license'])
"
```
Expected: prints the ordered fate anchors and `license: ccby`. No `RulesetReferenceError`.

- [ ] **Step 5: Commit (sidequest-content — land before the server gate)**

```bash
cd sidequest-content
git add rulesets/
git commit -m "content(rules-ref): Fate Core player chapters (verbatim, CC-BY)"
```

---

## Task 4: Fail-loud load gate (wire into the genre loader)

**Files:**
- Modify: `sidequest-server/sidequest/genre/ruleset_reference.py` (add `validate_ruleset_reference`, `RULESETS_WITH_REFERENCE`)
- Modify: `sidequest-server/sidequest/genre/loader.py` (call it inside `load_genre_pack`, near line 2225)
- Test: `sidequest-server/tests/genre/test_ruleset_reference_load_gate.py`

**Interfaces:**
- Consumes: `load_ruleset_chapters` (Task 1), `GenreLoadError` (`sidequest.genre.error`).
- Produces: `validate_ruleset_reference(ruleset: str, *, rulesets_root: Path, pack_name: str, required: frozenset[str] = RULESETS_WITH_REFERENCE) -> None` — raises `GenreLoadError` if `ruleset` is in `required` but composes to zero chapters, or if any chapter is malformed. No-op otherwise.

- [ ] **Step 1: Write the failing test**

```python
# sidequest-server/tests/genre/test_ruleset_reference_load_gate.py
from pathlib import Path

import pytest

from sidequest.genre.error import GenreLoadError
from sidequest.genre.ruleset_reference import validate_ruleset_reference


def _write(p: Path, anchor: str, order: int) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        f"---\nsrd: fate\nsrd_ref: \"R\"\nlicense: ccby\nanchor: {anchor}\ntitle: T\norder: {order}\n---\nbody\n",
        encoding="utf-8",
    )


def test_gate_passes_when_required_content_present(tmp_path: Path):
    root = tmp_path / "rulesets"
    _write(root / "fate" / "srd" / "01.md", "fate-basics", 1)
    validate_ruleset_reference("fate", rulesets_root=root, pack_name="wry_whimsy", required=frozenset({"fate"}))


def test_gate_fails_when_required_content_missing(tmp_path: Path):
    with pytest.raises(GenreLoadError):
        validate_ruleset_reference(
            "fate", rulesets_root=tmp_path / "rulesets", pack_name="wry_whimsy", required=frozenset({"fate"})
        )


def test_gate_noop_for_unrequired_ruleset(tmp_path: Path):
    # wwn not in the required set this phase -> no error even with no content
    validate_ruleset_reference("wwn", rulesets_root=tmp_path / "rulesets", pack_name="caverns_and_claudes", required=frozenset({"fate"}))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/genre/test_ruleset_reference_load_gate.py -v`
Expected: FAIL — `ImportError: cannot import name 'validate_ruleset_reference'`

- [ ] **Step 3: Write minimal implementation**

```python
# append to sidequest-server/sidequest/genre/ruleset_reference.py
from sidequest.genre.error import GenreLoadError

# Rulesets whose reference content MUST be present + complete (fail-loud).
# Phase 1 ships Fate only; Plan B (WN family) extends this set.
RULESETS_WITH_REFERENCE = frozenset({"fate"})


def validate_ruleset_reference(
    ruleset: str,
    *,
    rulesets_root: Path,
    pack_name: str,
    required: frozenset[str] = RULESETS_WITH_REFERENCE,
) -> None:
    """Fail loud if a required ruleset has missing/unstamped reference content."""
    if ruleset not in required:
        return
    try:
        chapters = load_ruleset_chapters(ruleset, rulesets_root=rulesets_root)
    except RulesetReferenceError as exc:
        raise GenreLoadError(
            path=rulesets_root / ruleset,
            detail=f"pack '{pack_name}': malformed {ruleset} reference content — {exc}",
        ) from exc
    if not chapters:
        raise GenreLoadError(
            path=rulesets_root / ruleset / "srd",
            detail=(
                f"pack '{pack_name}': ruleset '{ruleset}' requires reference content under "
                f"rulesets/{ruleset}/srd/ but none was found (No Silent Fallbacks)"
            ),
        )
```

Note: confirm `GenreLoadError(path=..., detail=...)` matches its constructor (loader.py uses this kwarg form, e.g. `loader.py:161`). If the signature differs, match the existing call form.

- [ ] **Step 4: Wire into the loader**

In `sidequest-server/sidequest/genre/loader.py`, add the import near line 22:

```python
from sidequest.genre.ruleset_reference import validate_ruleset_reference
```

Inside `load_genre_pack(path)` (def at line 1999), after `rules` is loaded and alongside the other validators (near `_validate_genre_baseline_no_bespoke(...)` at line 2225), add:

```python
    validate_ruleset_reference(
        rules.ruleset,
        rulesets_root=path.parent.parent / "rulesets",
        pack_name=path.name,
    )
```

- [ ] **Step 5: Run tests (gate unit + a real Fate pack still loads)**

Run: `cd sidequest-server && uv run pytest tests/genre/test_ruleset_reference_load_gate.py -v`
Expected: PASS (3 passed)

Run (real pack — needs Task 3 content committed in sidequest-content):
```bash
cd sidequest-server && uv run python -c "
from sidequest.genre.loader import load_genre_pack
from pathlib import Path
p = load_genre_pack(Path('../sidequest-content/genre_packs/wry_whimsy'))
print('loaded', p.slug if hasattr(p,'slug') else 'wry_whimsy', 'ruleset=', p.rules.ruleset)
"
```
Expected: loads without `GenreLoadError` (Fate content present). If it raises "requires reference content," Task 3 content is missing — land it first.

- [ ] **Step 6: Commit**

```bash
cd sidequest-server
git add sidequest/genre/ruleset_reference.py sidequest/genre/loader.py tests/genre/test_ruleset_reference_load_gate.py
git commit -m "feat(rules-ref): fail-loud load gate for required ruleset reference content"
```

---

## Task 5: Project the section into the Rules page payload

**Files:**
- Modify: `sidequest-server/sidequest/server/reference_projection.py` (`build_rules_projection`, ~line 666–697; add a `_read_ruleset` helper)
- Test: `sidequest-server/tests/server/test_rules_projection_ruleset_section.py`

**Interfaces:**
- Consumes: `build_ruleset_reference_section` (Task 2).
- Produces: `build_rules_projection` output whose `sections[0]` is the `rules_document` section when the pack binds a ruleset with authored content.

- [ ] **Step 1: Write the failing test**

```python
# sidequest-server/tests/server/test_rules_projection_ruleset_section.py
from pathlib import Path

from sidequest.server.reference_projection import build_rules_projection


def _seed_fate_content(content_root: Path) -> None:
    srd = content_root / "rulesets" / "fate" / "srd"
    srd.mkdir(parents=True, exist_ok=True)
    (srd / "01.md").write_text(
        "---\nsrd: fate\nsrd_ref: \"Basics\"\nlicense: ccby\nanchor: fate-basics\ntitle: The Basics\norder: 1\n---\nHow play works.\n",
        encoding="utf-8",
    )


def test_rules_projection_prepends_ruleset_section(tmp_path: Path):
    content_root = tmp_path / "sidequest-content"
    pack_dir = content_root / "genre_packs" / "smoke_pack"
    pack_dir.mkdir(parents=True, exist_ok=True)
    (pack_dir / "rules.yaml").write_text("ruleset: fate\n", encoding="utf-8")
    _seed_fate_content(content_root)

    doc = build_rules_projection("smoke_pack", pack_dir=pack_dir)
    assert doc["sections"][0]["id"] == "ruleset_reference"
    assert doc["sections"][0]["type"] == "rules_document"
    assert doc["sections"][0]["chapters"][0]["anchor"] == "fate-basics"


def test_rules_projection_no_section_for_native_pack(tmp_path: Path):
    content_root = tmp_path / "sidequest-content"
    pack_dir = content_root / "genre_packs" / "native_pack"
    pack_dir.mkdir(parents=True, exist_ok=True)
    (pack_dir / "rules.yaml").write_text("ruleset: dial\n", encoding="utf-8")

    doc = build_rules_projection("native_pack", pack_dir=pack_dir)
    assert all(s["id"] != "ruleset_reference" for s in doc["sections"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/server/test_rules_projection_ruleset_section.py -v`
Expected: FAIL — `sections[0]["id"]` is not `"ruleset_reference"` (section not emitted yet).

- [ ] **Step 3: Write minimal implementation**

In `reference_projection.py`, add the import at the top (near the other `sidequest.genre` imports):

```python
from sidequest.genre.ruleset_reference import build_ruleset_reference_section
```

Add a helper above `build_rules_projection`:

```python
def _read_ruleset(pack_dir: Path) -> str:
    """Read the bound ruleset slug from a pack's rules.yaml (default 'dial')."""
    rules_path = pack_dir / "rules.yaml"
    if not rules_path.exists():
        return "dial"
    data = yaml.safe_load(rules_path.read_text(encoding="utf-8")) or {}
    return str(data.get("ruleset", "dial")) if isinstance(data, dict) else "dial"
```

In `build_rules_projection`, replace the final `return {...}` with:

```python
    ruleset_section = build_ruleset_reference_section(
        _read_ruleset(pack_dir), rulesets_root=pack_dir.parent.parent / "rulesets"
    )
    if ruleset_section is not None:
        sections.insert(0, ruleset_section)

    return {"schema_version": 1, "pack": pack, "sections": sections}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/server/test_rules_projection_ruleset_section.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Wiring check — the live endpoint emits it**

Confirm the endpoint path is exercised (the route calls `build_rules_projection`, reference_routes.py:116). Add this wiring assertion to the same test file:

```python
def test_endpoint_handler_uses_projection(tmp_path: Path):
    # The route (reference_routes.rules_api) calls build_rules_projection(pack, pack_dir=...).
    # This asserts the projection is the seam the endpoint uses, so the section reaches the wire.
    import inspect
    from sidequest.server import reference_routes
    src = inspect.getsource(reference_routes)
    assert "build_rules_projection" in src
```

Run: `cd sidequest-server && uv run pytest tests/server/test_rules_projection_ruleset_section.py -v`
Expected: PASS (3 passed)

- [ ] **Step 6: Commit**

```bash
cd sidequest-server
git add sidequest/server/reference_projection.py tests/server/test_rules_projection_ruleset_section.py
git commit -m "feat(rules-ref): prepend rules_document section in build_rules_projection"
```

---

## Task 6: UI types + Markdown dependency

**Files:**
- Modify: `sidequest-ui/src/types/reference.ts`
- Modify: `sidequest-ui/package.json` (add deps)

**Interfaces:**
- Produces: `RulesChapter`, `RulesProvenance`, `RulesDocumentSection` types; `RulesDocumentSection` added to `ReferenceSection` union.

- [ ] **Step 1: Add the dependency**

```bash
cd sidequest-ui
# react-markdown 9 + remark-gfm 4 require React 18+. Confirm React major:
node -p "require('./package.json').dependencies.react"
npm install react-markdown@^9 remark-gfm@^4
```
Expected: `react` is `^18` (or 18.x); install adds the two deps.

- [ ] **Step 2: Add the types**

In `src/types/reference.ts`, add (near `GenericSection`, ~line 23):

```typescript
export interface RulesChapter {
  anchor: string;
  title: string;
  order: number;
  srd_ref: string;
  body_markdown: string;
}

export interface RulesProvenance {
  source: string;
  license: "wn-free" | "ccby";
  attribution: string;
}

export interface RulesDocumentSection {
  id: "ruleset_reference";
  type: "rules_document";
  label: string;
  ruleset: string;
  chapters: RulesChapter[];
  provenance: RulesProvenance;
}
```

Extend the `ReferenceSection` union (~line 127):

```typescript
export type ReferenceSection =
  | GenericSection
  | PoiSectionData
  | CastSectionData
  | TimelineSectionData
  | MapSectionData
  | RulesDocumentSection;
```

- [ ] **Step 3: Typecheck**

Run: `cd sidequest-ui && npx tsc --noEmit`
Expected: 0 errors.

- [ ] **Step 4: Commit**

```bash
cd sidequest-ui
git add src/types/reference.ts package.json package-lock.json
git commit -m "feat(rules-ref): RulesDocumentSection types + react-markdown dep"
```

---

## Task 7: RulesDocument renderer component

**Files:**
- Create: `sidequest-ui/src/components/reference/sections/RulesDocument.tsx`
- Test: `sidequest-ui/src/components/reference/sections/__tests__/RulesDocument.test.tsx`

**Interfaces:**
- Consumes: `RulesDocumentSection` (Task 6), `slugify` (existing, same import path as TimelineSection uses).
- Produces: `RulesDocument({ section }: { section: RulesDocumentSection })` — renders `<section id="section-ruleset-reference">`, the label heading, each chapter (`<article id={chapter.anchor}>` + markdown body), and a provenance footer.

- [ ] **Step 1: Write the failing test**

```tsx
// sidequest-ui/src/components/reference/sections/__tests__/RulesDocument.test.tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { RulesDocument } from "../RulesDocument";
import type { RulesDocumentSection } from "../../../../types/reference";

const section: RulesDocumentSection = {
  id: "ruleset_reference",
  type: "rules_document",
  label: "The Rules of Fate Core",
  ruleset: "fate",
  chapters: [
    { anchor: "fate-basics", title: "The Basics", order: 1, srd_ref: "Basics", body_markdown: "Play uses **aspects**." },
    { anchor: "fate-skills", title: "Skills", order: 2, srd_ref: "Skills", body_markdown: "## Skills\n\nSkills measure what you can do." },
  ],
  provenance: { source: "Fate Core System", license: "ccby", attribution: "Licensed under Creative Commons Attribution 3.0." },
};

describe("RulesDocument", () => {
  it("renders the label heading and an anchor per chapter", () => {
    const { container } = render(<RulesDocument section={section} />);
    expect(screen.getByRole("heading", { name: "The Rules of Fate Core" })).toBeInTheDocument();
    expect(container.querySelector("#fate-basics")).not.toBeNull();
    expect(container.querySelector("#fate-skills")).not.toBeNull();
    expect(container.querySelector("#section-ruleset-reference")).not.toBeNull();
  });

  it("renders markdown bodies", () => {
    render(<RulesDocument section={section} />);
    expect(screen.getByText("aspects")).toBeInTheDocument(); // <strong>aspects</strong>
    expect(screen.getByRole("heading", { name: "Skills", level: 2 })).toBeInTheDocument();
  });

  it("renders the provenance attribution", () => {
    render(<RulesDocument section={section} />);
    expect(screen.getByText(/Creative Commons Attribution 3.0/)).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-ui && npx vitest run src/components/reference/sections/__tests__/RulesDocument.test.tsx`
Expected: FAIL — cannot resolve `../RulesDocument`.

- [ ] **Step 3: Write the implementation**

```tsx
// sidequest-ui/src/components/reference/sections/RulesDocument.tsx
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { slugify } from "../nodeShape";
import type { RulesDocumentSection } from "../../../types/reference";

export function RulesDocument({ section }: { section: RulesDocumentSection }) {
  return (
    <section
      className="reference-section reference-section--rules-document"
      id={`section-${slugify(section.id)}`}
    >
      <h2 className="reference-section__label">{section.label}</h2>
      {section.chapters.map((chapter) => (
        <article key={chapter.anchor} id={chapter.anchor} className="rules-document__chapter">
          <h3 className="rules-document__chapter-title">{chapter.title}</h3>
          <div className="rules-document__body">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{chapter.body_markdown}</ReactMarkdown>
          </div>
        </article>
      ))}
      <footer className="rules-document__provenance">
        <p>{section.provenance.attribution}</p>
      </footer>
    </section>
  );
}
```

Note: confirm `slugify` is exported from `../nodeShape` (TimelineSection imports it from there per the extracted code). If it lives elsewhere, match TimelineSection's import.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-ui && npx vitest run src/components/reference/sections/__tests__/RulesDocument.test.tsx`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
cd sidequest-ui
git add src/components/reference/sections/RulesDocument.tsx src/components/reference/sections/__tests__/RulesDocument.test.tsx
git commit -m "feat(rules-ref): RulesDocument prose renderer"
```

---

## Task 8: Dispatch + ToC integration

**Files:**
- Modify: `sidequest-ui/src/components/reference/sections/SectionDispatch.tsx` (~line 30–59)
- Modify: `sidequest-ui/src/screens/reference/buildToc.ts` (~line 23–37)
- Test: extend `sidequest-ui/src/components/reference/sections/__tests__/SectionDispatch.test.tsx` and `src/screens/reference/__tests__/buildToc.test.ts` (create if absent)

**Interfaces:**
- Consumes: `RulesDocument` (Task 7), `RulesDocumentSection` (Task 6).
- Produces: dispatch routes `id === "ruleset_reference"` to `RulesDocument`; `buildToc` emits a top-level entry for the section with one child per chapter (`{ id: chapter.anchor, label: chapter.title }`).

- [ ] **Step 1: Write the failing tests**

```tsx
// append to SectionDispatch.test.tsx
import { RulesDocumentSection } from "../../../../types/reference";

it("dispatches ruleset_reference to RulesDocument", () => {
  const section = {
    id: "ruleset_reference", type: "rules_document", label: "The Rules of Fate Core", ruleset: "fate",
    chapters: [{ anchor: "fate-basics", title: "The Basics", order: 1, srd_ref: "B", body_markdown: "Body." }],
    provenance: { source: "Fate Core System", license: "ccby", attribution: "CC BY 3.0." },
  } as RulesDocumentSection;
  const { container } = render(<SectionDispatch section={section} />);
  expect(container.querySelector("#fate-basics")).not.toBeNull();
});
```

```ts
// sidequest-ui/src/screens/reference/__tests__/buildToc.test.ts
import { describe, expect, it } from "vitest";
import { buildToc } from "../buildToc";
import type { RulesDocumentSection } from "../../../types/reference";

describe("buildToc rules_document", () => {
  it("emits a chapter child per chapter", () => {
    const section: RulesDocumentSection = {
      id: "ruleset_reference", type: "rules_document", label: "The Rules of Fate Core", ruleset: "fate",
      chapters: [
        { anchor: "fate-basics", title: "The Basics", order: 1, srd_ref: "B", body_markdown: "x" },
        { anchor: "fate-skills", title: "Skills", order: 2, srd_ref: "S", body_markdown: "y" },
      ],
      provenance: { source: "Fate Core System", license: "ccby", attribution: "CC BY 3.0." },
    };
    const [item] = buildToc([section], "cards");
    expect(item.children.map((c) => c.id)).toEqual(["fate-basics", "fate-skills"]);
    expect(item.children.map((c) => c.label)).toEqual(["The Basics", "Skills"]);
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd sidequest-ui && npx vitest run src/components/reference/sections/__tests__/SectionDispatch.test.tsx src/screens/reference/__tests__/buildToc.test.ts`
Expected: FAIL — dispatch hits the generic/default branch (no `#fate-basics`); buildToc returns no children for the section.

- [ ] **Step 3: Implement dispatch**

In `SectionDispatch.tsx`, add a `case` before `default:` and the import:

```tsx
import { RulesDocument } from "./RulesDocument";
import type { RulesDocumentSection } from "../../../types/reference";
```

```tsx
    case "ruleset_reference":
      return <RulesDocument section={section as RulesDocumentSection} />;
```

- [ ] **Step 4: Implement buildToc branch**

In `buildToc.ts`, inside the `.map`, before the existing dict-node `if`:

```typescript
    if (section.id === "ruleset_reference" && "chapters" in section) {
      item.children = section.chapters.map((chapter) => ({
        id: chapter.anchor,
        label: chapter.title,
      }));
      return item;
    }
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd sidequest-ui && npx vitest run src/components/reference/sections/__tests__/SectionDispatch.test.tsx src/screens/reference/__tests__/buildToc.test.ts`
Expected: PASS.

- [ ] **Step 6: Full UI gate**

Run: `cd sidequest-ui && npx vitest run && npx tsc --noEmit && npx eslint src`
Expected: all green.

- [ ] **Step 7: Commit**

```bash
cd sidequest-ui
git add src/components/reference/sections/SectionDispatch.tsx src/screens/reference/buildToc.ts src/components/reference/sections/__tests__/SectionDispatch.test.tsx src/screens/reference/__tests__/buildToc.test.ts
git commit -m "feat(rules-ref): dispatch + ToC for the ruleset reference section"
```

---

## Task 9: ADR for the ruleset-tier content + rules_document section

**Files:**
- Create: `docs/adr/NNN-ruleset-tier-srd-reference.md` (next free number) OR add an "Amendment" section to `docs/adr/135-reference-pages-public-table-tool.md`.

**Interfaces:** none (documentation).

- [ ] **Step 1: Write the ADR**

Decide number via `ls docs/adr/ | tail`. Record: the new `sidequest-content/rulesets/` tier (first non-genre/world content), the `rules_document` reference section type + prose renderer, the front-matter contract, the fail-loud `RULESETS_WITH_REFERENCE` gate, and the ADR-145 attribution/no-endorsement rule. Cross-reference ADR-135 (extends the reference projection), ADR-145 (licensing), ADR-142 (WN core composition). Follow the ADR frontmatter schema (ADR-088) and run `scripts/regenerate_adr_indexes.py` if a new ADR is added.

- [ ] **Step 2: Commit (orchestrator, from repo root on its branch)**

```bash
cd /Users/slabgorb/Projects/oq-2
git add docs/adr/
git commit -m "docs(adr): ruleset-tier SRD reference content + rules_document section"
```

---

## Task 10: End-to-end verification (live Fate Rules page)

**Files:** none (verification).

- [ ] **Step 1: Restart the server (reloads cached packs/content)**

`--reload` does not reload YAML/content; bounce it. Then load a Fate pack page.

- [ ] **Step 2: Verify the API payload**

```bash
curl -s localhost:8765/reference/api/rules/wry_whimsy | python3 -m json.tool | grep -A3 '"ruleset_reference"' | head
```
Expected: a `ruleset_reference` section with `type: rules_document` and Fate chapters.

- [ ] **Step 3: Verify in the browser**

Open `http://localhost:5173/reference/rules/wry_whimsy`. Expected: a top section "The Rules of Fate Core" with readable chapters (The Basics, Aspects…, Skills, Stunts, Actions and Outcomes, Challenges/Contests/Conflicts), the chapters in the sticky ToC with working anchor links, and the CC-BY attribution footer. Confirm a WN pack (`/reference/rules/caverns_and_claudes`) is unchanged (no ruleset section yet — Plan B).

- [ ] **Step 4: Verify the fail-loud gate**

Temporarily rename `sidequest-content/rulesets/fate/srd` and reload `wry_whimsy`; confirm a loud `GenreLoadError` naming the missing reference content. Restore the dir.

---

## Self-Review

**Spec coverage:**
- "Reproduce verbatim player chapters (Fate)" → Task 3. "All five" → Fate here; WN family is Plan B (spec's endorsed Fate-first sequence), pipeline ready (Tasks 1–2 handle core+overlay, fixture-tested).
- "Ruleset-tier shared content, WN core shared" → Task 1 (`_chapter_dirs` core+overlay), Task 3 (`rulesets/`), README.
- "New `rules_document` section + prose renderer" → Tasks 2, 5 (server), 6, 7 (UI).
- "ADR-145 provenance, no endorsement" → Task 2 (provenance maps), Global Constraints.
- "Fail-loud gate" → Task 4.
- "Slot into existing ToC/anchor framework" → Task 8.
- "ADR for new tier + section type" → Task 9.
- "Phase-2 deep-link anchors ready" → chapter `anchor` ids (Tasks 1–2) + per-chapter `id` in the renderer (Task 7).

**Placeholder scan:** chapter bodies in Task 3 are the one place real content is authored, not pasted into the plan (it is verbatim SRD reproduction from the epub — the plan gives the extraction method, file list, front-matter, and a verify step). All code steps carry complete code.

**Type consistency:** section dict keys (`id`/`type`/`label`/`ruleset`/`chapters`/`provenance`) match across Task 2 (server), Task 5 (projection), Task 6 (TS type), Task 7 (renderer), Task 8 (dispatch/ToC). Chapter keys (`anchor`/`title`/`order`/`srd_ref`/`body_markdown`) match Task 1 → Task 6/7/8. `validate_ruleset_reference` signature consistent Task 4 → loader wiring.

**Open confirmations flagged inline:** `GenreLoadError(path=, detail=)` kwarg form (Task 4), `slugify` import path (Task 7), React major ≥18 for react-markdown 9 (Task 6).
