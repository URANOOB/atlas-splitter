"""Flujo GLB CPU: máscaras UV, recortes y manifiestos, sin GPU ni red."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

from atlas_splitter.geometry.glb_exporter import _flip_v, export_glb
from atlas_splitter.geometry.glb_loader import load_gltf
from atlas_splitter.geometry.texture_association import load_atlas_bindings


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

    bindings = tmp_path / "bindings.yaml"
    bindings.write_text(
        "atlas_bindings:\n  - atlas: atlas.png\n    nodes: [0]\n    uv_set: 0\n    flip_v: true\n",
        encoding="utf-8",
    )
    loaded = load_gltf(model)
    association = load_atlas_bindings(bindings, loaded)[0]
    bound = export_glb(
        loaded,
        tmp_path / "bound-output",
        atlas=association.atlas_path,
        node_indices=set(association.node_indices),
        uv_set=association.uv_set,
        flip_v=association.flip_v,
        force_external_atlas=association.manual_confirmation,
    )
    manifest_data = json.loads((tmp_path / "bound-output" / "uv_manifest.json").read_text(encoding="utf-8"))
    assert bound.elements[0].texcoord == 0
    assert manifest_data["elements"][0]["exported_files"]["uv_mask"].startswith("masks/")
    assert (tmp_path / "bound-output" / "blender" / "rebuild_scene.py").is_file()


def test_flips_only_the_v_coordinate_for_confirmed_external_atlas() -> None:
    assert _flip_v(np.array([[0.25, 0.0], [0.75, 1.0]])).tolist() == [[0.25, 1.0], [0.75, 0.0]]


def test_image_index_filters_a_multiatlas_node_to_its_declared_material(tmp_path: Path) -> None:
    for name, color in (("wall.png", (255, 0, 0, 255)), ("roof.png", (0, 0, 255, 255))):
        Image.new("RGBA", (8, 8), color).save(tmp_path / name)
    positions = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype="<f4").tobytes()
    texcoords = np.array([[0, 0], [1, 0], [0, 1]], dtype="<f4").tobytes()
    indices = np.array([0, 1, 2], dtype="<u2").tobytes()
    payload = positions + texcoords + indices
    (tmp_path / "mesh.bin").write_bytes(payload)
    model = tmp_path / "multiatlas.gltf"
    model.write_text(
        json.dumps(
            {
                "asset": {"version": "2.0"},
                "buffers": [{"uri": "mesh.bin", "byteLength": len(payload)}],
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
                "images": [{"uri": "wall.png"}, {"uri": "roof.png"}],
                "textures": [{"source": 0}, {"source": 1}],
                "materials": [
                    {"pbrMetallicRoughness": {"baseColorTexture": {"index": 0}}},
                    {"pbrMetallicRoughness": {"baseColorTexture": {"index": 1}}},
                ],
                "meshes": [{"primitives": [
                    {"attributes": {"POSITION": 0, "TEXCOORD_0": 1}, "indices": 2, "material": 0},
                    {"attributes": {"POSITION": 0, "TEXCOORD_0": 1}, "indices": 2, "material": 1},
                ]}],
                "nodes": [{"mesh": 0}],
                "scenes": [{"nodes": [0]}],
            }
        ),
        encoding="utf-8",
    )
    loaded = load_gltf(model)

    wall = export_glb(loaded, tmp_path / "wall-output", atlas=tmp_path / "wall.png", image_index=0)
    roof = export_glb(loaded, tmp_path / "roof-output", atlas=tmp_path / "roof.png", image_index=1)

    assert [element.material_index for element in wall.elements] == [0]
    assert [element.material_index for element in roof.elements] == [1]


def test_group_by_modes_produce_distinct_deterministic_element_counts(tmp_path: Path) -> None:
    image_path = tmp_path / "paint.png"
    Image.new("RGBA", (16, 16), (200, 20, 10, 255)).save(image_path)
    positions = np.array([[0, 0, 0]] * 6, dtype="<f4").tobytes()
    texcoords = np.array([[0, 0], [0.4, 0], [0, 0.4], [0.6, 0.6], [1, 0.6], [0.6, 1]], dtype="<f4").tobytes()
    indices = np.arange(6, dtype="<u2").tobytes()
    payload = positions + texcoords + indices
    (tmp_path / "mesh.bin").write_bytes(payload)
    model = tmp_path / "two-nodes.gltf"
    model.write_text(
        json.dumps(
            {
                "asset": {"version": "2.0"},
                "buffers": [{"uri": "mesh.bin", "byteLength": len(payload)}],
                "bufferViews": [
                    {"buffer": 0, "byteOffset": 0, "byteLength": len(positions)},
                    {"buffer": 0, "byteOffset": len(positions), "byteLength": len(texcoords)},
                    {"buffer": 0, "byteOffset": len(positions) + len(texcoords), "byteLength": len(indices)},
                ],
                "accessors": [
                    {"bufferView": 0, "componentType": 5126, "count": 6, "type": "VEC3"},
                    {"bufferView": 1, "componentType": 5126, "count": 6, "type": "VEC2"},
                    {"bufferView": 2, "componentType": 5123, "count": 6, "type": "SCALAR"},
                ],
                "images": [{"uri": "paint.png"}],
                "textures": [{"source": 0}],
                "materials": [{"pbrMetallicRoughness": {"baseColorTexture": {"index": 0}}}],
                "meshes": [
                    {
                        "primitives": [
                            {"attributes": {"POSITION": 0, "TEXCOORD_0": 1}, "indices": 2, "material": 0},
                            {"attributes": {"POSITION": 0, "TEXCOORD_0": 1}, "indices": 2, "material": 0},
                        ]
                    }
                ],
                "nodes": [{"name": "one", "mesh": 0}, {"name": "two", "mesh": 0}],
                "scenes": [{"nodes": [0, 1]}],
            }
        ),
        encoding="utf-8",
    )
    loaded = load_gltf(model)
    manifests = {
        mode: export_glb(loaded, tmp_path / mode, group_by=mode)
        for mode in ("node", "mesh", "primitive", "uv-island")
    }
    counts = {mode: len(manifest.elements) for mode, manifest in manifests.items()}
    assert counts == {"node": 2, "mesh": 1, "primitive": 4, "uv-island": 8}
    assert all(element.group_by == mode for mode, manifest in manifests.items() for element in manifest.elements)
    mesh_sources = manifests["mesh"].elements[0].source_primitives
    assert len(mesh_sources) == 4
    assert all("node_transform" in source for source in mesh_sources)


def test_node_group_keeps_regions_and_auxiliary_maps_per_material(tmp_path: Path) -> None:
    for name, color in (("base.png", (255, 0, 0, 255)), ("normal.png", (128, 128, 255, 255))):
        Image.new("RGBA", (8, 8), color).save(tmp_path / name)
    positions = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype="<f4").tobytes()
    texcoords = np.array([[0, 0], [1, 0], [0, 1]], dtype="<f4").tobytes()
    indices = np.array([0, 1, 2], dtype="<u2").tobytes()
    payload = positions + texcoords + indices
    (tmp_path / "mesh.bin").write_bytes(payload)
    model = tmp_path / "materials.gltf"
    model.write_text(
        json.dumps(
            {
                "asset": {"version": "2.0"},
                "buffers": [{"uri": "mesh.bin", "byteLength": len(payload)}],
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
                "images": [{"uri": "base.png"}, {"uri": "normal.png"}],
                "textures": [{"source": 0}, {"source": 1}],
                "materials": [
                    {"pbrMetallicRoughness": {"baseColorTexture": {"index": 0}}},
                    {"pbrMetallicRoughness": {"baseColorTexture": {"index": 0}}, "normalTexture": {"index": 1}},
                ],
                "meshes": [{"primitives": [
                    {"attributes": {"POSITION": 0, "TEXCOORD_0": 1}, "indices": 2, "material": 0},
                    {"attributes": {"POSITION": 0, "TEXCOORD_0": 1}, "indices": 2, "material": 1},
                ]}],
                "nodes": [{"mesh": 0}], "scenes": [{"nodes": [0]}],
            }
        ),
        encoding="utf-8",
    )

    output = tmp_path / "output"
    manifest = export_glb(load_gltf(model), output, group_by="node")

    assert len(manifest.elements) == 2
    assert {item.material_index for item in manifest.elements} == {0, 1}
    assert "normal" not in manifest.elements[0].exported_files
    assert (output / manifest.elements[1].exported_files["normal"]).is_file()
    assert "varios materiales" in manifest.elements[0].warnings[-1]
