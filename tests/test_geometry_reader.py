"""Pruebas CPU deterministas para la etapa 7.1 del lector glTF."""

import json
import struct
from pathlib import Path

import numpy as np
import pytest

from atlas_splitter.exceptions import AccessorDecodeError, GltfLoadError, PrimitiveDecodeError
from atlas_splitter.geometry.accessor_decoder import AccessorDecoder
from atlas_splitter.geometry.glb_loader import load_gltf
from atlas_splitter.geometry.primitive_decoder import decode_scene_primitives


def _write_gltf(tmp_path: Path, document: dict[str, object], payload: bytes) -> Path:
    (tmp_path / "mesh.bin").write_bytes(payload)
    document["buffers"] = [{"uri": "mesh.bin", "byteLength": len(payload)}]
    path = tmp_path / "scene.gltf"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def _write_glb(tmp_path: Path, document: dict[str, object], payload: bytes) -> Path:
    document["buffers"] = [{"byteLength": len(payload)}]
    json_chunk = json.dumps(document, separators=(",", ":")).encode("utf-8")
    json_chunk += b" " * (-len(json_chunk) % 4)
    binary_chunk = payload + b"\x00" * (-len(payload) % 4)
    contents = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(json_chunk) + 8 + len(binary_chunk))
    contents += struct.pack("<II", len(json_chunk), 0x4E4F534A) + json_chunk
    contents += struct.pack("<II", len(binary_chunk), 0x004E4942) + binary_chunk
    path = tmp_path / "triangle.glb"
    path.write_bytes(contents)
    return path


def _triangle_document(mode: int = 4, indices: bool = True) -> tuple[dict[str, object], bytes]:
    positions = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]], dtype="<f4").tobytes()
    texcoords = np.array([[0, 0], [1, 0], [0, 1], [1, 1]], dtype="<f4").tobytes()
    index_data = np.array([0, 1, 2] if mode == 4 else [0, 1, 2, 3], dtype="<u2").tobytes()
    payload = positions + texcoords + index_data
    attributes = {"POSITION": 0, "TEXCOORD_1": 1}
    primitive: dict[str, object] = {"attributes": attributes, "mode": mode}
    if indices:
        primitive["indices"] = 2
    document: dict[str, object] = {
        "asset": {"version": "2.0"},
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(positions)},
            {"buffer": 0, "byteOffset": len(positions), "byteLength": len(texcoords)},
            {"buffer": 0, "byteOffset": len(positions) + len(texcoords), "byteLength": len(index_data)},
        ],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 4, "type": "VEC3"},
            {"bufferView": 1, "componentType": 5126, "count": 4, "type": "VEC2"},
            {"bufferView": 2, "componentType": 5123, "count": len(index_data) // 2, "type": "SCALAR"},
        ],
        "meshes": [{"primitives": [primitive]}],
        "nodes": [{"name": "Casa", "mesh": 0, "translation": [2, 0, 0]}],
        "scenes": [{"nodes": [0]}],
    }
    return document, payload


def test_loads_glb_triangle_and_keeps_texcoord_set_and_node_transform(tmp_path: Path) -> None:
    document, payload = _triangle_document(mode=4)
    primitive = decode_scene_primitives(load_gltf(_write_glb(tmp_path, document, payload)))[0]
    assert primitive.triangle_indices.tolist() == [[0, 1, 2]]
    assert primitive.texcoords[1].tolist()[2] == [0.0, 1.0]
    assert primitive.node_path == ("Casa",)
    assert primitive.node_transform[:3, 3].tolist() == [2.0, 0.0, 0.0]


@pytest.mark.parametrize(("mode", "expected"), [(5, [[0, 1, 2], [2, 1, 3]]), (6, [[0, 1, 2], [0, 2, 3]])])
def test_converts_strip_and_fan_to_triangles(tmp_path: Path, mode: int, expected: list[list[int]]) -> None:
    document, payload = _triangle_document(mode=mode)
    primitive = decode_scene_primitives(load_gltf(_write_gltf(tmp_path, document, payload)))[0]
    assert primitive.triangle_indices.tolist() == expected


def test_decodes_nonindexed_geometry(tmp_path: Path) -> None:
    document, payload = _triangle_document(mode=4, indices=False)
    document["accessors"] = document["accessors"][:2]  # type: ignore[index]
    document["bufferViews"] = document["bufferViews"][:2]  # type: ignore[index]
    document["accessors"][0]["count"] = 3  # type: ignore[index]
    document["accessors"][1]["count"] = 3  # type: ignore[index]
    document["bufferViews"][0]["byteLength"] = 36  # type: ignore[index]
    document["bufferViews"][1]["byteOffset"] = 36  # type: ignore[index]
    document["bufferViews"][1]["byteLength"] = 24  # type: ignore[index]
    triangle_payload = payload[:36] + payload[48:72]
    primitive = decode_scene_primitives(load_gltf(_write_gltf(tmp_path, document, triangle_payload)))[0]
    assert primitive.triangle_indices.tolist() == [[0, 1, 2]]


def test_decodes_offsets_stride_normalized_and_sparse_accessor(tmp_path: Path) -> None:
    payload = b"xxxx" + bytes([0, 99, 255, 99]) + b"zz" + bytes([1, 128])
    document: dict[str, object] = {
        "asset": {"version": "2.0"},
        "bufferViews": [
            {"buffer": 0, "byteOffset": 4, "byteLength": 4, "byteStride": 2},
            {"buffer": 0, "byteOffset": 10, "byteLength": 1},
            {"buffer": 0, "byteOffset": 11, "byteLength": 1},
        ],
        "accessors": [
            {"bufferView": 0, "byteOffset": 0, "componentType": 5121, "normalized": True, "count": 2, "type": "SCALAR"},
            {
                "componentType": 5121,
                "count": 3,
                "type": "SCALAR",
                "sparse": {
                    "count": 1,
                    "indices": {"bufferView": 1, "componentType": 5121},
                    "values": {"bufferView": 2},
                },
            },
        ],
    }
    decoder = AccessorDecoder(load_gltf(_write_gltf(tmp_path, document, payload)))
    assert np.allclose(decoder.decode(0).reshape(-1), [0.0, 1.0])
    assert decoder.decode(1).reshape(-1).tolist() == [0, 128, 0]


def test_rejects_corrupt_or_remote_inputs(tmp_path: Path) -> None:
    corrupt = tmp_path / "bad.glb"
    corrupt.write_bytes(b"not-a-glb")
    with pytest.raises(GltfLoadError):
        load_gltf(corrupt)


def test_rejects_accessor_that_overflows_its_buffer_view(tmp_path: Path) -> None:
    document: dict[str, object] = {
        "asset": {"version": "2.0"},
        "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": 2}],
        "accessors": [{"bufferView": 0, "componentType": 5121, "count": 3, "type": "SCALAR"}],
    }
    with pytest.raises(AccessorDecodeError, match="bufferView"):
        AccessorDecoder(load_gltf(_write_gltf(tmp_path, document, b"abc"))).decode(0)


def test_reports_compressed_extension_and_rejects_compressed_primitive(tmp_path: Path) -> None:
    document, payload = _triangle_document()
    document["extensionsUsed"] = ["KHR_draco_mesh_compression"]
    document["meshes"][0]["primitives"][0]["extensions"] = {  # type: ignore[index]
        "KHR_draco_mesh_compression": {"bufferView": 0, "attributes": {}}
    }
    loaded = load_gltf(_write_gltf(tmp_path, document, payload))
    assert loaded.diagnostics[0].extension == "KHR_draco_mesh_compression"
    with pytest.raises(PrimitiveDecodeError, match="KHR_draco_mesh_compression"):
        decode_scene_primitives(loaded)
