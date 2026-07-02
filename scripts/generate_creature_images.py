#!/usr/bin/env python3
"""Batch-generate creature/monster images from creatures.yaml files.

Usage:
    python scripts/generate_creature_images.py                           # all genres
    python scripts/generate_creature_images.py --genre caverns_and_claudes
    python scripts/generate_creature_images.py --genre caverns_and_claudes --dry-run
    python scripts/generate_creature_images.py --force                    # regenerate existing
"""

from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path

from render_common import (
    GENRE_PACKS_DIR,
    TOKEN_LIMIT,
    deterministic_seed,
    load_visual_style,
    load_yaml,
    render_batch,
    truncate_to_tokens,
)

DEFAULT_STEPS = 20
log = logging.getLogger(__name__)


THREAT_LEVEL_CAP = 5


def _threat_from_level(level) -> int:
    """Trivial ``level -> threat_level`` map (Story 158-52).

    The bestiary carries an SRD ``level`` (HD); compose_prompt frames on a 1..5
    threat band (>=4 full-page … 1 spot vignette). Clamp the level into that
    band: a level-1 mook floors to threat 1, a high-HD capstone caps at 5. This
    is the only transform the bestiary roster needs to become a render roster.
    """
    try:
        lvl = int(level)
    except (TypeError, ValueError):
        lvl = 1
    return max(1, min(THREAT_LEVEL_CAP, lvl))


def _world_from_rel(rel: Path) -> str:
    """Derive the world slug from a genre-relative pack path.

    ``worlds/<slug>/<file>`` → ``<slug>``; a genre-root file → ``default``.
    """
    parts = rel.parts
    return parts[1] if len(parts) > 2 and parts[0] == "worlds" else "default"


def _derive_from_bestiary(
    genre_name: str, world: str, entry: dict, name_is_secret: bool
) -> dict:
    """Build a render creature from one bestiary entry (Story 158-52).

    The bestiary is the single source of truth: ``id``/``name``/``description``/
    ``tags`` come straight across and ``threat_level`` derives from ``level``.
    ``name_is_secret`` propagates the world's "nothing is named" conceit so the
    raw bestiary proper noun is suppressed from the CLIP unless a creatures.yaml
    naming override replaces it (see ``compose_prompt``).
    """
    return {
        "genre": genre_name,
        "world": world,
        "id": entry["id"],
        "name": entry.get("name", "unknown"),
        "description": entry.get("description", ""),
        "threat_level": _threat_from_level(entry.get("level", 1)),
        "tags": entry.get("tags", []),
        "name_is_secret": name_is_secret,
    }


def _creature_from_manifest(genre_name: str, world: str, entry: dict) -> dict:
    """Build a render creature from a creatures.yaml entry with NO bestiary row.

    Legacy path: worlds whose creatures.yaml carries entries the bestiary does
    not. The manifest supplies its own (already-safe) name, so it never needs
    proper-noun suppression.
    """
    return {
        "genre": genre_name,
        "world": world,
        "id": entry.get("id", "unknown"),
        "name": entry.get("name", "unknown"),
        "description": entry.get("description", ""),
        "threat_level": entry.get("threat_level", 1),
        "tags": entry.get("tags", []),
        "name_is_secret": False,
    }


def _apply_override(base: dict, entry: dict) -> None:
    """Overlay a creatures.yaml entry onto a bestiary-derived creature.

    Per-field override (ADR-121 flavor): creatures.yaml wins for any field it
    declares. A ``name`` override supplies a safe descriptive phrase, so it also
    clears ``name_is_secret`` — the bespoke name is meant to reach the CLIP.
    """
    if "name" in entry:
        base["name"] = entry["name"]
        base["name_is_secret"] = False
    if "description" in entry:
        base["description"] = entry["description"]
    if "threat_level" in entry:
        base["threat_level"] = entry["threat_level"]
    if "tags" in entry:
        base["tags"] = entry["tags"]


def _collect_world_creatures(
    genre_name: str,
    world: str,
    bestiary_path: Path | None,
    creatures_path: Path | None,
) -> list[dict]:
    """Merge one world's bestiary (source of truth) with its creatures.yaml override."""
    overrides: dict[str, dict] = {}
    name_is_secret = False
    if creatures_path is not None:
        cdata = load_yaml(creatures_path)
        if isinstance(cdata, dict):
            # Render-only conceit flag: this world's names are secret, so a
            # bestiary-derived proper noun must not reach the CLIP. Lives in
            # creatures.yaml (a render manifest) because the server's Bestiary
            # model is extra="forbid" — no engine-code change (Story 158-52).
            name_is_secret = bool(cdata.get("name_is_secret", False))
            clist = cdata.get("creatures", []) or []
        else:
            clist = cdata or []
        for c in clist:
            if isinstance(c, dict) and c.get("id"):
                overrides[c["id"]] = c

    merged: dict[str, dict] = {}
    order: list[str] = []

    if bestiary_path is not None:
        bdata = load_yaml(bestiary_path)
        entries = bdata if isinstance(bdata, list) else (bdata.get("entries", []) or [])
        for e in entries:
            if not isinstance(e, dict) or not e.get("id"):
                continue
            merged[e["id"]] = _derive_from_bestiary(genre_name, world, e, name_is_secret)
            order.append(e["id"])

    for cid, c in overrides.items():
        base = merged.get(cid)
        if base is None:
            merged[cid] = _creature_from_manifest(genre_name, world, c)
            order.append(cid)
        else:
            _apply_override(base, c)

    return [merged[cid] for cid in order]


def collect_creatures(genre_dir: Path) -> list[dict]:
    """Collect render creatures for a genre, DERIVED from bestiary.yaml.

    Story 158-52: the ``bestiary.yaml`` roster (what encountergen samples on the
    Without-Number path) is the single source of truth for creature-image
    production. Each entry derives a render creature; a per-world
    ``creatures.yaml`` is an OPTIONAL per-field override (naming conceits +
    bespoke marquee plates), not a precondition. This is why portraits now scale
    past the two hand-authored worlds that shipped a creatures.yaml.
    """
    genre_name = genre_dir.name

    worlds: dict[str, dict[str, Path]] = {}
    for path in sorted(genre_dir.rglob("bestiary.yaml")):
        worlds.setdefault(_world_from_rel(path.relative_to(genre_dir)), {})[
            "bestiary"
        ] = path
    for path in sorted(genre_dir.rglob("creatures.yaml")):
        worlds.setdefault(_world_from_rel(path.relative_to(genre_dir)), {})[
            "creatures"
        ] = path

    creatures: list[dict] = []
    for world in sorted(worlds):
        paths = worlds[world]
        creatures.extend(
            _collect_world_creatures(
                genre_name, world, paths.get("bestiary"), paths.get("creatures")
            )
        )
    return creatures


def compose_prompt(creature: dict, visual_style: dict) -> tuple[str, str, int]:
    """Compose subject description, CLIP prompt, and seed.

    Returns the subject (not a pre-composed prompt). The daemon's PromptComposer
    handles style injection via art_style, visual_tag_overrides, and LoRA.
    """
    base_seed = visual_style.get("base_seed", 42)

    description = creature.get("description", "")
    name = creature.get("name", "unknown")
    threat = creature.get("threat_level", 1)

    # Scale framing by threat level
    if threat >= 4:
        framing = "full page illustration, dramatic composition, imposing scale"
    elif threat >= 3:
        framing = "half page illustration, menacing pose"
    elif threat >= 2:
        framing = "quarter page illustration, lurking posture"
    else:
        framing = "spot illustration, small creature vignette"

    subject = truncate_to_tokens(description, TOKEN_LIMIT - 100)
    subject = f"{subject}, {framing}"

    # Z-Image paints proper nouns from the CLIP. In a "nothing is named" world
    # (Story 158-52), a bestiary-derived name is a proper noun the plate must
    # not caption, so it is dropped from the CLIP. A creatures.yaml naming
    # override clears the flag (its name is a safe descriptive phrase), so
    # bespoke names still reach the CLIP.
    if creature.get("name_is_secret"):
        clip = "creature illustration"
    else:
        clip = f"{name}, creature illustration"

    seed = deterministic_seed(
        f"creature-{creature['genre']}-{creature['id']}", base_seed
    )

    return subject, clip, seed


def main():
    parser = argparse.ArgumentParser(
        description="Generate creature images from creatures.yaml"
    )
    parser.add_argument("--genre", help="Only process this genre")
    parser.add_argument("--world", help="Only process this world (requires --genre)")
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview prompts without rendering"
    )
    parser.add_argument(
        "--steps", type=int, default=DEFAULT_STEPS, help="Inference steps"
    )
    parser.add_argument(
        "--force", action="store_true", help="Regenerate existing images"
    )
    parser.add_argument(
        "--no-upload",
        action="store_true",
        help="Test render: keep PNGs local, do not upload to R2 or rebuild the manifest",
    )
    args = parser.parse_args()
    if args.world and not args.genre:
        parser.error("--world requires --genre")

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    genre_dirs = (
        sorted(GENRE_PACKS_DIR.iterdir())
        if not args.genre
        else [GENRE_PACKS_DIR / args.genre]
    )
    genre_dirs = [d for d in genre_dirs if d.is_dir() and (d / "pack.yaml").exists()]

    if not genre_dirs:
        log.error("No genre packs found (genre=%s)", args.genre)
        return

    all_creatures = []
    for genre_dir in genre_dirs:
        visual_style = load_visual_style(genre_dir, tier="portrait")
        creatures = collect_creatures(genre_dir)
        if args.world:
            creatures = [c for c in creatures if c.get("world") == args.world]
        for c in creatures:
            c["_visual_style"] = visual_style
        all_creatures.extend(creatures)

    asyncio.run(
        render_batch(
            all_creatures,
            compose_prompt,
            "portrait",
            "creatures",
            genre_filter=args.genre,
            dry_run=args.dry_run,
            steps=args.steps,
            force=args.force,
            upload=not args.no_upload,
        )
    )


if __name__ == "__main__":
    main()
