"""Tests for the per-world split of ``generate_r2_preview``.

Loading every world's tiles on one page pulled far too many images at once, so
the generator now emits one ``<genre>/<world>.html`` gallery per world plus a
lightweight ``index.html`` that links to each. These tests pin that shape:

- ``world_page_href`` derives the one-dir-deep link,
- ``build_index`` links every world present (and only those),
- ``build_world_page`` isolates a single world's tiles + keeps the gallery JS,
- ``main`` writes the index + per-world tree and no longer writes the old
  combined ``r2_preview.html`` (the wiring test).

``generate_r2_preview`` uses bare sibling imports (``from render_common import``)
because it's run as a script, so we import it top-level with ``scripts/`` on the
path — mirroring ``uv run python scripts/generate_r2_preview.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent.parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import generate_r2_preview as gp  # noqa: E402


def _asset(genre: str, world: str, kind: str, name: str) -> gp.Asset:
    key = f"genre_packs/{genre}/worlds/{world}/assets/{kind}/{name}"
    return gp.Asset(genre=genre, world=world, kind=kind, key=key)


_ASSETS = [
    _asset("heavy_metal", "barsoom", "portraits", "dejah.png"),
    _asset("heavy_metal", "barsoom", "poi", "atmosphere_plant.png"),
    _asset("heavy_metal", "evropi", "portraits", "knight.png"),
    _asset("wry_whimsy", "tumbledown", "portraits", "mouse.png"),
]


def test_world_page_href_is_one_dir_deep():
    assert gp.world_page_href("heavy_metal", "barsoom") == "heavy_metal/barsoom.html"


def test_asset_tree_buckets_by_genre_world_kind():
    tree = gp.asset_tree(_ASSETS)
    assert sorted(tree) == ["heavy_metal", "wry_whimsy"]
    assert sorted(tree["heavy_metal"]) == ["barsoom", "evropi"]
    assert sorted(tree["heavy_metal"]["barsoom"]) == ["poi", "portraits"]
    assert len(tree["heavy_metal"]["barsoom"]["portraits"]) == 1


def test_build_index_links_every_world_and_only_those():
    tree = gp.asset_tree(_ASSETS)
    index = gp.build_index(tree, base="https://cdn.example.com", generated="now")
    # Every written world is linked, at its one-dir-deep href.
    assert 'href="heavy_metal/barsoom.html"' in index
    assert 'href="heavy_metal/evropi.html"' in index
    assert 'href="wry_whimsy/tumbledown.html"' in index
    # No link to a world that has no page.
    assert "nonexistent.html" not in index
    # Expected counts are surfaced so heavy worlds are visible before opening.
    assert "expected" in index


def test_build_world_page_isolates_one_world_and_keeps_gallery():
    tree = gp.asset_tree(_ASSETS)
    page, count = gp.build_world_page(
        "heavy_metal",
        "barsoom",
        tree["heavy_metal"]["barsoom"],
        base="https://cdn.example.com",
        generated="now",
    )
    assert count == 2
    # This world's tiles are present...
    assert "dejah.png" in page
    assert "atmosphere_plant.png" in page
    # ...but a sibling world's tile is not.
    assert "knight.png" not in page
    # Gallery machinery survives the split: live counter, refresh, lightbox, backlink.
    assert 'id="rendered"' in page
    assert "setInterval(refresh" in page
    assert 'id="lightbox"' in page
    assert 'href="../index.html"' in page


def test_main_writes_index_and_per_world_tree(tmp_path, monkeypatch):
    """Wiring: main() enumerates assets and writes the index + per-world pages."""
    monkeypatch.setattr(
        gp, "collect_assets", lambda: (_ASSETS, {"portraits": 3, "poi": 1})
    )
    monkeypatch.setattr(
        sys, "argv", ["generate_r2_preview.py", "--out", str(tmp_path)]
    )

    assert gp.main() == 0

    assert (tmp_path / "index.html").exists()
    assert (tmp_path / "heavy_metal" / "barsoom.html").exists()
    assert (tmp_path / "heavy_metal" / "evropi.html").exists()
    assert (tmp_path / "wry_whimsy" / "tumbledown.html").exists()
    # The old single combined page is retired — it's the whole reason we split.
    assert not (tmp_path / "r2_preview.html").exists()

    # The barsoom page holds only barsoom's tiles.
    barsoom = (tmp_path / "heavy_metal" / "barsoom.html").read_text()
    assert "atmosphere_plant.png" in barsoom
    assert "knight.png" not in barsoom
