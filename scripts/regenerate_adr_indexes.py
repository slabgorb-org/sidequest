#!/usr/bin/env python3
"""Regenerate ADR indexes from frontmatter per ADR-088.

Outputs:
  docs/adr/README.md        — full index, grouped by primary tag
  docs/adr/SUPERSEDED.md    — supersession archive, grouped by successor
  docs/adr/DRIFT.md         — implementation-drift view
  CLAUDE.md                 — compact category-keyed ADR index block

The generated regions in README.md and CLAUDE.md are delimited by HTML comment
markers. On first run, if a file lacks markers, the script inserts them at the
known boundary (see MARKER_INSERT_HINTS below) and then fills the content. On
subsequent runs, it replaces whatever is between the markers.

DRIFT.md and SUPERSEDED.md are regenerated wholesale — they have no preamble
to preserve.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).parent.parent
ADR_DIR = ROOT / "docs" / "adr"
CLAUDE_MD = ROOT / "CLAUDE.md"

MARKER_BEGIN = "<!-- ADR-INDEX:GENERATED:BEGIN -->"
MARKER_END = "<!-- ADR-INDEX:GENERATED:END -->"

# Tag → display section title (order here defines section order in the README).
TAG_SECTIONS: list[tuple[str, str]] = [
    ("core-architecture", "Core Architecture"),
    ("prompt-engineering", "Prompt Engineering"),
    ("agent-system", "Agent System"),
    ("game-systems", "Game Systems"),
    ("frontend-protocol", "Frontend / Protocol"),
    ("multiplayer", "Multiplayer"),
    ("transport-infrastructure", "Transport / Infrastructure"),
    ("narrator", "Narrator / Text"),
    ("npc-character", "NPC / Character Systems"),
    ("media-audio", "Media / Audio / Rendering"),
    ("turn-management", "Turn Management"),
    ("room-graph", "Room Graph / Dungeon Crawl"),
    ("code-generation", "Code Generation / Tooling"),
    ("observability", "Observability"),
    ("codebase-decomposition", "Codebase Decomposition"),
    ("narrator-migration", "Narrator Architecture"),
    ("genre-mechanics", "Genre Mechanics"),
    ("project-lifecycle", "Project Lifecycle / Meta"),
]

# Small hand-curated list — the top reads for a new contributor / agent.
# Kept explicit because "load-bearing" is a judgment call, not derivable.
LOAD_BEARING_IDS = [82, 85, 67, 59, 38, 35, 14, 88]


@dataclass
class ADR:
    id: int
    filename: str
    title: str
    status: str
    date: str
    tags: list[str]
    impl_status: str
    impl_pointer: int | None
    supersedes: list[int]
    superseded_by: int | None

    @property
    def primary_tag(self) -> str:
        return self.tags[0] if self.tags else "core-architecture"

    @property
    def link(self) -> str:
        return f"[ADR-{self.id:03d}: {self.title}]({self.filename})"

    @property
    def short_link(self) -> str:
        return f"[ADR-{self.id:03d}]({self.filename})"


FM_BLOCK_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def parse_yaml_lite(block: str) -> dict:
    """Minimal YAML parser for the fixed frontmatter shape ADR-088 defines.

    Handles: scalar key: value, inline flow lists [a, b, "c d"], null, quoted
    strings. Does NOT handle block-style lists, nested objects, multi-line
    strings. The frontmatter schema in ADR-088 only uses the forms this
    parser handles.
    """
    out: dict = {}
    for line in block.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, raw = line.partition(":")
        key = key.strip()
        raw = raw.strip()
        out[key] = _parse_value(raw)
    return out


def _parse_value(raw: str):
    if raw in ("", "null", "~"):
        return None
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        # Split on commas NOT inside quotes
        items = _split_flow_list(inner)
        return [_parse_scalar(i.strip()) for i in items if i.strip()]
    return _parse_scalar(raw)


def _split_flow_list(s: str) -> list[str]:
    parts: list[str] = []
    buf: list[str] = []
    in_dq = False
    in_sq = False
    for c in s:
        if c == '"' and not in_sq:
            in_dq = not in_dq
            buf.append(c)
        elif c == "'" and not in_dq:
            in_sq = not in_sq
            buf.append(c)
        elif c == "," and not in_dq and not in_sq:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(c)
    if buf:
        parts.append("".join(buf))
    return parts


def _parse_scalar(s: str):
    s = s.strip()
    if not s:
        return None
    if s[0] == '"' and s[-1] == '"':
        return s[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    if s[0] == "'" and s[-1] == "'":
        return s[1:-1]
    if s.lower() in ("null", "~"):
        return None
    try:
        return int(s)
    except ValueError:
        return s


def load_adr(filepath: Path) -> ADR | None:
    content = filepath.read_text()
    m = FM_BLOCK_RE.match(content)
    if not m:
        print(f"  WARN: {filepath.name} has no frontmatter, skipping", file=sys.stderr)
        return None
    fm = parse_yaml_lite(m.group(1))
    try:
        return ADR(
            id=int(fm["id"]),
            filename=filepath.name,
            title=str(fm["title"]),
            status=str(fm["status"]),
            date=str(fm.get("date", "")),
            tags=list(fm.get("tags") or []),
            impl_status=str(fm.get("implementation-status", "live")),
            impl_pointer=fm.get("implementation-pointer"),
            supersedes=list(fm.get("supersedes") or []),
            superseded_by=fm.get("superseded-by"),
        )
    except (KeyError, ValueError, TypeError) as e:
        print(f"  WARN: {filepath.name} frontmatter malformed ({e})", file=sys.stderr)
        return None


def load_all() -> list[ADR]:
    adrs: list[ADR] = []
    for p in sorted(ADR_DIR.glob("[0-9][0-9][0-9]-*.md")):
        adr = load_adr(p)
        if adr is not None:
            adrs.append(adr)
    return adrs


# -------------- Rendering --------------

STATUS_BADGES = {
    "accepted": "✓ accepted",
    "proposed": "◇ proposed",
    "superseded": "✗ superseded",
    "historical": "✗ historical",
    "deprecated": "✗ deprecated",
}
IMPL_BADGES = {
    "live": "live",
    "drift": "**drift**",
    "partial": "*partial*",
    "deferred": "deferred",
    "not-applicable": "—",
    "retired": "—",
}


def impl_cell(adr: ADR) -> str:
    label = IMPL_BADGES.get(adr.impl_status, adr.impl_status)
    pointer = adr.impl_pointer
    if pointer is None:
        return label
    if isinstance(pointer, int):
        return f"{label} → ADR-{pointer:03d}"
    if isinstance(pointer, str) and pointer.isdigit():
        return f"{label} → ADR-{int(pointer):03d}"
    return f"{label} → {pointer}"


def render_readme_body(adrs: list[ADR]) -> str:
    by_primary_tag: dict[str, list[ADR]] = {}
    for adr in adrs:
        if adr.status in ("superseded", "historical"):
            continue
        by_primary_tag.setdefault(adr.primary_tag, []).append(adr)

    lines: list[str] = []
    lines.append(
        "> **Generated.** Do not edit this section by hand. Update frontmatter on the "
        "individual ADR files and rerun `scripts/regenerate_adr_indexes.py`. The "
        "preamble above the BEGIN marker and any prose below the END marker are "
        "preserved."
    )
    lines.append("")

    for tag_key, title in TAG_SECTIONS:
        bucket = by_primary_tag.get(tag_key, [])
        if not bucket:
            continue
        lines.append(f"## {title}")
        lines.append("")
        lines.append("| ADR | Status | Impl |")
        lines.append("|-----|--------|------|")
        for adr in sorted(bucket, key=lambda a: a.id):
            status = STATUS_BADGES.get(adr.status, adr.status)
            lines.append(f"| {adr.link} | {status} | {impl_cell(adr)} |")
        lines.append("")

    # Superseded / historical appendix
    retired = [a for a in adrs if a.status in ("superseded", "historical")]
    if retired:
        lines.append("## Superseded / Historical")
        lines.append("")
        lines.append("Retired ADRs. See [SUPERSEDED.md](SUPERSEDED.md) for the grouped view.")
        lines.append("")
        lines.append("| ADR | Status | Successor |")
        lines.append("|-----|--------|-----------|")
        for adr in sorted(retired, key=lambda a: a.id):
            status = STATUS_BADGES.get(adr.status, adr.status)
            if adr.superseded_by is not None:
                by = next((a for a in adrs if a.id == adr.superseded_by), None)
                succ = by.short_link if by else f"ADR-{adr.superseded_by:03d}"
            else:
                succ = "—"
            lines.append(f"| {adr.link} | {status} | {succ} |")
        lines.append("")

    # Drift view
    drift = [a for a in adrs if a.impl_status in ("drift", "partial", "deferred")]
    if drift:
        lines.append("## Implementation Drift")
        lines.append("")
        lines.append(
            "ADRs whose implementation is absent, partial, or deferred. "
            "See [DRIFT.md](DRIFT.md) for priority-tier details."
        )
        lines.append("")
        lines.append("| ADR | Impl | Pointer |")
        lines.append("|-----|------|---------|")
        for adr in sorted(drift, key=lambda a: (a.impl_status, a.id)):
            label = IMPL_BADGES.get(adr.impl_status, adr.impl_status)
            pointer = adr.impl_pointer
            if pointer is None:
                ptr = "—"
            else:
                by = next((a for a in adrs if a.id == pointer), None)
                if by:
                    ptr = by.short_link
                elif isinstance(pointer, int):
                    ptr = f"ADR-{pointer:03d}"
                elif isinstance(pointer, str) and pointer.isdigit():
                    ptr = f"ADR-{int(pointer):03d}"
                else:
                    ptr = str(pointer)
            lines.append(f"| {adr.link} | {label} | {ptr} |")
        lines.append("")

    return "\n".join(lines)


def render_superseded(adrs: list[ADR]) -> str:
    retired = [a for a in adrs if a.status in ("superseded", "historical")]
    by_successor: dict[int | None, list[ADR]] = {}
    for a in retired:
        by_successor.setdefault(a.superseded_by, []).append(a)

    lines: list[str] = []
    lines.append("# Superseded / Historical ADRs")
    lines.append("")
    lines.append(
        "> Generated by `scripts/regenerate_adr_indexes.py`. Do not edit by hand. "
        "ADRs remain in the tree for audit. Current decisions are in the primary "
        "[README.md](README.md)."
    )
    lines.append("")

    # Grouped by successor
    adr_map = {a.id: a for a in adrs}
    lines.append("## Superseded — by successor")
    lines.append("")
    if not any(sb is not None for sb in by_successor):
        lines.append("_No superseded ADRs with a named successor._")
        lines.append("")
    else:
        for succ_id in sorted(sb for sb in by_successor if sb is not None):
            succ = adr_map.get(succ_id)
            succ_str = succ.link if succ else f"ADR-{succ_id:03d}"
            lines.append(f"### Superseded by {succ_str}")
            lines.append("")
            for a in sorted(by_successor[succ_id], key=lambda x: x.id):
                lines.append(f"- {a.link} — {a.status}")
            lines.append("")

    # Historical (no successor)
    historicals = [a for a in retired if a.superseded_by is None]
    if historicals:
        lines.append("## Historical — no successor")
        lines.append("")
        lines.append(
            "These ADRs describe features or decisions that were cut without "
            "direct replacement."
        )
        lines.append("")
        for a in sorted(historicals, key=lambda x: x.id):
            lines.append(f"- {a.link} — {a.status}")
        lines.append("")

    return "\n".join(lines)


def render_drift(adrs: list[ADR]) -> str:
    drift = [a for a in adrs if a.impl_status in ("drift", "partial", "deferred")]
    adr_map = {a.id: a for a in adrs}

    lines: list[str] = []
    lines.append("# Implementation Drift — ADRs Not Fully Live")
    lines.append("")
    lines.append(
        "> Generated by `scripts/regenerate_adr_indexes.py`. Do not edit by hand. "
        "An ADR moves off this list when its `implementation-status` frontmatter "
        "field is updated to `live`. Priority tiers and restoration verdicts are in "
        "[ADR-087](087-post-port-subsystem-restoration-plan.md)."
    )
    lines.append("")

    for bucket_key, heading in [
        ("drift", "Drift — accepted ADR, implementation absent"),
        ("partial", "Partial — accepted ADR, implementation incomplete"),
        ("deferred", "Deferred — accepted/proposed, not yet implemented"),
    ]:
        bucket = [a for a in drift if a.impl_status == bucket_key]
        if not bucket:
            continue
        lines.append(f"## {heading}")
        lines.append("")
        lines.append("| ADR | Status | Pointer |")
        lines.append("|-----|--------|---------|")
        for a in sorted(bucket, key=lambda x: x.id):
            status = STATUS_BADGES.get(a.status, a.status)
            pointer = a.impl_pointer
            if pointer is None:
                ptr = "—"
            else:
                by = adr_map.get(pointer)
                if by:
                    ptr = by.link
                elif isinstance(pointer, int):
                    ptr = f"ADR-{pointer:03d}"
                elif isinstance(pointer, str) and pointer.isdigit():
                    ptr = f"ADR-{int(pointer):03d}"
                else:
                    ptr = str(pointer)
            lines.append(f"| {a.link} | {status} | {ptr} |")
        lines.append("")

    return "\n".join(lines)


def render_claude_block(adrs: list[ADR]) -> str:
    """Compact ADR index for CLAUDE.md — one line per tag, accepted only."""
    adr_map = {a.id: a for a in adrs}
    by_primary_tag: dict[str, list[ADR]] = {}
    for adr in adrs:
        if adr.status != "accepted":
            continue
        by_primary_tag.setdefault(adr.primary_tag, []).append(adr)

    lines: list[str] = []
    lines.append(
        "> Generated block. Edit frontmatter on individual ADRs + rerun "
        "`scripts/regenerate_adr_indexes.py`. Preamble above and `Conventions:` "
        "trailer below the markers are preserved."
    )
    lines.append("")

    # Load-bearing reads
    lines.append("**Load-bearing reads — start here:**")
    for adr_id in LOAD_BEARING_IDS:
        a = adr_map.get(adr_id)
        if a is None or a.status != "accepted":
            continue
        lines.append(f"- **ADR-{a.id:03d}** {a.title} — {a.status}")
    lines.append("")

    for tag_key, title in TAG_SECTIONS:
        bucket = by_primary_tag.get(tag_key, [])
        if not bucket:
            continue
        ids = ", ".join(f"{a.id:03d}" for a in sorted(bucket, key=lambda x: x.id))
        lines.append(f"**{title} ({ids})**")
        parts: list[str] = []
        for a in sorted(bucket, key=lambda x: x.id):
            prefix = "**" if a.id in LOAD_BEARING_IDS else ""
            suffix_bits: list[str] = []
            if a.impl_status == "drift":
                suffix_bits.append("drift")
            elif a.impl_status == "partial":
                suffix_bits.append("partial")
            elif a.impl_status == "deferred":
                suffix_bits.append("deferred")
            suffix = f" *({', '.join(suffix_bits)})*" if suffix_bits else ""
            parts.append(f"{prefix}{a.id:03d} {a.title}{prefix}{suffix}")
        lines.append("- " + " · ".join(parts))
        lines.append("")

    lines.append(
        "**Conventions:** Bold = load-bearing for current architecture. "
        "`drift`/`partial`/`deferred` in a line means the ADR is accepted but "
        "implementation is not fully live — see [DRIFT.md](docs/adr/DRIFT.md). "
        "Superseded/historical ADRs are filtered from this view — see "
        "[SUPERSEDED.md](docs/adr/SUPERSEDED.md)."
    )
    return "\n".join(lines)


# -------------- Marker-aware in-place writer --------------

def replace_between_markers(
    filepath: Path, body: str, insert_before_line_prefix: str | None = None,
) -> None:
    """Write `body` between MARKER_BEGIN / MARKER_END in filepath.

    If markers don't exist yet: find the first line starting with
    `insert_before_line_prefix` (raw string match). Insert markers + body
    immediately before that line. If `insert_before_line_prefix` is None,
    append markers + body to end of file.
    """
    text = filepath.read_text()
    if MARKER_BEGIN in text and MARKER_END in text:
        begin_idx = text.index(MARKER_BEGIN)
        end_idx = text.index(MARKER_END, begin_idx) + len(MARKER_END)
        new_text = (
            text[:begin_idx]
            + MARKER_BEGIN
            + "\n\n"
            + body.rstrip()
            + "\n\n"
            + MARKER_END
            + text[end_idx:]
        )
    else:
        block = (
            f"{MARKER_BEGIN}\n\n"
            f"{body.rstrip()}\n\n"
            f"{MARKER_END}\n"
        )
        if insert_before_line_prefix is not None:
            lines = text.splitlines(keepends=True)
            insert_at = None
            for i, line in enumerate(lines):
                if line.startswith(insert_before_line_prefix):
                    insert_at = i
                    break
            if insert_at is None:
                # Fallback: append to end
                new_text = text.rstrip() + "\n\n" + block
            else:
                # First-run migration: everything from the hint line to EOF is
                # the hand-maintained content we are replacing. Truncate and
                # emit preamble + generated block.
                new_text = "".join(lines[:insert_at]).rstrip() + "\n\n" + block
        else:
            new_text = text.rstrip() + "\n\n" + block
    filepath.write_text(new_text)


def main() -> None:
    adrs = load_all()
    print(f"Loaded {len(adrs)} ADRs")

    # README: preserve preamble, replace tag sections + appendices with generated body
    readme_body = render_readme_body(adrs)
    replace_between_markers(
        ADR_DIR / "README.md",
        readme_body,
        insert_before_line_prefix="## Core Architecture",
    )
    print(f"Wrote {ADR_DIR / 'README.md'}")

    # SUPERSEDED.md: full regen
    sup_path = ADR_DIR / "SUPERSEDED.md"
    sup_path.write_text(render_superseded(adrs))
    print(f"Wrote {sup_path}")

    # DRIFT.md: full regen
    drift_path = ADR_DIR / "DRIFT.md"
    drift_path.write_text(render_drift(adrs))
    print(f"Wrote {drift_path}")

    # CLAUDE.md: replace block between markers
    claude_block = render_claude_block(adrs)
    replace_between_markers(
        CLAUDE_MD,
        claude_block,
        insert_before_line_prefix="**Load-bearing reads",
    )
    print(f"Wrote {CLAUDE_MD}")

    # Report tag coverage — any ADRs landed in an unknown tag?
    known = {k for k, _ in TAG_SECTIONS}
    orphans: list[int] = []
    for a in adrs:
        if a.primary_tag not in known:
            orphans.append(a.id)
    if orphans:
        print(f"\nWARN: ADRs with unknown primary tag: {orphans}", file=sys.stderr)


if __name__ == "__main__":
    main()
