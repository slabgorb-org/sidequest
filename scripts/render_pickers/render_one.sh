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

# Preflight: the running daemon must serve the SAME content root this script
# renders from. If it serves a different checkout (e.g. oq-1 vs oq-2), its
# CharacterCatalog loads a manifest WITHOUT the newly-authored pickers and every
# new face dies with a per-entry `CatalogMissError`. Fail loud on mismatch rather
# than let that scroll by (No Silent Fallbacks).
EXPECTED_PACKS="$ROOT/sidequest-content/genre_packs"
SOCK="/tmp/sidequest-renderer.sock"
DPID="$(lsof "$SOCK" 2>/dev/null | awk 'NR==2{print $2}')"
if [ -z "${DPID:-}" ]; then
  echo "[render_pickers] WARNING: no daemon on $SOCK — start it with 'just daemon' (from the oq workspace whose content you're rendering)." >&2
else
  DPACKS="$(ps eww "$DPID" 2>/dev/null | tr ' ' '\n' | sed -n 's/^SIDEQUEST_GENRE_PACKS=//p' | head -1)"
  if [ -z "${DPACKS:-}" ]; then
    echo "[render_pickers] WARNING: could not read the daemon's SIDEQUEST_GENRE_PACKS (pid $DPID) — cannot confirm it serves $EXPECTED_PACKS. If you see CatalogMissError, that mismatch is why." >&2
  elif [ "$DPACKS" != "$EXPECTED_PACKS" ]; then
    echo "[render_pickers] FATAL: daemon (pid $DPID) serves content from:" >&2
    echo "                     $DPACKS" >&2
    echo "                   but this script renders pickers from:" >&2
    echo "                     $EXPECTED_PACKS" >&2
    echo "                   The daemon's CharacterCatalog will MISS the new pickers." >&2
    echo "                   Fix: restart the daemon with SIDEQUEST_GENRE_PACKS=$EXPECTED_PACKS," >&2
    echo "                   or run this script from the workspace the daemon already serves." >&2
    exit 2
  fi
fi

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
