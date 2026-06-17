#!/usr/bin/env python3
"""Lightweight doc-drift tripwire (epic-127 regression guard).

Scans the *canonical, agent-facing* doc set for a curated set of known-stale
patterns — the specific drifts epic-127 reconciled (Rust→Python, SQLite→Postgres,
TTS removal, native-ruleset vestigialisation, the Opus model generation, and pack
facts). It is a regression guard, not a semantic linter: each pattern is a
high-confidence stale claim with (essentially) zero legitimate live use, so a hit
means a doc has drifted back out of sync with reality.

Scope (canonical docs only):
  - README.md, JARGONFILE.md
  - docs/**/*.md            EXCEPT docs/adr/** and docs/superpowers/**
  - the six subrepo READMEs

Deliberately excluded — these are historical / process artifacts where stale
terms are *correct* (they record a point in time):
  - docs/adr/**                     decision records
  - docs/superpowers/**             specs, plans, dev notes (completed & superseded)

Per-line escape hatch: append ``<!-- drift-ok: <reason> -->`` to a line to suppress
it (use sparingly, for a genuinely-historical mention inside a canonical doc).

Usage:
    python scripts/check_doc_drift.py          # scan; exit 1 if any hit
    python scripts/check_doc_drift.py --list    # print the tripwire table
Exit code 0 = clean, 1 = drift found (or a configured doc is missing).

Add a pattern when you reconcile a class of drift, so it can't creep back.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Canonical doc roots to scan (relative to REPO_ROOT). Directories are walked
# recursively for *.md; files are scanned directly.
SCAN_ROOTS: list[str] = [
    "README.md",
    "JARGONFILE.md",
    "docs",
    "sidequest-server/README.md",
    "sidequest-ui/README.md",
    "sidequest-daemon/README.md",
    "sidequest-content/README.md",
    "sidequest-composer/README.md",
    "sidequest-understudy/README.md",
]

# Path fragments that mark a file/dir as a historical or process artifact where
# stale terms are correct. Matched against the POSIX path relative to REPO_ROOT.
EXCLUDE_FRAGMENTS: tuple[str, ...] = (
    "docs/adr/",
    "docs/superpowers/",
    "docs/doc-drift-check.md",  # this check's own doc — lists every pattern as an example
)

SUPPRESS_MARKER = "drift-ok"

# (id, regex, hint). Keep each pattern unambiguous-stale to avoid false positives.
TRIPWIRES: list[tuple[str, str, str]] = [
    ("opus-model-id", r"claude-opus-4-7", "Opus generation is 4.8 — use claude-opus-4-8 (ADR-101 routing)."),
    ("opus-version", r"Opus 4\.7\b", "Opus generation is 4.8 — say 'Opus 4.8'."),
    ("pack-count-prod", r"\b10 production packs\b", "There are 11 packs — update the count + list (add wry_whimsy)."),
    ("pack-count-all", r"\ball 10 packs\b", "There are 11 packs — update the count."),
    ("dead-rust-link", r"\]\(\.\./sidequest-api/", "Dead Rust crate link — repoint to the Python source (sidequest-server/sidequest/...)."),
    ("workshop-tree-path", r"genre_workshopping/[A-Za-z]", "genre_workshopping/ was retired 2026-06-03 — use genre_packs/."),
    ("hp-removed", r"No HP field on sheet", "ADR-114 reinstated ablative HP — HP is on the sheet (HpPool)."),
]

# Context-sensitive terms deliberately NOT auto-tripwired: `SqliteStore`, `TTS`,
# `native` (ruleset), `low_fantasy`. Each has *legitimate* "removed/retired/deleted"
# mentions in canonical docs, so a bare-term pattern would cry wolf and get ignored.
# Review these by hand when touching persistence / audio / ruleset / pack docs.


def _is_excluded(rel_posix: str) -> bool:
    return any(frag in rel_posix for frag in EXCLUDE_FRAGMENTS)


def _iter_docs() -> list[Path]:
    docs: list[Path] = []
    for root in SCAN_ROOTS:
        p = REPO_ROOT / root
        if p.is_dir():
            for md in sorted(p.rglob("*.md")):
                rel = md.relative_to(REPO_ROOT).as_posix()
                if not _is_excluded(rel):
                    docs.append(md)
        elif p.is_file():
            docs.append(p)
        # Missing configured files are reported by the caller, not here.
    return docs


def scan() -> list[tuple[str, int, str, str, str]]:
    """Return (rel_path, lineno, tripwire_id, hint, line) for each unsuppressed hit."""
    compiled = [(tid, re.compile(rx), hint) for tid, rx, hint in TRIPWIRES]
    hits: list[tuple[str, int, str, str, str]] = []
    for doc in _iter_docs():
        rel = doc.relative_to(REPO_ROOT).as_posix()
        try:
            text = doc.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if SUPPRESS_MARKER in line:
                continue
            for tid, rx, hint in compiled:
                if rx.search(line):
                    hits.append((rel, lineno, tid, hint, line.strip()))
    return hits


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true", help="print the tripwire table and exit")
    args = ap.parse_args()

    if args.list:
        print("Doc-drift tripwires:")
        for tid, rx, hint in TRIPWIRES:
            print(f"  {tid:20} /{rx}/\n  {' ' * 20} → {hint}")
        return 0

    # Report any configured top-level file that has gone missing (loud, per No Silent Fallbacks).
    missing = [r for r in SCAN_ROOTS if not (REPO_ROOT / r).exists()]
    if missing:
        print("doc-drift: configured doc path(s) missing — update SCAN_ROOTS:", file=sys.stderr)
        for m in missing:
            print(f"  - {m}", file=sys.stderr)
        return 1

    hits = scan()
    if not hits:
        print("doc-drift: clean — no stale-pattern hits in the canonical doc set.")
        return 0

    print(f"doc-drift: {len(hits)} stale-pattern hit(s) found:\n", file=sys.stderr)
    for rel, lineno, tid, hint, line in hits:
        print(f"  {rel}:{lineno}  [{tid}]", file=sys.stderr)
        print(f"      {line}", file=sys.stderr)
        print(f"      → {hint}", file=sys.stderr)
    print(
        "\nFix the drift, or append '<!-- drift-ok: <reason> -->' to a line that is a "
        "genuinely-historical mention inside a canonical doc.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
