import importlib.util
import json
from pathlib import Path

import pytest
from blender_addon.manifest import collection_name, load_manifest, resolve_manifest_path


def test_blender_addon_can_be_inspected_without_blender() -> None:
    root = Path(__file__).parents[1] / "blender_addon"
    spec = importlib.util.spec_from_file_location(
        "atlas_addon", root / "__init__.py", submodule_search_locations=[str(root)]
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.bl_info["blender"] == (4, 0, 0)


def test_manifest_validation_accepts_supported_project_and_rejects_unknown_versions(tmp_path: Path) -> None:
    project = tmp_path / "project.json"
    project.write_text(json.dumps({"schema_version": "1.0", "atlases": []}), encoding="utf-8")

    path, data = load_manifest(project)

    assert path == project.resolve()
    assert data["atlases"] == []
    project.write_text(json.dumps({"schema_version": "2.0", "atlases": []}), encoding="utf-8")
    with pytest.raises(ValueError, match="Versión"):
        load_manifest(project)


def test_manifest_path_and_collection_names_are_safe_and_deterministic(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"elements": []}), encoding="utf-8")

    assert resolve_manifest_path(manifest) == manifest.resolve()
    assert collection_name("pared/techo") == "pared_techo"
    assert collection_name("grupo", {"grupo", "grupo (2)"}) == "grupo (3)"
    with pytest.raises(ValueError, match="Selecciona"):
        resolve_manifest_path(tmp_path / "otro.json")
