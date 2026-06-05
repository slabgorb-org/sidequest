#!/usr/bin/env python3
"""Pull objects from R2 down to the local content tree.

Counterpart to ``r2_sync_packs.py`` (which only uploads). Downloads every
object under a prefix into ``<content-root>/<key>`` so tools that read the
local tree (e.g. ``generate_image_sheets.py``) can see assets that were
rendered/uploaded on another machine and never landed on this clone's disk.

Per CLAUDE.md (No Silent Fallbacks): missing R2 creds raise rather than
silently no-op, and an empty listing is reported, not treated as success.

Usage:
    uv run --project . python scripts/r2_pull.py --prefix genre_packs/wry_whimsy/worlds/wonderland/assets/
    uv run --project . python scripts/r2_pull.py --prefix <prefix> --dry-run
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from scripts.r2_sync_packs import _build_client

_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONTENT_ROOT = _ROOT / "sidequest-content"


def pull(prefix: str, content_root: Path, bucket: str, dry_run: bool) -> int:
    client = _build_client()
    paginator = client.get_paginator("list_objects_v2")
    keys: list[str] = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            keys.append(obj["Key"])

    if not keys:
        raise SystemExit(
            f"R2 listing returned 0 objects under prefix {prefix!r} — refusing to "
            "treat an empty result as success."
        )

    print(f"Found {len(keys)} objects under {prefix!r} (bucket={bucket})")
    for key in sorted(keys):
        dest = content_root / key
        if dry_run:
            print(f"  [dry-run] {key} -> {dest}")
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        client.download_file(bucket, key, str(dest))
        print(f"  pulled {key}")
    return len(keys)


def main() -> None:
    parser = argparse.ArgumentParser(description="Pull objects from R2 to the local content tree")
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--bucket", default="sidequest")
    parser.add_argument("--content-root", type=Path, default=DEFAULT_CONTENT_ROOT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    count = pull(args.prefix, args.content_root, args.bucket, args.dry_run)
    print(f"Done! {count} objects {'listed' if args.dry_run else 'pulled'}.")


if __name__ == "__main__":
    sys.exit(main())
