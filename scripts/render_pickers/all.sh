#!/usr/bin/env bash
# Render new pickers for ALL expanded worlds, in sequence. Run at leisure.
# Each per-world script is idempotent (only new faces render), so re-running is safe.
set -euo pipefail
here="$(dirname "$0")"
for s in "$here"/*__*.sh; do
  echo "=== $s ==="
  "$s"
done
