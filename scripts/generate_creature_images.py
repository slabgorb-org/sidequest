#!/usr/bin/env python3
"""Batch-generate creature/monster images from the bestiary.

Story 158-52 (ADR-155): ``bestiary.yaml`` is the single source of truth for
creature-image production — the runtime roster the encountergen samples is
what gets plates. Each entry derives a render item (threat_level <- level);
a world's ``creatures.yaml`` is an OPTIONAL per-field override manifest
(naming conceits via top-level ``name_is_secret: true``, bespoke marquee
plates), not a precondition.

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
import math
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

# The render fields a creatures.yaml override may replace per-field
# (ADR-121 flavor): fields the override declares win; omitted fields fall
# through to the bestiary-derived value.
_RENDER_FIELDS = ("name", "description", "threat_level", "tags")


def derive_threat_level(level: int) -> int:
    """Map a bestiary ``level`` (== HD on the SRD convention) onto the
    framing-band threat ladder compose_prompt keys off (>=4 full page,
    >=3 half, >=2 quarter, else spot): levels 1-2 spot, 3-4 quarter,
    5-6 half, 7+ full page — trivial, monotone, matches the low/mid/deep
    band tagging."""
    return max(1, math.ceil(level / 2))


def _world_key(path: Path, genre_dir: Path) -> str:
    rel = path.relative_to(genre_dir)
    return (
        rel.parts[1]
        if len(rel.parts) > 2 and rel.parts[0] == "worlds"
        else "default"
    )


def _derive_render_item(
    entry: dict, genre_name: str, world: str, name_is_secret: bool
) -> dict | None:
    """Derive one render item from a bestiary entry, or loud-skip to None.

    A skip is always logged with the id and reason (ADR-124 loud-skip fold)
    — never a silent drop, never a batch-killing crash.
    """
    eid = entry["id"]
    description = (entry.get("description") or "").strip()
    if not description:
        log.warning(
            "SKIP %s/%s/%s: bestiary entry has no description — no render subject",
            genre_name,
            world,
            eid,
        )
        return None
    level = entry.get("level")
    if not isinstance(level, int):
        log.warning(
            "SKIP %s/%s/%s: bestiary entry has no integer level — cannot derive threat_level",
            genre_name,
            world,
            eid,
        )
        return None

    name = entry.get("name", "unknown")
    if name_is_secret:
        # "Nothing is named" conceit: Z-Image paints proper nouns from
        # subject AND clip, so the roster name never reaches the prompt.
        # The SRD `role` line is already non-proper descriptive prose.
        role = (entry.get("role") or "").strip()
        if not role:
            log.warning(
                "SKIP %s/%s/%s: name_is_secret world but entry has no `role` "
                "to de-proper-noun the render name",
                genre_name,
                world,
                eid,
            )
            return None
        name = role

    return {
        "genre": genre_name,
        "world": world,
        "name": name,
        "id": eid,
        "description": description,
        "threat_level": derive_threat_level(level),
        "tags": entry.get("tags", []),
    }


def collect_creatures(genre_dir: Path) -> list[dict]:
    """Collect render items: bestiary.yaml derives, creatures.yaml overrides.

    Walks every ``bestiary.yaml`` (top-level ``entries:``) and
    ``creatures.yaml`` (top-level ``creatures:``) under the genre dir, keyed
    per world (genre-root files map to world ``"default"``). Bestiary entries
    derive render items; a creatures.yaml entry with the same id overrides
    per-field; creatures.yaml-only entries pass through verbatim (bespoke
    plates). One item per (world, id).
    """
    genre_name = genre_dir.name

    bestiary_order: dict[str, list[dict]] = {}
    for path in sorted(genre_dir.rglob("bestiary.yaml")):
        data = load_yaml(path)
        entries = data.get("entries") or [] if isinstance(data, dict) else []
        world_entries = bestiary_order.setdefault(_world_key(path, genre_dir), [])
        world_entries.extend(
            e for e in entries if isinstance(e, dict) and e.get("id")
        )

    manifests: dict[str, tuple[list[dict], bool]] = {}
    for path in sorted(genre_dir.rglob("creatures.yaml")):
        data = load_yaml(path)
        if isinstance(data, list):
            manifests[_world_key(path, genre_dir)] = (data, False)
        else:
            manifests[_world_key(path, genre_dir)] = (
                data.get("creatures") or [],
                data.get("name_is_secret") is True,
            )

    creatures: list[dict] = []
    for world in sorted(set(bestiary_order) | set(manifests)):
        override_list, name_is_secret = manifests.get(world, ([], False))
        overrides = {
            c["id"]: c for c in override_list if isinstance(c, dict) and c.get("id")
        }
        derived_ids: set[str] = set()

        for entry in bestiary_order.get(world, []):
            item = _derive_render_item(entry, genre_name, world, name_is_secret)
            if item is None:
                continue
            override = overrides.get(entry["id"])
            if override is not None:
                for field in _RENDER_FIELDS:
                    if field in override:
                        item[field] = override[field]
            derived_ids.add(entry["id"])
            creatures.append(item)

        # Bespoke plates: override entries with no bestiary id (or whose
        # bestiary entry was loud-skipped) keep the legacy pass-through shape.
        for creature in override_list:
            if not isinstance(creature, dict):
                continue
            if creature.get("id") in derived_ids:
                continue
            creatures.append(
                {
                    "genre": genre_name,
                    "world": world,
                    "name": creature.get("name", "unknown"),
                    "id": creature.get("id", "unknown"),
                    "description": creature.get("description", ""),
                    "threat_level": creature.get("threat_level", 1),
                    "tags": creature.get("tags", []),
                }
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
        creatures = collect_creatures(genre_dir)
        if args.world:
            creatures = [c for c in creatures if c.get("world") == args.world]
        # World-merged style per item: a world-level positive_suffix REPLACES
        # the genre suffix (beneath_sunden's carries the no-text/no-caption
        # clause), so genre-level-only loading would strip a conceit world's
        # caption protection. One load per world, cached.
        styles: dict[str, dict] = {}
        for c in creatures:
            world = c.get("world", "default")
            if world not in styles:
                styles[world] = load_visual_style(
                    genre_dir,
                    "" if world == "default" else world,
                    tier="portrait",
                )
            c["_visual_style"] = styles[world]
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
