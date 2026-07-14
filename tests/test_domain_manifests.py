"""Pruebas puramente CPU para los contratos de dominio versionados."""

import json

import pytest
from pydantic import ValidationError

from atlas_splitter.domain import (
    AtlasCapabilities,
    AtlasElement,
    BoundingBox,
    SceneManifest,
    UvManifest,
    slugify,
    stable_element_id,
    write_versioned_manifest,
)


def _element() -> AtlasElement:
    return AtlasElement(
        element_id=stable_element_id(0, 1, 2, 3, "primitive"),
        original_name="Roof / Front",
        slug="roof-front",
        scene_index=0,
        node_index=1,
        mesh_index=2,
        primitive_index=3,
        bounding_box=BoundingBox(x=1, y=2, width=3, height=4),
    )


def test_stable_element_id_does_not_depend_on_visual_order() -> None:
    assert stable_element_id(0, 1, 2, 3, "primitive") == stable_element_id(0, 1, 2, 3, "primitive")
    assert stable_element_id(0, 1, 2, 3, "primitive") != stable_element_id(0, 1, 2, 4, "primitive")


def test_slugify_removes_paths_and_is_bounded() -> None:
    assert slugify("../../Techo principal!.png") == "techo-principal-png"
    assert slugify("***", fallback="unassigned") == "unassigned"
    assert len(slugify("a" * 200)) == 80


def test_versioned_manifests_are_deterministic_and_atomic(tmp_path) -> None:
    manifest = UvManifest(
        source_file="model.glb",
        capabilities=AtlasCapabilities.geometry_guided(),
        atlas_width=64,
        atlas_height=32,
        elements=[_element()],
    )
    destination = tmp_path / "uv_manifest.json"
    write_versioned_manifest(destination, manifest)
    first = destination.read_text(encoding="utf-8")
    write_versioned_manifest(destination, manifest)
    assert destination.read_text(encoding="utf-8") == first
    assert json.loads(first)["schema_version"] == "1.0"
    assert json.loads(first)["capabilities"]["reconstruction_quality"] == "geometry_guided"


def test_manifest_rejects_unsafe_slugs_and_uses_declared_capabilities() -> None:
    with pytest.raises(ValidationError, match="safe lowercase filename"):
        AtlasElement(**(_element().model_dump() | {"slug": "../unsafe"}))
    semantic = SceneManifest(
        source_file="atlas.webp",
        capabilities=AtlasCapabilities.approximate_2d_only(),
    )
    assert semantic.capabilities.model_dump() == {
        "uv_available": False,
        "geometry_available": False,
        "reconstruction_quality": "approximate_2d_only",
    }
