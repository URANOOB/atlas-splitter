"""Flujo GLB CPU: máscaras UV, recortes y manifiestos, sin GPU ni red."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

from atlas_splitter.geometry.glb_exporter import _flip_v, export_glb
from atlas_splitter.geometry.glb_loader import load_gltf


def test_exports_material_crops_masks_manifests_and_blender_script(tmp_path: Path) -> None:
    image_path = tmp_path / "paint.png"
    Image.new("RGBA", (12, 12), (200, 20, 10, 255)).save(image_path)
    positions = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype="<f4").tobytes()
    texcoords = np.array([[0, 0], [1, 0], [0, 1]], dtype="<f4").tobytes()
    indices = np.array([0, 1, 2], dtype="<u2").tobytes()
    (tmp_path / "mesh.bin").write_bytes(positions + texcoords + indices)
    (tmp_path / "model.gltf").write_text(
        json.dumps(
            {
                "asset": {"version": "2.0"},
                "buffers": [{"uri": "mesh.bin", "byteLength": len(positions + texcoords + indices)}],
                "bufferViews": [
                    {"buffer": 0, "byteOffset": 0, "byteLength": len(positions)},
                    {"buffer": 0, "byteOffset": len(positions), "byteLength": len(texcoords)},
                    {"buffer": 0, "byteOffset": len(positions) + len(texcoords), "byteLength": len(indices)},
                ],
                "accessors": [
                    {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3"},
                    {"bufferView": 1, "componentType": 5126, "count": 3, "type": "VEC2"},
                    {"bufferView": 2, "componentType": 5123, "count": 3, "type": "SCALAR"},
                ],
                "images": [{"uri": "paint.png"}], "textures": [{"source": 0}],
                "materials": [{"pbrMetallicRoughness": {"baseColorTexture": {"index": 0}}}],
                "meshes": [
                    {
                        "primitives": [
                            {"attributes": {"POSITION": 0, "TEXCOORD_0": 1}, "indices": 2, "material": 0}
                        ]
                    }
                ],
                "nodes": [{"mesh": 0}], "scenes": [{"nodes": [0]}],
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "output"
    manifest = export_glb(load_gltf(tmp_path / "model.gltf"), output, atlas=image_path)
    element = manifest.elements[0]
    assert (output / "uv_manifest.json").is_file()
    assert (output / "scene_manifest.json").is_file()
    assert (output / "blender" / "rebuild_scene.py").is_file()
    assert (output / element.exported_files["uv_mask"]).is_file()
    assert (output / element.exported_files["baseColor"]).is_file()


def test_exports_uvs_with_an_explicit_manual_atlas_when_glb_has_no_material(tmp_path: Path) -> None:
    image_path = tmp_path / "atlas.png"
    Image.new("RGBA", (8, 8), (20, 40, 60, 255)).save(image_path)
    positions = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype="<f4").tobytes()
    texcoords = np.array([[0, 0], [1, 0], [0, 1]], dtype="<f4").tobytes()
    indices = np.array([0, 1, 2], dtype="<u2").tobytes()
    (tmp_path / "mesh.bin").write_bytes(positions + texcoords + indices)
    model = tmp_path / "room.gltf"
    model.write_text(
        json.dumps(
            {
                "asset": {"version": "2.0"},
                "buffers": [{"uri": "mesh.bin", "byteLength": len(positions + texcoords + indices)}],
                "bufferViews": [
                    {"buffer": 0, "byteOffset": 0, "byteLength": len(positions)},
                    {"buffer": 0, "byteOffset": len(positions), "byteLength": len(texcoords)},
                    {"buffer": 0, "byteOffset": len(positions) + len(texcoords), "byteLength": len(indices)},
                ],
                "accessors": [
                    {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3"},
                    {"bufferView": 1, "componentType": 5126, "count": 3, "type": "VEC2"},
                    {"bufferView": 2, "componentType": 5123, "count": 3, "type": "SCALAR"},
                ],
                "meshes": [{"primitives": [{"attributes": {"POSITION": 0, "TEXCOORD_0": 1}, "indices": 2}]}],
                "nodes": [{"mesh": 0}], "scenes": [{"nodes": [0]}],
            }
        ),
        encoding="utf-8",
    )
    manifest = export_glb(load_gltf(model), tmp_path / "output", atlas=image_path, allow_unbound_atlas=True)
    assert manifest.elements[0].compatibility_level == "manual_external_atlas"
    assert manifest.elements[0].image_index is None
    assert "asociado manualmente" in manifest.elements[0].warnings[0]


def test_flips_only_the_v_coordinate_for_confirmed_external_atlas() -> None:
    assert _flip_v(np.array([[0.25, 0.0], [0.75, 1.0]])).tolist() == [[0.25, 1.0], [0.75, 0.0]]
