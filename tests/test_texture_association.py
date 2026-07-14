"""Asociación determinista de atlas externos por los nombres conservados del GLB."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from atlas_splitter.exceptions import GltfLoadError
from atlas_splitter.geometry.texture_association import (
    associate_named_external_atlases,
    load_atlas_bindings,
    resolve_external_atlases,
)


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


def test_yaml_bindings_resolve_names_and_record_manual_confirmation(tmp_path: Path) -> None:
    atlas = tmp_path / "custom.webp"
    atlas.touch()
    bindings = tmp_path / "bindings.yaml"
    bindings.write_text(
        "version: 1\n"
        "atlas_bindings:\n"
        "  - atlas: custom.webp\n"
        "    nodes: [Roof]\n"
        "    texture_slot: normal\n"
        "    uv_set: 1\n"
        "    flip_v: true\n"
    )
    loaded = SimpleNamespace(document=SimpleNamespace(nodes=[SimpleNamespace(name="Roof")]))

    result = load_atlas_bindings(bindings, loaded)

    assert result[0].atlas_path == atlas.resolve()
    assert result[0].node_indices == frozenset({0})
    assert result[0].method == "yaml"
    assert result[0].manual_confirmation is True
    assert result[0].uv_set == 1
    assert result[0].flip_v is True
    assert result[0].texture_slot == "normal"


def test_yaml_bindings_reject_ambiguous_node_names(tmp_path: Path) -> None:
    (tmp_path / "custom.webp").touch()
    bindings = tmp_path / "bindings.yaml"
    bindings.write_text("atlas_bindings:\n  - atlas: custom.webp\n    nodes: [Roof]\n    uv_set: 0\n")
    loaded = SimpleNamespace(
        document=SimpleNamespace(nodes=[SimpleNamespace(name="Roof"), SimpleNamespace(name="Roof")])
    )

    with pytest.raises(GltfLoadError, match="ambiguo"):
        load_atlas_bindings(bindings, loaded)


def test_automatic_name_ambiguity_is_rejected_safely(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "wall.webp").touch()
    loaded = SimpleNamespace(
        document=SimpleNamespace(images=[SimpleNamespace(uri="wall.png"), SimpleNamespace(uri="wall.jpg")], nodes=[])
    )
    monkeypatch.setattr("atlas_splitter.geometry.texture_association._nodes_using_image", lambda *_: {0})

    with pytest.raises(GltfLoadError, match="--bindings"):
        resolve_external_atlases(loaded, tmp_path)


def test_automatic_association_records_normalized_name_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "brick-wall.webp").touch()
    loaded = SimpleNamespace(document=SimpleNamespace(images=[SimpleNamespace(uri="brick_wall.png")], nodes=[]))
    monkeypatch.setattr("atlas_splitter.geometry.texture_association._nodes_using_image", lambda *_: {2})

    result = resolve_external_atlases(loaded, tmp_path)

    assert result[0].atlas_path == (tmp_path / "brick-wall.webp").resolve()
    assert result[0].method == "normalized_name"
    assert result[0].confidence == 0.70
    assert result[0].node_indices == frozenset({2})


def test_automatic_association_records_hash_evidence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "unknown.webp").touch()
    loaded = SimpleNamespace(document=SimpleNamespace(images=[SimpleNamespace(uri="declared.png")], nodes=[]))
    monkeypatch.setattr("atlas_splitter.geometry.texture_association._nodes_using_image", lambda *_: {3})
    monkeypatch.setattr("atlas_splitter.geometry.texture_association._matching_image_indices", lambda *_: [0])

    result = resolve_external_atlases(loaded, tmp_path)

    assert result[0].method == "image_hash"
    assert result[0].confidence == 0.99
    assert result[0].node_indices == frozenset({3})


def test_automatic_association_prefers_hash_over_a_matching_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "wall-basecolor.webp").touch()
    loaded = SimpleNamespace(document=SimpleNamespace(images=[SimpleNamespace(uri="wall.png")], nodes=[]))
    monkeypatch.setattr("atlas_splitter.geometry.texture_association._matching_image_indices", lambda *_: [0])
    monkeypatch.setattr("atlas_splitter.geometry.texture_association._nodes_using_image", lambda *_: {4})

    result = resolve_external_atlases(loaded, tmp_path)

    assert result[0].method == "image_hash"
    assert result[0].confidence == 0.99
