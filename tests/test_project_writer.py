from pathlib import Path

from atlas_splitter.domain import AtlasCapabilities, UvManifest
from atlas_splitter.geometry.object_grouping import ExportedAtlas
from atlas_splitter.geometry.project_writer import write_project_manifest


def test_project_manifest_records_multiple_atlases_and_evidence(tmp_path: Path) -> None:
    first, second = tmp_path / "wall.png", tmp_path / "roof.png"
    first.touch()
    second.touch()
    manifest = UvManifest(
        source_file=str(tmp_path / "model.gltf"),
        capabilities=AtlasCapabilities.geometry_guided(),
        atlas_width=8,
        atlas_height=8,
    )
    atlases = [
        ExportedAtlas(first, tmp_path / "output" / "wall", manifest, False, "image_hash", 0.99),
        ExportedAtlas(second, tmp_path / "output" / "roof", manifest, False, "normalized_name", 0.70),
    ]

    result = write_project_manifest(tmp_path / "output" / "project.json", tmp_path / "model.gltf", atlases)

    assert (tmp_path / "output" / "project.json").is_file()
    assert result.processing_mode == "geometry_guided"
    assert result.geometry_available
    assert [item.atlas_id for item in result.atlases] == ["wall", "roof"]
    assert [item.association_method for item in result.atlases] == ["image_hash", "normalized_name"]
