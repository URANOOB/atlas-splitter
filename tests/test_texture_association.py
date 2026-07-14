"""Asociación determinista de atlas externos por los nombres conservados del GLB."""

from pathlib import Path
from types import SimpleNamespace

from atlas_splitter.geometry.texture_association import associate_named_external_atlases


def test_associates_room_node_families_and_ignores_original_variant(tmp_path: Path) -> None:
    names = (
        "first-house_day.webp",
        "fourth-extras_day.webp",
        "second-photos_day.webp",
        "second-photos_day.original.webp",
    )
    for name in names:
        (tmp_path / name).touch()
    loaded = SimpleNamespace(
        document=SimpleNamespace(
            nodes=[
                SimpleNamespace(name="First_House_Baked"),
                SimpleNamespace(name="Fourth_Russell_Raycaster"),
                SimpleNamespace(name="Fourth_Carl_Raycaster"),
                SimpleNamespace(name="Second_Photos_Baked"),
            ]
        )
    )
    result = associate_named_external_atlases(loaded, tmp_path)
    assert result[tmp_path / "first-house_day.webp"] == {0}
    assert result[tmp_path / "fourth-extras_day.webp"] == {1, 2}
    assert result[tmp_path / "second-photos_day.webp"] == {3}
