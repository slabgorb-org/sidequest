#!/usr/bin/env bash
# Transfer all SideQuest repos from personal account (slabgorb) to the org
# (slabgorb-org), then repoint local remotes and verify.
#
# Prereqs: gh authed as slabgorb with 'repo' scope; admin on slabgorb-org.
# Run from the orchestrator root:  ./scripts/transfer_to_org.sh
set -euo pipefail

SRC_OWNER="slabgorb"
DST_OWNER="slabgorb-org"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# repo-dir : github-repo-name
declare -A REPOS=(
  ["."]="sidequest"
  ["sidequest-ui"]="sidequest-ui"
  ["sidequest-content"]="sidequest-content"
  ["sidequest-daemon"]="sidequest-daemon"
  ["sidequest-server"]="sidequest-server"
  ["sidequest-composer"]="sidequest-composer"
  ["sidequest-understudy"]="sidequest-understudy"
)

echo "==> Step 1/3: transfer ownership ${SRC_OWNER} -> ${DST_OWNER}"
for name in "${REPOS[@]}"; do
  printf '  %-22s ' "$name"
  if gh api -X POST "repos/${SRC_OWNER}/${name}/transfer" \
        -f new_owner="${DST_OWNER}" >/tmp/xfer_$$.json 2>&1; then
    echo "transfer accepted"
  else
    msg=$(python3 -c "import json,sys;print(json.load(open('/tmp/xfer_$$.json')).get('message','?'))" 2>/dev/null || cat /tmp/xfer_$$.json)
    # already moved is not fatal — keep going
    echo "skip/err: ${msg}"
  fi
done
rm -f /tmp/xfer_$$.json

echo "==> waiting 5s for transfers to settle..."
sleep 5

echo "==> Step 2/3: repoint local remotes to ${DST_OWNER} (SSH)"
for dir in "${!REPOS[@]}"; do
  name="${REPOS[$dir]}"
  new_url="git@github.com:${DST_OWNER}/${name}.git"
  git -C "${ROOT}/${dir}" remote set-url origin "${new_url}"
  printf '  %-22s -> %s\n' "$dir" "$new_url"
done

echo "==> Step 3/3: verify each origin resolves"
for dir in "${!REPOS[@]}"; do
  printf '  %-22s ' "$dir"
  if git -C "${ROOT}/${dir}" ls-remote --heads origin >/dev/null 2>&1; then
    echo "OK"
  else
    echo "FETCH FAILED — check transfer/SSH access"
  fi
done

echo "==> done. Post-move checklist:"
echo "   - Migrate R2/Cloudflare tokens to org-level secrets"
echo "   - Re-apply branch protection (main/develop) as org rulesets"
echo "   - Confirm Actions billing now points at the org"
