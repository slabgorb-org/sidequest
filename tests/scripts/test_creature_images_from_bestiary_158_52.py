"""Story 158-52 (RED) — creature-image production derives from bestiary.yaml.

Today ``scripts/generate_creature_images.py::collect_creatures`` only rglobs
``creatures.yaml``, so creature portraits render for just 2 of 22 WN-bound
worlds (beneath_sunden, flickering_reach). Every other world ships a
``bestiary.yaml`` runtime roster (encountergen samples it — it IS the WN-path
roster) but no hand-authored image manifest, so it collects ZERO renderable
creatures.

This story makes the BESTIARY the single source of truth for creature-image
production: ``collect_creatures`` derives ``{id, name, description,
threat_level<-level, tags}`` from each ``bestiary.yaml`` entry, and a per-world
``creatures.yaml`` becomes an OPTIONAL per-field OVERRIDE (naming conceits +
bespoke marquee plates), NOT a precondition.

These tests drive the REAL ``collect_creatures`` / ``compose_prompt`` against
real shipped content — this is the wiring test (the production functions are
exercised end-to-end, not mocked):

* ``space_opera/coyote_star`` (SWN) — a manifest-LESS world; proves derivation
  scales portraits past the 2 hand-authored worlds (AC4 + AC1).
* ``caverns_and_claudes/beneath_sunden`` (WWN) — a "nothing is named" world;
  proves the ``creatures.yaml`` naming override wins per-field (AC1) and that
  the derived CLIP never paints a bestiary proper noun (AC2), while a normal
  world keeps its names (the de-proper-noun'ing must be scoped, not global).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

# ``generate_creature_images.py`` runs as ``python scripts/generate_creature_images.py``
# and uses a bare ``from render_common import ...``; put scripts/ on sys.path and
# import by bare module name — same shim as tests/scripts/test_generate_music.py.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from generate_creature_images import collect_creatures, compose_prompt  # noqa: E402
from render_common import GENRE_PACKS_DIR, load_visual_style  # noqa: E402

pytestmark = pytest.mark.skipif(
    not GENRE_PACKS_DIR.is_dir(), reason="sidequest-content not on disk"
)


def _collect_world(genre: str, world: str) -> dict[str, dict]:
    """Run the REAL collector over a genre pack, keyed by id for one world."""
    genre_dir = GENRE_PACKS_DIR / genre
    return {
        c["id"]: c
        for c in collect_creatures(genre_dir)
        if c.get("world") == world
    }


def _compose(genre: str, creature: dict) -> tuple[str, str, int]:
    vs = load_visual_style(GENRE_PACKS_DIR / genre, tier="portrait")
    return compose_prompt(creature, vs)


def _bestiary_name(genre: str, world: str, cid: str) -> str:
    path = GENRE_PACKS_DIR / genre / "worlds" / world / "bestiary.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    for e in data.get("entries", []):
        if isinstance(e, dict) and e.get("id") == cid:
            return e["name"]
    raise AssertionError(f"{genre}/{world} bestiary has no entry {cid!r}")


def _creatures_yaml_name(genre: str, world: str, cid: str) -> str:
    path = GENRE_PACKS_DIR / genre / "worlds" / world / "creatures.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    for c in data.get("creatures", []):
        if isinstance(c, dict) and c.get("id") == cid:
            return c["name"]
    raise AssertionError(f"{genre}/{world} creatures.yaml has no override {cid!r}")


# ── AC4 + AC1: manifest-less WN world derives creatures from bestiary ──────


def test_manifestless_wn_world_derives_creatures_from_bestiary() -> None:
    """coyote_star ships bestiary.yaml but NO creatures.yaml. Under the old
    creatures.yaml-only collector it yields ZERO renderable creatures (RED);
    under the derived-source model every bestiary entry is a renderable
    creature carrying the fields compose_prompt needs."""
    collected = _collect_world("space_opera", "coyote_star")
    assert collected, (
        "coyote_star (bestiary-only, no creatures.yaml) collected NO creatures — "
        "creature portraits still don't scale past the 2 hand-authored worlds"
    )
    for cid, c in collected.items():
        assert (c.get("description") or "").strip(), (
            f"{cid}: derived creature has empty description (nothing to render from)"
        )
        assert isinstance(c.get("threat_level"), int), f"{cid}: threat_level not int"
        assert c.get("id"), f"{cid}: derived creature missing id"
        assert isinstance(c.get("tags"), list), f"{cid}: tags not a list"


def test_derived_creatures_compose_nonempty_prompts() -> None:
    """AC4: a derived creature resolves to a real render prompt (non-empty
    subject AND clip), proving the whole render path is reachable from the
    bestiary alone."""
    collected = _collect_world("space_opera", "coyote_star")
    assert collected, "precondition: coyote_star derives creatures"
    dock = collected.get("dock_tough")
    assert dock is not None, "coyote_star bestiary entry 'dock_tough' not derived"
    subject, clip, seed = _compose("space_opera", dock)
    assert subject.strip(), "derived creature composed an EMPTY subject prompt"
    assert clip.strip(), "derived creature composed an EMPTY clip prompt"
    assert isinstance(seed, int)


def test_threat_level_derived_from_bestiary_level() -> None:
    """AC1: threat_level derives from the bestiary ``level`` (level->threat map).
    A level-1 mook floors to threat 1; a level-8 entry outranks it. Positive
    int, order-preserving — asserted without pinning the exact map formula."""
    collected = _collect_world("space_opera", "coyote_star")
    dock = collected.get("dock_tough")  # level 1
    apex = collected.get("apex_predator")  # level 8
    assert dock is not None and apex is not None, (
        "coyote_star anchors dock_tough (L1) / apex_predator (L8) not derived"
    )
    assert all(
        isinstance(c["threat_level"], int) and c["threat_level"] >= 1
        for c in collected.values()
    ), "every derived threat_level must be a positive int"
    assert dock["threat_level"] == 1, (
        f"level-1 bestiary entry should floor to threat_level 1, got "
        f"{dock['threat_level']}"
    )
    assert apex["threat_level"] > dock["threat_level"], (
        "threat_level must rise with bestiary level (a level-8 entry outranks a "
        f"level-1 mook) — got apex={apex['threat_level']} dock={dock['threat_level']}"
    )


# ── AC1: creatures.yaml override wins per-field; bestiary-only ids derive ──


def test_bestiary_merge_keeps_override_and_adds_bestiary_only_ids() -> None:
    """beneath_sunden ships BOTH a bestiary (48+ low entries) and a 7-capstone
    creatures.yaml naming override. The merge must (a) surface a bestiary-ONLY
    low id (``constrictor_snake``, no creatures.yaml entry) AND (b) keep the
    creatures.yaml override name for a SHARED id (``lich``), never falling back
    to the bestiary proper noun. Old collector: constrictor_snake is absent."""
    collected = _collect_world("caverns_and_claudes", "beneath_sunden")

    # (a) bestiary-only low id is now renderable
    assert "constrictor_snake" in collected, (
        "beneath_sunden bestiary-only low id 'constrictor_snake' not collected — "
        "bestiary derivation is not wired (creatures.yaml is not the only source)"
    )

    # (b) shared id keeps the creatures.yaml override name, NOT the bestiary name
    lich = collected.get("lich")
    assert lich is not None, "shared id 'lich' missing after merge"
    override_name = _creatures_yaml_name("caverns_and_claudes", "beneath_sunden", "lich")
    bestiary_name = _bestiary_name("caverns_and_claudes", "beneath_sunden", "lich")
    assert lich["name"] == override_name, (
        f"creatures.yaml override name lost in merge: got {lich['name']!r}, "
        f"expected override {override_name!r} — the per-world override must win "
        "per-field over the bestiary entry"
    )
    assert lich["name"] != bestiary_name, (
        f"merged name is the bestiary proper noun {bestiary_name!r} — the override "
        "did not take precedence"
    )


# ── AC2: secret-name world suppresses proper nouns; scoping is not global ──


def test_secret_name_world_derived_clip_has_no_bestiary_proper_noun() -> None:
    """AC2: beneath_sunden's conceit is 'nothing is named'. A bestiary-derived
    low creature (``constrictor_snake``, bestiary name 'Constrictor Snake') must
    NOT put that proper noun in the CLIP prompt — Z-Image paints CLIP nouns, so
    this world would otherwise caption 'Constrictor Snake'."""
    collected = _collect_world("caverns_and_claudes", "beneath_sunden")
    snake = collected.get("constrictor_snake")
    assert snake is not None, (
        "constrictor_snake not derived (see the bestiary-merge test)"
    )
    bestiary_name = _bestiary_name(
        "caverns_and_claudes", "beneath_sunden", "constrictor_snake"
    )
    _subject, clip, _seed = _compose("caverns_and_claudes", snake)
    assert bestiary_name.lower() not in clip.lower(), (
        f"derived CLIP paints the bestiary proper noun {bestiary_name!r}: "
        f"{clip!r} — a 'nothing is named' world must suppress or rewrite the "
        "derived name before it reaches the CLIP prompt"
    )


def test_named_world_keeps_creature_name_in_clip() -> None:
    """AC2 guard: de-proper-noun'ing must be SCOPED to secret-name worlds. A
    normal world (coyote_star) keeps its creature name in the CLIP — a global
    strip would gut every other world's prompts."""
    collected = _collect_world("space_opera", "coyote_star")
    dock = collected.get("dock_tough")
    assert dock is not None, "dock_tough not derived (see the derivation test)"
    _subject, clip, _seed = _compose("space_opera", dock)
    assert "dock tough" in clip.lower(), (
        f"coyote_star (not a secret-name world) dropped the creature name from "
        f"CLIP {clip!r} — de-proper-noun'ing must be scoped, not global"
    )
