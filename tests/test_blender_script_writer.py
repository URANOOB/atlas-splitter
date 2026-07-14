"""Pruebas sin Blender para el generador del script de reconstrucción."""

from __future__ import annotations

import json
import shutil
import struct
import subprocess
from pathlib import Path

import pytest
from PIL import Image

from atlas_splitter.blender.script_writer import (
    write_atlas_rebuild_script,
    write_object_rebuild_script,
    write_rebuild_script,
    write_single_object_rebuild_script,
)

BLENDER = shutil.which("blender")
requires_blender = pytest.mark.skipif(BLENDER is None, reason="Blender no estÃ¡ disponible en PATH")


def _write_minimal_textured_glb(destination: Path, image_path: Path) -> None:
    """Escribe un GLB local de un triÃ¡ngulo con un material e imagen embebidos."""
    positions = struct.pack("<9f", 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0)
    indices = struct.pack("<3H", 0, 1, 2)
    image_bytes = image_path.read_bytes()
    padded_positions = _pad4(positions)
    padded_indices = _pad4(indices)
    binary = padded_positions + padded_indices + _pad4(image_bytes)
    document = {
        "asset": {"version": "2.0"},
        "buffers": [{"byteLength": len(binary)}],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(positions), "target": 34962},
            {"buffer": 0, "byteOffset": len(padded_positions), "byteLength": len(indices), "target": 34963},
            {
                "buffer": 0,
                "byteOffset": len(padded_positions) + len(padded_indices),
                "byteLength": len(image_bytes),
            },
        ],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3", "max": [1, 1, 0], "min": [0, 0, 0]},
            {"bufferView": 1, "componentType": 5123, "count": 3, "type": "SCALAR"},
        ],
        "images": [{"bufferView": 2, "mimeType": "image/png"}],
        "textures": [{"source": 0}],
        "materials": [{"name": "ImportedMaterial", "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}}}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1, "material": 0}]}],
        "nodes": [{"name": "Triangle", "mesh": 0}],
        "scenes": [{"nodes": [0]}],
        "scene": 0,
    }
    json_chunk = _pad4(json.dumps(document, separators=(",", ":")).encode("utf-8"), padding=b" ")
    destination.write_bytes(
        struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(json_chunk) + 8 + len(binary))
        + struct.pack("<I4s", len(json_chunk), b"JSON")
        + json_chunk
        + struct.pack("<I4s", len(binary), b"BIN\x00")
        + binary
    )


def _pad4(data: bytes, *, padding: bytes = b"\x00") -> bytes:
    return data + padding * ((-len(data)) % 4)


def _run_blender(script: Path, output: Path, assertion: str) -> None:
    assert BLENDER is not None
    result = subprocess.run(
        [
            BLENDER,
            "--background",
            "--factory-startup",
            "--python",
            str(script),
            "--python-expr",
            f"import bpy; {assertion}; bpy.ops.wm.save_as_mainfile(filepath={str(output)!r})",
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert output.is_file()


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
    assert "obj.data.materials.clear()" in contents
    assert "def local_path(path):" in contents
    assert "TARGET_OBJECT_ID = None" in contents
    assert "Path(local_path(OBJECT_MANIFEST)).read_text" in contents
    assert "nodo con varios atlas" in contents
    assert 'item.get("atlas_paths", [item["atlas_path"]])' in contents
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
    assert 'kept_names = {item["node_name"] for item in selected}' in contents
    assert "SEPARATE_LOOSE_PARTS = True" in contents
    assert 'bpy.ops.mesh.separate(type="LOOSE")' in contents
    compile(contents, str(destination), "exec")


@requires_blender
def test_generated_script_reconstructs_minimal_glb_in_background(tmp_path: Path) -> None:
    atlas = tmp_path / "atlas.png"
    Image.new("RGBA", (1, 1), "red").save(atlas)
    source = tmp_path / "triangle.glb"
    _write_minimal_textured_glb(source, atlas)
    manifest = tmp_path / "objects_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "objects": [
                    {
                        "object_id": "triangle-atlas",
                        "node_name": "Triangle",
                        "atlas_path": str(atlas.resolve()),
                        "flip_v": False,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    script = write_object_rebuild_script(tmp_path / "rebuild.py", source, manifest)

    _run_blender(
        script,
        tmp_path / "reconstructed.blend",
        "obj = bpy.data.objects['Triangle']; assert obj.active_material.name == 'triangle-atlas'",
    )


@requires_blender
def test_generated_script_preserves_imported_material_for_multiple_atlases(tmp_path: Path) -> None:
    atlas_one = tmp_path / "atlas-one.png"
    atlas_two = tmp_path / "atlas-two.png"
    Image.new("RGBA", (1, 1), "red").save(atlas_one)
    Image.new("RGBA", (1, 1), "blue").save(atlas_two)
    source = tmp_path / "triangle.glb"
    _write_minimal_textured_glb(source, atlas_one)
    manifest = tmp_path / "objects_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "objects": [
                    {
                        "object_id": "triangle-atlas",
                        "node_name": "Triangle",
                        "atlas_path": str(atlas_one.resolve()),
                        "atlas_paths": [str(atlas_one.resolve()), str(atlas_two.resolve())],
                        "flip_v": False,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    script = write_object_rebuild_script(tmp_path / "rebuild.py", source, manifest)

    _run_blender(
        script,
        tmp_path / "multiple-atlases.blend",
        "obj = bpy.data.objects['Triangle']; assert obj.active_material.name == 'ImportedMaterial'",
    )
