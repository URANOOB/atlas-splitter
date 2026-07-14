"""Pruebas sin Blender para el generador del script de reconstrucción."""

from atlas_splitter.blender.script_writer import (
    write_atlas_rebuild_script,
    write_object_rebuild_script,
    write_rebuild_script,
    write_single_object_rebuild_script,
)


def test_rebuild_script_is_deterministic_and_uses_only_bpy(tmp_path) -> None:
    destination = tmp_path / "blender" / "rebuild_scene.py"
    script = write_rebuild_script(destination, tmp_path / "model.glb", tmp_path / "uv_manifest.json")
    first = script.read_text(encoding="utf-8")
    repeated = write_rebuild_script(destination, tmp_path / "model.glb", tmp_path / "uv_manifest.json")
    assert repeated.read_text(encoding="utf-8") == first
    assert "import bpy" in first
    assert "AtlasSplitter" in first
    assert "bpy.data.collections.remove(collection, do_unlink=True)" in first
    assert "manifest_path = Path(local_path(UV_MANIFEST))" in first
    compile(first, str(destination), "exec")


def test_object_rebuild_script_uses_full_editable_atlas(tmp_path) -> None:
    destination = tmp_path / "blender" / "rebuild_scene.py"
    script = write_object_rebuild_script(destination, tmp_path / "model.glb", tmp_path / "objects_manifest.json")
    contents = script.read_text(encoding="utf-8")
    assert "OBJECT_MANIFEST" in contents
    assert "ShaderNodeMapping" in contents
    assert 'obj.data.materials.clear()' in contents
    assert "def local_path(path):" in contents
    assert "TARGET_OBJECT_ID = None" in contents
    assert "Path(local_path(OBJECT_MANIFEST)).read_text" in contents
    compile(contents, str(destination), "exec")


def test_single_object_script_declares_and_filters_its_target(tmp_path) -> None:
    destination = tmp_path / "objects" / "object_0123456789abcdef" / "rebuild_object.py"
    script = write_single_object_rebuild_script(
        destination, tmp_path / "model.glb", tmp_path / "objects_manifest.json", "object_0123456789abcdef"
    )
    contents = script.read_text(encoding="utf-8")
    assert 'TARGET_OBJECT_ID = "object_0123456789abcdef"' in contents
    assert "bpy.data.objects.remove(obj, do_unlink=True)" in contents
    compile(contents, str(destination), "exec")


def test_atlas_script_filters_nodes_by_the_external_atlas(tmp_path) -> None:
    destination = tmp_path / "atlas" / "blender" / "rebuild_scene.py"
    script = write_atlas_rebuild_script(
        destination, tmp_path / "model.glb", tmp_path / "objects_manifest.json", tmp_path / "first-house_day.webp"
    )
    contents = script.read_text(encoding="utf-8")
    assert 'TARGET_ATLAS_PATH = "' in contents
    assert "kept_names = {item[\"node_name\"] for item in selected}" in contents
    assert "SEPARATE_LOOSE_PARTS = True" in contents
    assert 'bpy.ops.mesh.separate(type="LOOSE")' in contents
    compile(contents, str(destination), "exec")
