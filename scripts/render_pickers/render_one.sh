#!/usr/bin/env bash
# Render only the NEW picker portraits for one world, sync them to R2, rebuild the manifest.
#
# Usage: scripts/render_pickers/render_one.sh <genre> <world>
#
# A non-`--force` render skips images already on R2, so this renders exactly the
# newly-authored picker faces and nothing else. Re-running a world that is already
# fully rendered is a clean no-op. REQUIRES the media daemon to be warm.
set -euo pipefail

GENRE="${1:?usage: render_one.sh <genre> <world>}"
WORLD="${2:?usage: render_one.sh <genre> <world>}"
ROOT="/Users/slabgorb/Projects/oq-2"
PORTRAITS_DIR="$ROOT/sidequest-content/genre_packs/$GENRE/worlds/$WORLD/assets/portraits"

cd "$ROOT"
mkdir -p "$PORTRAITS_DIR"

# Snapshot the local portraits dir before rendering so we can isolate the new PNGs.
before="$(cd "$PORTRAITS_DIR" && ls -1 2>/dev/null | sort || true)"

# Non-force run: images already on R2 are skipped; only new pickers render.
# ALWAYS `uv run python` (never bare python3) — these scripts import boto3 from the
# orchestrator uv env; bare python3 fails on a non-force run.
uv run python scripts/generate_portrait_images.py --genre "$GENRE" --world "$WORLD"

after="$(cd "$PORTRAITS_DIR" && ls -1 2>/dev/null | sort || true)"
new="$(comm -13 <(printf '%s\n' "$before") <(printf '%s\n' "$after") | grep -E '\.png$' || true)"

if [ -z "$new" ]; then
  echo "[render_pickers] no new portraits for $GENRE/$WORLD (already on R2)"
  exit 0
fi

echo "[render_pickers] new portraits for $GENRE/$WORLD:"
printf '  %s\n' $new

# Absolute paths for the R2 sync.
files=""
for n in $new; do files="$files $PORTRAITS_DIR/$n"; done
uv run python scripts/r2_sync_packs.py --files $files

# Rebuild the committed manifest index from a live bucket scan.
uv run python scripts/r2_manifest_from_bucket.py

echo "[render_pickers] done: $GENRE/$WORLD ($(printf '%s\n' $new | wc -l | tr -d ' ') new)"
