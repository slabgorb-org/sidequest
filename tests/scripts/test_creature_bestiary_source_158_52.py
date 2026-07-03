"""Story 158-52 (RED) — creature portraits derive from bestiary.yaml.

DECISION (Keith, 2026-07-01): the bestiary is the single source of truth for
creature-image production; the render pipeline DERIVES the prompt from it.
``creatures.yaml`` is demoted to an OPTIONAL per-world override — load-bearing
only where a world overrides the derived name (naming conceits) or wants a
bespoke marquee plate. Today ``collect_creatures`` hard-rglobs
``creatures.yaml`` and never reads ``bestiary.yaml``, so portraits exist for
only 2 of 22 WN-bound worlds.

Contract pinned by these tests (Dev implements to this):

1. ``collect_creatures(genre_dir)`` reads BOTH ``bestiary.yaml`` (top-level
   ``entries:``) and ``creatures.yaml`` (top-level ``creatures:``), per world.
   Genre-root files map to world ``"default"``, mirroring the existing
   creatures.yaml behavior.
2. Each bestiary entry derives ``{id, name, description, tags}`` verbatim and
   ``threat_level`` from ``level``: an int >= 1, monotone non-decreasing in
   level, with level 1 landing in the spot/quarter framing band (<= 2) and
   level >= 8 landing in the full-page band (>= 4). The exact map is Dev's
   choice inside those bounds (identity satisfies them).
3. Where a world's ``creatures.yaml`` carries an entry for the same id, the
   override wins PER-FIELD (ADR-121 flavor): fields the override declares
   replace the derived ones; fields it omits fall through to the bestiary.
   One collected creature per (world, id) — never a duplicate.
4. A ``creatures.yaml`` entry whose id has no bestiary match is still
   collected verbatim (bespoke plate back-compat — the two hand-authored
   worlds keep working).
5. A top-level ``name_is_secret: true`` in a world's ``creatures.yaml``
   declares the "nothing is named" conceit: every bestiary-DERIVED name must
   be de-proper-noun'd (the collected name is not the bestiary ``name``, and
   the composed CLIP prompt never contains it). Z-Image paints proper nouns
   from subject AND clip. A per-id override name still wins under the flag.
6. A bestiary entry with an empty/missing ``description`` is not renderable:
   it is excluded from collection WITH a logged warning (loud-skip, the
   ADR-124 fold pattern — never a silent fallback, never a crash that takes
   the whole batch down).

Integration tests at the bottom run against the real content tree and are
skipped when ``sidequest-content`` is not on disk (mirrors
``sidequest-server/tests/genre/test_beneath_sunden_creature_images_107_2.py``).
"""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
sys.path.insert(0, str(_SCRIPTS_DIR))

from generate_creature_images import collect_creatures, compose_prompt  # noqa: E402
from render_common import GENRE_PACKS_DIR  # noqa: E402


# ---------------------------------------------------------------------------
# Synthetic-content helpers
# ---------------------------------------------------------------------------


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _bestiary_entry(
    eid: str,
    name: str,
    level: int,
    description: str = "a pale thing that watches from the seam of the dark",
    role: str = "starveling shaft vermin",
    tags: list[str] | None = None,
) -> dict:
    return {
        "id": eid,
        "name": name,
        "level": level,
        "hp": level * 4,
        "armor_class": 12,
        "attack_bonus": level,
        "damage": "1d6",
        "morale": 7,
        "save": 15,
        "role": role,
        "tags": tags if tags is not None else ["beast", "low"],
        "description": description,
    }


def _make_world(
    genre_dir: Path,
    world: str,
    bestiary_entries: list[dict] | None = None,
    creatures: list[dict] | None = None,
    name_is_secret: bool = False,
) -> None:
    world_dir = genre_dir / "worlds" / world
    if bestiary_entries is not None:
        _write_yaml(world_dir / "bestiary.yaml", {"entries": bestiary_entries})
    if creatures is not None or name_is_secret:
        payload: dict = {"creatures": creatures or []}
        if name_is_secret:
            payload["name_is_secret"] = True
        _write_yaml(world_dir / "creatures.yaml", payload)


@pytest.fixture()
def genre_dir(tmp_path: Path) -> Path:
    d = tmp_path / "testgenre"
    d.mkdir()
    return d


def _by_id(creatures: list[dict], world: str | None = None) -> dict[str, dict]:
    picked = [c for c in creatures if world is None or c.get("world") == world]
    return {c["id"]: c for c in picked}


# ---------------------------------------------------------------------------
# Contract 1 + 2 — bestiary alone is a render source, fields derive
# ---------------------------------------------------------------------------


def test_bestiary_only_world_is_collected(genre_dir: Path) -> None:
    """A world shipping ONLY bestiary.yaml yields renderable creatures."""
    _make_world(
        genre_dir,
        "hollow",
        bestiary_entries=[
            _bestiary_entry("mine_rat", "Mine Rat", 1, description="a blind rat"),
            _bestiary_entry("pit_wight", "Pit Wight", 3, description="a dry husk"),
        ],
    )
    got = _by_id(collect_creatures(genre_dir), world="hollow")
    assert set(got) == {"mine_rat", "pit_wight"}, (
        "bestiary.yaml entries must be collected as render sources "
        f"(got ids: {sorted(got)})"
    )
    rat = got["mine_rat"]
    assert rat["name"] == "Mine Rat"
    assert rat["description"] == "a blind rat"
    assert rat["tags"] == ["beast", "low"]
    assert rat["genre"] == "testgenre"
    assert rat["world"] == "hollow"


def test_genre_root_bestiary_maps_to_default_world(genre_dir: Path) -> None:
    """Genre-level bestiary.yaml (neon_dystopia/mutant_wasteland ship one)
    collects under world='default', mirroring creatures.yaml behavior."""
    _write_yaml(
        genre_dir / "bestiary.yaml",
        {"entries": [_bestiary_entry("street_dog", "Street Dog", 1)]},
    )
    got = _by_id(collect_creatures(genre_dir))
    assert "street_dog" in got
    assert got["street_dog"]["world"] == "default"


def test_threat_level_derives_from_level_within_framing_bands(
    genre_dir: Path,
) -> None:
    """threat_level <- level: int >= 1, monotone, level 1 in the spot/quarter
    band (<= 2), level >= 8 in the full-page band (>= 4). compose_prompt's
    framing ladder keys off threat >= 4 / >= 3 / >= 2."""
    levels = [1, 2, 3, 5, 8]
    _make_world(
        genre_dir,
        "hollow",
        bestiary_entries=[
            _bestiary_entry(f"critter_{lv}", f"Critter {lv}", lv) for lv in levels
        ],
    )
    got = _by_id(collect_creatures(genre_dir), world="hollow")
    threats = []
    for lv in levels:
        t = got[f"critter_{lv}"]["threat_level"]
        assert isinstance(t, int) and t >= 1, (
            f"level {lv}: derived threat_level must be an int >= 1, got {t!r}"
        )
        threats.append(t)
    assert threats == sorted(threats), (
        f"threat_level must be monotone non-decreasing in level: {threats}"
    )
    assert threats[0] <= 2, f"level 1 must land in the spot/quarter band, got {threats[0]}"
    assert threats[-1] >= 4, f"level 8 must land in the full-page band, got {threats[-1]}"


def test_high_level_entry_gets_full_page_framing(genre_dir: Path) -> None:
    """End-to-end through compose_prompt: a deep capstone derives a subject
    with the full-page framing clause."""
    _make_world(
        genre_dir,
        "hollow",
        bestiary_entries=[
            _bestiary_entry("old_lich", "The Lich of the Stair", 9, tags=["undead", "deep"])
        ],
    )
    got = _by_id(collect_creatures(genre_dir), world="hollow")
    subject, clip, seed = compose_prompt(got["old_lich"], {"base_seed": 42})
    assert "full page illustration" in subject
    assert isinstance(seed, int)


# ---------------------------------------------------------------------------
# Contract 3 + 4 — creatures.yaml is a per-field override, not a precondition
# ---------------------------------------------------------------------------


def test_creatures_yaml_name_override_wins_per_field(genre_dir: Path) -> None:
    """An override declaring only `name` replaces the name and inherits the
    bestiary description — the naming-only override the conceit worlds keep."""
    _make_world(
        genre_dir,
        "hollow",
        bestiary_entries=[
            _bestiary_entry(
                "gnaw_swarm", "Gnaw-Swarm", 1, description="blind hairless mine-rats"
            )
        ],
        creatures=[{"id": "gnaw_swarm", "name": "a boiling carpet of blind vermin"}],
    )
    collected = collect_creatures(genre_dir)
    got = _by_id(collected, world="hollow")
    assert list(got) == ["gnaw_swarm"], (
        "same id in bestiary + creatures.yaml must collect exactly ONCE "
        f"(got {[c['id'] for c in collected]})"
    )
    merged = got["gnaw_swarm"]
    assert merged["name"] == "a boiling carpet of blind vermin", "override name wins"
    assert merged["description"] == "blind hairless mine-rats", (
        "field omitted by the override falls through to the bestiary"
    )


def test_creatures_yaml_description_override_keeps_derived_name(
    genre_dir: Path,
) -> None:
    """The symmetric per-field case: a bespoke plate description with no name
    keeps the bestiary-derived name."""
    _make_world(
        genre_dir,
        "hollow",
        bestiary_entries=[
            _bestiary_entry("pit_wight", "Pit Wight", 3, description="a dry husk")
        ],
        creatures=[{"id": "pit_wight", "description": "a husk crowned in salt"}],
    )
    got = _by_id(collect_creatures(genre_dir), world="hollow")
    merged = got["pit_wight"]
    assert merged["description"] == "a husk crowned in salt"
    assert merged["name"] == "Pit Wight"


def test_creatures_yaml_only_entry_is_still_collected(genre_dir: Path) -> None:
    """A bespoke plate with no bestiary id keeps rendering (back-compat for the
    two hand-authored worlds)."""
    _make_world(
        genre_dir,
        "hollow",
        bestiary_entries=[_bestiary_entry("mine_rat", "Mine Rat", 1)],
        creatures=[
            {
                "id": "the_unlisted",
                "name": "a shape the roster never counted",
                "description": "a marquee bespoke plate",
                "threat_level": 4,
                "tags": ["marquee"],
            }
        ],
    )
    got = _by_id(collect_creatures(genre_dir), world="hollow")
    assert "the_unlisted" in got, "creatures.yaml-only entries must survive the demotion"
    assert got["the_unlisted"]["description"] == "a marquee bespoke plate"


# ---------------------------------------------------------------------------
# Contract 5 — the naming conceit (name_is_secret)
# ---------------------------------------------------------------------------


def test_name_is_secret_world_never_derives_the_proper_noun(genre_dir: Path) -> None:
    """Top-level `name_is_secret: true` in creatures.yaml de-proper-nouns every
    bestiary-derived name: the collected name is not the roster name and the
    CLIP prompt never carries it (Z-Image would paint it as a caption)."""
    _make_world(
        genre_dir,
        "sunless",
        bestiary_entries=[
            _bestiary_entry(
                "giant_rat", "Giant Rat", 1, role="starveling mine vermin"
            )
        ],
        name_is_secret=True,
    )
    got = _by_id(collect_creatures(genre_dir), world="sunless")
    assert "giant_rat" in got, "the flag must not drop the entry — only rename it"
    creature = got["giant_rat"]
    assert creature["name"] != "Giant Rat", (
        "name_is_secret world derived the bestiary proper noun as the render name"
    )
    assert creature["name"].strip(), "de-proper-noun'd name must still be non-empty"
    _, clip, _ = compose_prompt(creature, {"base_seed": 42})
    assert "giant rat" not in clip.lower(), (
        f"CLIP prompt leaks the roster name under name_is_secret: {clip!r}"
    )


def test_name_is_secret_per_id_override_still_wins(genre_dir: Path) -> None:
    """The flag sets the default; a bespoke naming override remains the
    strongest word (per-field merge is unchanged by the conceit)."""
    _make_world(
        genre_dir,
        "sunless",
        bestiary_entries=[_bestiary_entry("giant_bat", "Giant Bat", 1)],
        creatures=[{"id": "giant_bat", "name": "a leather hush overhead"}],
        name_is_secret=True,
    )
    got = _by_id(collect_creatures(genre_dir), world="sunless")
    assert got["giant_bat"]["name"] == "a leather hush overhead"


# ---------------------------------------------------------------------------
# Contract 6 — unrenderable bestiary entries loud-skip
# ---------------------------------------------------------------------------


def test_empty_description_bestiary_entry_loud_skips(
    genre_dir: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """No description -> no subject -> not renderable. The entry is excluded
    AND a warning names it — a loud skip (ADR-124 fold pattern), never a
    silent drop and never a batch-killing crash."""
    _make_world(
        genre_dir,
        "hollow",
        bestiary_entries=[
            _bestiary_entry("mute_thing", "Mute Thing", 2, description=""),
            _bestiary_entry("spoken_thing", "Spoken Thing", 2),
        ],
    )
    with caplog.at_level(logging.WARNING):
        got = _by_id(collect_creatures(genre_dir), world="hollow")
    assert "spoken_thing" in got, "renderable siblings must survive the skip"
    assert "mute_thing" not in got, (
        "an entry with no description has no render subject and must be excluded"
    )
    assert any("mute_thing" in rec.getMessage() for rec in caplog.records), (
        "the skip must be LOUD — a warning naming the skipped id "
        f"(got records: {[rec.getMessage() for rec in caplog.records]!r})"
    )


# ---------------------------------------------------------------------------
# Integration — real content tree (gated like the server genre tests)
# ---------------------------------------------------------------------------

pytestmark_content = pytest.mark.skipif(
    not GENRE_PACKS_DIR.is_dir(), reason="sidequest-content not on disk"
)


def _load_bestiary_low_names(world_dir: Path) -> dict[str, str]:
    data = yaml.safe_load(
        (world_dir / "bestiary.yaml").read_text(encoding="utf-8")
    )
    return {
        e["id"]: e["name"]
        for e in data["entries"]
        if "low" in (e.get("tags") or [])
    }


@pytestmark_content
def test_beneath_sunden_low_band_derives_with_no_proper_noun_clips() -> None:
    """AC2: the conceit world. Every low-tagged bestiary entry is collected
    (derived-source coverage — today 42 of 48 are missing because collection
    reads creatures.yaml only), and no composed CLIP carries the bestiary
    proper noun."""
    genre = GENRE_PACKS_DIR / "caverns_and_claudes"
    low_names = _load_bestiary_low_names(genre / "worlds" / "beneath_sunden")
    assert low_names, "precondition: bestiary tags its low band"

    collected = _by_id(collect_creatures(genre), world="beneath_sunden")
    missing = sorted(set(low_names) - set(collected))
    assert not missing, (
        f"{len(missing)} low-band bestiary entries not collected as render "
        f"sources (first 10: {missing[:10]}) — the bestiary is the single "
        "source of truth for creature-image production"
    )

    leaks = []
    for eid, proper in low_names.items():
        _, clip, _ = compose_prompt(collected[eid], {"base_seed": 42})
        if proper.lower() in clip.lower():
            leaks.append((eid, clip))
    assert not leaks, (
        "beneath_sunden ('nothing is named') CLIP prompts carry bestiary "
        f"proper nouns — Z-Image will paint them as captions: {leaks[:5]}"
    )


@pytestmark_content
def test_coyote_star_renders_from_bestiary_alone() -> None:
    """AC4 wiring: a previously manifest-less WN world produces non-empty
    creature prompts from bestiary alone — portraits scale past the 2
    hand-authored worlds."""
    genre = GENRE_PACKS_DIR / "space_opera"
    assert not (genre / "worlds" / "coyote_star" / "creatures.yaml").exists(), (
        "precondition drift: coyote_star grew a creatures.yaml — pick another "
        "manifest-less world for this wiring test"
    )
    collected = [
        c for c in collect_creatures(genre) if c.get("world") == "coyote_star"
    ]
    assert collected, (
        "coyote_star has a populated bestiary.yaml but yielded zero render "
        "items — bestiary is not wired as a creature source"
    )
    for creature in collected:
        subject, clip, seed = compose_prompt(creature, {"base_seed": 42})
        assert subject.strip(), f"{creature['id']}: empty render subject"
        assert clip.strip(), f"{creature['id']}: empty CLIP prompt"
        assert isinstance(seed, int)


def _run_dry_run_cli(*args: str) -> str:
    proc = subprocess.run(
        [sys.executable, str(_SCRIPTS_DIR / "generate_creature_images.py"), *args],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert proc.returncode == 0, (
        f"dry-run exited {proc.returncode}\nstdout: {proc.stdout[-800:]}\n"
        f"stderr: {proc.stderr[-800:]}"
    )
    return proc.stdout + proc.stderr


@pytestmark_content
def test_cli_dry_run_coyote_star_lists_bestiary_prompts() -> None:
    """AC4, through the real CLI entrypoint: the render dry-run for a
    manifest-less world lists prompts instead of 'No items found!'."""
    out = _run_dry_run_cli(
        "--genre", "space_opera", "--world", "coyote_star", "--dry-run"
    )
    assert "No items found" not in out, (
        "the CLI still sees zero renderable creatures for coyote_star"
    )
    assert "CLIP prompt:" in out, "dry-run printed no composed prompt blocks"


@pytestmark_content
def test_cli_dry_run_beneath_sunden_layers_world_suffix() -> None:
    """The no-text/no-caption clause lives in the WORLD visual_style
    positive_suffix (which REPLACES the genre suffix for this world). The
    derived pipeline must therefore layer world-level style — pinned via the
    world suffix's distinctive 'crushing black' phrase in the dry-run output."""
    out = _run_dry_run_cli(
        "--genre", "caverns_and_claudes", "--world", "beneath_sunden", "--dry-run"
    )
    assert "crushing black" in out, (
        "dry-run output never shows the beneath_sunden world suffix — the "
        "pipeline is still rendering with genre-level style only, so the "
        "world's no-text/no-caption clause never reaches the prompt"
    )
