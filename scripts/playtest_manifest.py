#!/usr/bin/env python3
"""Playtest Phase 0 — "What changed since last playtest?" test manifest.

Read-only gatherer. Anchors on the newest playtest archive (by mtime, globbing both
scatter locations), then surfaces five sources tiered so they don't drown each other:

  Tier 1  Features to test   — sprint completions + merged PRs + landed specs/plans
  Tier 2  Unverified fixes   — live ping-pong `open`/`fixed`-awaiting-verify items
  Tier 3  Coverage backstop  — raw per-subrepo commit counts (flags untracked churn)

Never writes. Fails loud (No Silent Fallbacks): empty archive -> non-zero exit;
`gh` unavailable -> a loud SKIPPED line, not an empty omission.

Usage:
    python3 scripts/playtest_manifest.py            # text manifest for the operator
    python3 scripts/playtest_manifest.py --json     # raw gathered data
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

# --- Locations (ping-pong/archive live under ~/Projects, shared across checkouts) -----
REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECTS_DIR = Path.home() / "Projects"
ARCHIVE_DIR = PROJECTS_DIR / "sq-playtest-archive"
LIVE_PINGPONG = PROJECTS_DIR / "sq-playtest-pingpong.md"

# subrepo dir -> GitHub slug (orchestrator first)
SUBREPOS: dict[str, str] = {
    ".": "slabgorb/sidequest",
    "sidequest-server": "slabgorb/sidequest-server",
    "sidequest-ui": "slabgorb/sidequest-ui",
    "sidequest-content": "slabgorb/sidequest-content",
    "sidequest-daemon": "slabgorb/sidequest-daemon",
    "sidequest-composer": "slabgorb/sidequest-composer",
}
SPEC_DIRS = ("docs/superpowers/specs", "docs/superpowers/plans")

DATE_PREFIX = re.compile(r"^(\d{4}-\d{2}-\d{2})")
PR_NUM = re.compile(r"#(\d+)")


class ManifestError(RuntimeError):
    """Loud failure — surfaced to the operator, non-zero exit."""


# --- Anchor --------------------------------------------------------------------------
@dataclass
class Anchor:
    date: dt.date
    label: str
    source: Path


def _archive_candidates(archive_dir: Path, projects_dir: Path, live: Path) -> list[Path]:
    """Union of both scatter locations, excluding the live ping-pong file."""
    found: list[Path] = []
    if archive_dir.is_dir():
        found += [p for p in archive_dir.iterdir() if p.is_file()]
    if projects_dir.is_dir():
        for p in projects_dir.iterdir():
            if not p.is_file() or p == live:
                continue
            name = p.name
            if name.startswith("sq-playtest-pingpong") and (
                "archive" in name or name.endswith(".bak")
            ):
                found.append(p)
    return found


def _label_from_name(name: str) -> str:
    """Best-effort human label (display only) — text after the date, sans extension."""
    stem = re.sub(r"\.(md|bak)$", "", name)
    stem = re.sub(r"\.md$", "", stem)
    m = re.search(r"\d{4}-\d{2}-\d{2}-?(.*)$", stem)
    tail = (m.group(1) if m else "").strip("-. ")
    return tail or "(unlabeled)"


def find_anchor(
    archive_dir: Path = ARCHIVE_DIR,
    projects_dir: Path = PROJECTS_DIR,
    live: Path = LIVE_PINGPONG,
) -> Anchor:
    candidates = _archive_candidates(archive_dir, projects_dir, live)
    if not candidates:
        raise ManifestError(
            f"No prior playtest archive found under {archive_dir} or {projects_dir}. "
            "This is the first playtest, or the archive dir moved — not a silent 0 days."
        )
    newest = max(candidates, key=lambda p: p.stat().st_mtime)
    date = dt.date.fromtimestamp(newest.stat().st_mtime)
    return Anchor(date=date, label=_label_from_name(newest.name), source=newest)


# --- Sources -------------------------------------------------------------------------
@dataclass
class Story:
    story_id: str
    title: str
    pr_ref: str


SPRINT_LINE = re.compile(r"complete\s+(?P<id>\S+)\s+[—-]\s+(?P<rest>.*)$")
PR_TAIL = re.compile(r"\s*\((?:PR\s+)?(?P<ref>[^)]*#\d+|#\d+)\)\s*$")


def parse_sprint_completions(log_text: str) -> list[Story]:
    out: list[Story] = []
    for line in log_text.splitlines():
        m = SPRINT_LINE.search(line)
        if not m:
            continue
        rest = m.group("rest").strip()
        pr_ref = ""
        tail = PR_TAIL.search(rest)
        if tail:
            pr_ref = tail.group("ref").strip()
            rest = rest[: tail.start()].strip()
        out.append(Story(story_id=m.group("id"), title=rest, pr_ref=pr_ref))
    return out


@dataclass
class PingTask:
    tag: str
    title: str
    status: str  # 'open' | 'fixed'
    note: str


PING_HEADER = re.compile(r"^###\s+(?:\[(?P<tag>[^\]]+)\]\s*)?(?P<title>.+?)\s*$")
PING_STATUS = re.compile(r"^[-*]\s*\*\*Status:\*\*\s*(?P<status>\w[\w-]*)\s*(?P<note>.*)$")


def parse_pingpong(text: str) -> list[PingTask]:
    """Split into `### ` blocks; surface open + fixed-awaiting-verify items."""
    tasks: list[PingTask] = []
    cur_tag = cur_title = None
    for line in text.splitlines():
        h = PING_HEADER.match(line)
        if h:
            cur_tag = (h.group("tag") or "").strip()
            cur_title = h.group("title").strip()
            continue
        s = PING_STATUS.match(line)
        if s and cur_title is not None:
            status = s.group("status").lower()
            if status in ("open", "fixed"):
                tasks.append(
                    PingTask(
                        tag=cur_tag or "",
                        title=cur_title,
                        status=status,
                        note=s.group("note").strip(" ()"),
                    )
                )
            cur_tag = cur_title = None  # consume; one status per block
    return tasks


@dataclass
class Design:
    date: str
    topic: str
    kind: str  # 'spec' | 'plan'
    status: str  # 'shipped' | 'in-flight'


def collect_designs(repo_root: Path, anchor: dt.date) -> list[Design]:
    out: list[Design] = []
    for rel in SPEC_DIRS:
        base = repo_root / rel
        kind = "spec" if rel.endswith("specs") else "plan"
        for p in list(base.glob("*.md")) + list(base.glob("completed/*.md")):
            m = DATE_PREFIX.match(p.name)
            if not m:
                continue
            try:
                fdate = dt.date.fromisoformat(m.group(1))
            except ValueError:
                continue
            if fdate < anchor:
                continue
            topic = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", p.name)
            topic = re.sub(r"-(design|plan)?\.md$", "", topic)
            out.append(
                Design(
                    date=m.group(1),
                    topic=topic,
                    kind=kind,
                    status="shipped" if "completed" in p.parts else "in-flight",
                )
            )
    out.sort(key=lambda d: d.date, reverse=True)
    return out


# --- Git / gh IO (thin, defensive) ---------------------------------------------------
def _run(args: list[str], cwd: Path | None = None) -> tuple[int, str]:
    proc = subprocess.run(
        args, cwd=cwd, capture_output=True, text=True, env=_clean_env()
    )
    return proc.returncode, proc.stdout


def _clean_env() -> dict:
    import os

    env = dict(os.environ)
    env.pop("GITHUB_TOKEN", None)  # keyring gotcha: a stale token 401s gh
    return env


def git_sprint_log(repo_root: Path, anchor: dt.date) -> str:
    code, out = _run(
        [
            "git", "-C", str(repo_root), "log",
            f"--since={anchor.isoformat()}",
            "--grep=chore(sprint): complete",
            "--pretty=%s",
        ]
    )
    return out if code == 0 else ""


def git_commit_count(repo_dir: Path, anchor: dt.date) -> int | None:
    # `.git` may be a dir (orchestrator/subrepos) or a file (worktree) — .exists() covers
    # both. Missing -> loud None, surfaced as an ERROR line, never a silent 0.
    if not (repo_dir / ".git").exists():
        return None
    code, out = _run(
        ["git", "-C", str(repo_dir), "log", f"--since={anchor.isoformat()}", "--oneline"]
    )
    if code != 0:
        return None
    return len([ln for ln in out.splitlines() if ln.strip()])


@dataclass
class MergedPR:
    repo: str
    number: int
    title: str


def gh_merged_prs(slug: str, anchor: dt.date) -> list[MergedPR] | None:
    """Returns None on gh failure (loud SKIPPED upstream), list otherwise."""
    code, out = _run(
        [
            "gh", "pr", "list", "-R", slug, "--state", "merged",
            "--search", f"merged:>={anchor.isoformat()}",
            "--json", "number,title", "--limit", "200",
        ]
    )
    if code != 0:
        return None
    try:
        rows = json.loads(out or "[]")
    except json.JSONDecodeError:
        return None
    short = slug.split("/")[-1].replace("sidequest-", "") or "orc"
    return [MergedPR(repo=short, number=r["number"], title=r["title"]) for r in rows]


# --- Assembly ------------------------------------------------------------------------
@dataclass
class Manifest:
    anchor: Anchor
    days: int
    stories: list[Story]
    prs_unmatched: dict[str, list[MergedPR]]
    pr_skipped: list[str]
    designs: list[Design]
    unverified: list[PingTask]
    churn: dict[str, int | None] = field(default_factory=dict)


def gather(
    repo_root: Path = REPO_ROOT,
    archive_dir: Path = ARCHIVE_DIR,
    projects_dir: Path = PROJECTS_DIR,
    live: Path = LIVE_PINGPONG,
    today: dt.date | None = None,
) -> Manifest:
    anchor = find_anchor(archive_dir, projects_dir, live)
    today = today or dt.date.today()
    days = (today - anchor.date).days

    stories = parse_sprint_completions(git_sprint_log(repo_root, anchor.date))
    story_pr_nums = {
        int(n) for s in stories for n in PR_NUM.findall(s.pr_ref)
    }

    prs_unmatched: dict[str, list[MergedPR]] = {}
    pr_skipped: list[str] = []
    for d, slug in SUBREPOS.items():
        prs = gh_merged_prs(slug, anchor.date)
        if prs is None:
            pr_skipped.append(slug)
            continue
        leftover = [p for p in prs if p.number not in story_pr_nums]
        if leftover:
            prs_unmatched[slug.split("/")[-1]] = leftover

    designs = collect_designs(repo_root, anchor.date)

    unverified = []
    if live.is_file():
        unverified = parse_pingpong(live.read_text(encoding="utf-8", errors="replace"))

    churn = {d: git_commit_count(repo_root / d, anchor.date) for d in SUBREPOS}

    return Manifest(
        anchor=anchor,
        days=days,
        stories=stories,
        prs_unmatched=prs_unmatched,
        pr_skipped=pr_skipped,
        designs=designs,
        unverified=unverified,
        churn=churn,
    )


# --- Render --------------------------------------------------------------------------
def render_text(m: Manifest) -> str:
    L: list[str] = []
    L.append("═══════════════════════════════════════════════════════")
    L.append("  PLAYTEST MANIFEST — what changed since last playtest")
    L.append("═══════════════════════════════════════════════════════")
    L.append(
        f"Last playtest: {m.anchor.date}  ({m.anchor.label})   "
        f"— {m.days} day(s) ago"
    )
    local_churn = sum(c for c in m.churn.values() if c)
    remote_prs = sum(len(v) for v in m.prs_unmatched.values())
    L.append(f"Anchor file:   {m.anchor.source.name}")
    L.append(f"Local churn:   {local_churn} commit(s) in your working trees since then")
    if local_churn == 0 and remote_prs > 0:
        L.append(
            "  ⚠ LOCAL TREES ARE BEHIND REMOTE — "
            f"{remote_prs} PR(s) merged on develop but 0 pulled locally."
        )
        L.append("    PULL + restart before verifying, or you'll test stale code/content.")
    L.append("")

    # Tier 1
    L.append("── TIER 1 — Features to test ──────────────────────────")
    L.append(f"  Sprint stories completed ({len(m.stories)}):")
    if m.stories:
        for s in m.stories:
            ref = f"   [{s.pr_ref}]" if s.pr_ref else ""
            L.append(f"    {s.story_id:<7} {s.title}{ref}")
    else:
        L.append("    (none)")
    n_prs = sum(len(v) for v in m.prs_unmatched.values())
    L.append(f"  Merged PRs without a sprint story ({n_prs}):")
    if m.prs_unmatched:
        for repo, prs in m.prs_unmatched.items():
            for p in prs:
                L.append(f"    {repo} #{p.number}  {p.title}")
    else:
        L.append("    (none)")
    if m.pr_skipped:
        L.append(f"    SKIPPED (gh unavailable): {', '.join(m.pr_skipped)}")
    L.append(f"  Designs landed — specs/plans ({len(m.designs)}):")
    if m.designs:
        for d in m.designs:
            L.append(f"    [{d.status:<9}] {d.date}  {d.topic} ({d.kind})")
    else:
        L.append("    (none)")
    L.append("")

    # Tier 2
    L.append("── TIER 2 — Unverified fixes (verify FIRST) ───────────")
    if m.unverified:
        for t in m.unverified:
            tag = f"[{t.tag}] " if t.tag else ""
            note = f"  — {t.note}" if t.note else ""
            L.append(f"    ({t.status:<5}) {tag}{t.title}{note}")
    else:
        L.append("    (none in the live ping-pong working set)")
    L.append("")

    # Tier 3
    L.append("── TIER 3 — Coverage backstop (LOCAL working-tree churn) ──")
    for d, count in m.churn.items():
        name = d if d != "." else "(orchestrator)"
        if count is None:
            L.append(f"    {name:<20} ERROR: not a git repo / git failed")
        elif count == 0:
            L.append(f"    {name:<20} 0 commits")
        else:
            L.append(f"    {name:<20} {count} commits")
    L.append("")
    L.append("Suggested order: Tier 2 unverified fixes first, then Tier 1 features")
    L.append("touching the world you're about to play. Eyeball any high-churn subrepo")
    L.append("in Tier 3 with few matching stories/PRs.")
    return "\n".join(L)


def to_dict(m: Manifest) -> dict:
    return {
        "last_playtest": {
            "date": m.anchor.date.isoformat(),
            "label": m.anchor.label,
            "source": m.anchor.source.name,
            "days_ago": m.days,
        },
        "tier1": {
            "stories": [vars(s) for s in m.stories],
            "prs_unmatched": {k: [vars(p) for p in v] for k, v in m.prs_unmatched.items()},
            "pr_skipped": m.pr_skipped,
            "designs": [vars(d) for d in m.designs],
        },
        "tier2_unverified": [vars(t) for t in m.unverified],
        "tier3_churn": m.churn,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Playtest Phase 0 test manifest.")
    ap.add_argument("--json", action="store_true", help="emit raw gathered data as JSON")
    args = ap.parse_args()
    try:
        m = gather()
    except ManifestError as e:
        print(f"playtest_manifest: {e}")
        return 2
    if args.json:
        print(json.dumps(to_dict(m), indent=2))
    else:
        print(render_text(m))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
