#!/usr/bin/env python3
"""Tests for playtest_manifest — pure parse/anchor logic against tmp fixtures.

Stdlib `assert` only; run directly:  python3 scripts/test_playtest_manifest.py
Ends with a live smoke run (the wiring test) asserting the real script exits 0
with a non-empty, three-tier manifest.
"""
from __future__ import annotations

import datetime as dt
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import playtest_manifest as pm  # noqa: E402


def test_anchor_picks_newest_across_scatter_and_excludes_live():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        archive = root / "sq-playtest-archive"
        projects = root
        archive.mkdir()
        live = projects / "sq-playtest-pingpong.md"

        old = archive / "sq-playtest-pingpong.archive-2026-05-28-glenross-coyote.md"
        old.write_text("old")
        loose = projects / "sq-playtest-pingpong-archive-2026-06-04.md"
        loose.write_text("new")
        live.write_text("LIVE — must be ignored even though it is newest")

        # Force mtimes: old < loose < live
        os.utime(old, (time.time() - 1000, time.time() - 1000))
        os.utime(loose, (time.time() - 500, time.time() - 500))
        os.utime(live, (time.time(), time.time()))

        a = pm.find_anchor(archive_dir=archive, projects_dir=projects, live=live)
        assert a.source == loose, f"expected loose archive, got {a.source.name}"
        assert "glenross" not in a.label  # label came from loose, not old
        print("ok  anchor: newest-across-scatter, excludes live")


def test_anchor_empty_raises_loud():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        archive = root / "sq-playtest-archive"
        archive.mkdir()
        try:
            pm.find_anchor(archive_dir=archive, projects_dir=root, live=root / "x.md")
        except pm.ManifestError as e:
            assert "first playtest" in str(e)
            print("ok  anchor: empty union fails loud (no silent 0 days)")
            return
        raise AssertionError("expected ManifestError on empty archive union")


def test_parse_sprint_completions_handles_pr_ref_variants():
    log = "\n".join(
        [
            "chore(sprint): complete 83-2 — Standing Folio AC8 gaps (PR sidequest-ui#325)",
            "chore(sprint): complete 77-2 — typed quest/stakes narrator tools (PR #621)",
            "chore(sprint): complete 74-4 — world-flavor hardening (server #620)",
            "chore(sprint): complete 75-10 — wire player-NPC reference signal",
            "feat(x): unrelated commit should be ignored",
        ]
    )
    stories = pm.parse_sprint_completions(log)
    assert len(stories) == 4, [s.story_id for s in stories]
    by_id = {s.story_id: s for s in stories}
    assert by_id["83-2"].pr_ref == "sidequest-ui#325"
    assert by_id["77-2"].pr_ref == "#621"
    assert by_id["77-2"].title == "typed quest/stakes narrator tools"
    assert by_id["74-4"].pr_ref == "server #620"
    assert by_id["75-10"].pr_ref == ""  # no PR ref present
    assert by_id["75-10"].title == "wire player-NPC reference signal"
    print("ok  sprint parse: id/title/PR-ref across all four ref shapes")


def test_parse_pingpong_surfaces_open_and_fixed_only():
    text = """
### [BUG] lore Cast display names broken

- **Priority:** high
- **Status:** fixed (FIXER 2026-06-04 — server PR #630 MERGED; pull+restart to verify)

### [GAP] ally seating not mechanical

- **Status:** open (needs an Architect story)

### [UX] something already done

- **Status:** verified
"""
    tasks = pm.parse_pingpong(text)
    assert len(tasks) == 2, [(t.title, t.status) for t in tasks]
    assert tasks[0].status == "fixed" and "Cast" in tasks[0].title
    assert tasks[0].tag == "BUG"
    assert "pull+restart" in tasks[0].note
    assert tasks[1].status == "open"
    print("ok  ping-pong parse: open+fixed surfaced, verified dropped")


def test_collect_designs_tags_status_and_filters_by_date():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        specs = root / "docs/superpowers/specs"
        plans = root / "docs/superpowers/plans"
        (specs / "completed").mkdir(parents=True)
        (plans).mkdir(parents=True)

        (specs / "2026-06-03-feature-inventory-surfacing-design.md").write_text("x")
        (specs / "completed/2026-06-02-wonderland-world-design.md").write_text("x")
        (plans / "2026-05-01-too-old-plan.md").write_text("x")  # before anchor
        (specs / "no-date-prefix.md").write_text("x")  # skipped

        designs = pm.collect_designs(root, anchor=dt.date(2026, 6, 1))
        topics = {d.topic: d for d in designs}
        assert "too-old" not in " ".join(topics)  # date filter dropped it
        assert "no-date-prefix" not in " ".join(topics)
        assert topics["feature-inventory-surfacing"].status == "in-flight"
        assert topics["feature-inventory-surfacing"].kind == "spec"
        assert topics["wonderland-world"].status == "shipped"
        print("ok  designs: date-filtered, shipped/in-flight tagged by location")


def smoke_live_script():
    """Wiring test: the real script runs end-to-end against the repo, exit 0,
    three tiers present. Skips loudly (not silently) if no archive exists here."""
    script = Path(__file__).resolve().parent / "playtest_manifest.py"
    proc = subprocess.run(
        [sys.executable, str(script)], capture_output=True, text=True
    )
    if proc.returncode == 2 and "first playtest" in proc.stdout:
        print("skip smoke: no playtest archive on this machine (loud, expected)")
        return
    assert proc.returncode == 0, f"exit {proc.returncode}: {proc.stdout}{proc.stderr}"
    for tier in ("TIER 1", "TIER 2", "TIER 3", "Last playtest:"):
        assert tier in proc.stdout, f"missing {tier!r} in manifest output"
    print("ok  smoke: live script exit 0, all three tiers + anchor present")


def main() -> int:
    tests = [
        test_anchor_picks_newest_across_scatter_and_excludes_live,
        test_anchor_empty_raises_loud,
        test_parse_sprint_completions_handles_pr_ref_variants,
        test_parse_pingpong_surfaces_open_and_fixed_only,
        test_collect_designs_tags_status_and_filters_by_date,
        smoke_live_script,
    ]
    for t in tests:
        t()
    print(f"\n{len(tests)} checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
