"""Contrato CPU del agrupamiento de recortes por nodo GLB."""

from pathlib import Path

from atlas_splitter.domain import AtlasCapabilities, AtlasElement, BoundingBox, UvManifest, stable_element_id
from atlas_splitter.geometry.object_grouping import ExportedAtlas, write_object_manifest


def _element(node_index: int, node_name: str) -> AtlasElement:
    return AtlasElement(
        element_id=stable_element_id(0, node_index, 0, 0, "primitive"),
        original_name=node_name,
        slug=node_name.lower().replace("_", "-"),
        scene_index=0,
        node_index=node_index,
        node_path=[node_name],
        mesh_index=0,
        primitive_index=0,
        bounding_box=BoundingBox(x=0, y=0, width=2, height=2),
        exported_files={"baseColor": "materials/piece.png"},
    )


def test_groups_parts_by_node_and_preserves_atlas_reference(tmp_path: Path) -> None:
    atlas = tmp_path / "first-house_day.webp"
    manifest = UvManifest(
        source_file="room.glb",
        capabilities=AtlasCapabilities.geometry_guided(),
        atlas_width=8,
        atlas_height=8,
        elements=[_element(0, "First_House_Baked"), _element(0, "First_House_Baked")],
    )
    result = write_object_manifest(
        tmp_path / "objects_manifest.json",
        tmp_path / "room.glb",
        [ExportedAtlas(atlas, tmp_path / "first-house_day", manifest, flip_v=True)],
    )

    assert result.objects[0].associations[0].method == "manual"
    assert result.objects[0].associations[0].uv_set is None
    assert len(result.objects) == 1
    assert result.objects[0].node_name == "First_House_Baked"
    assert result.objects[0].flip_v is True
    assert result.objects[0].atlas_paths == [str(atlas.resolve())]
    assert len(result.objects[0].parts) == 2


def test_preserves_multiple_atlases_for_the_same_node(tmp_path: Path) -> None:
    first_atlas = tmp_path / "first-house_day.webp"
    second_atlas = tmp_path / "first-house_night.webp"
    manifest = UvManifest(
        source_file="room.glb",
        capabilities=AtlasCapabilities.geometry_guided(),
        atlas_width=8,
        atlas_height=8,
        elements=[_element(0, "First_House_Baked")],
    )

    result = write_object_manifest(
        tmp_path / "objects_manifest.json",
        tmp_path / "room.glb",
        [
            ExportedAtlas(first_atlas, tmp_path / "first-house_day", manifest, flip_v=False),
            ExportedAtlas(second_atlas, tmp_path / "first-house_night", manifest, flip_v=False),
        ],
    )

    assert result.objects[0].atlas_path is None
    assert result.objects[0].atlas_paths == sorted([str(first_atlas.resolve()), str(second_atlas.resolve())])
    assert len(result.objects[0].associations) == 2
