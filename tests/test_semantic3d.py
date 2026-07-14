"""Contratos CPU para la primera agrupación semántica 3D."""

import json

import numpy as np
from PIL import Image

from atlas_splitter.blender.script_writer import write_semantic_objects_rebuild_script
from atlas_splitter.geometry.types import DecodedPrimitive, PrimitiveReference
from atlas_splitter.semantic.types import GroupingResult, SemanticGroup
from atlas_splitter.semantic3d.service import (
    Semantic3DConfig,
    _external_atlas_uvs,
    _manifest,
    _write_components_for_primitives,
    _write_json,
    _write_proposals,
)
from atlas_splitter.semantic3d.topology import bounding_box_distance, mesh_connected_components


def test_mesh_decomposition_is_deterministic() -> None:
    triangles = np.asarray([[0, 1, 2], [2, 1, 3], [4, 5, 6]], dtype=np.int64)
    first = mesh_connected_components(triangles)
    second = mesh_connected_components(triangles)
    assert [item.triangle_rows.tolist() for item in first] == [[0, 1], [2]]
    assert [item.vertex_indices.tolist() for item in second] == [[0, 1, 2, 3], [4, 5, 6]]


def test_bounding_box_proximity_is_zero_when_boxes_touch() -> None:
    assert bounding_box_distance(((0.0, 0.0, 0.0), (1.0, 1.0, 1.0)), ((1.0, 0.0, 0.0), (2.0, 1.0, 1.0))) == 0.0


def test_external_atlas_uvs_flip_v_before_rasterization() -> None:
    uvs = np.asarray([[0.25, 0.0], [0.75, 1.0]])
    assert _external_atlas_uvs(uvs, True).tolist() == [[0.25, 1.0], [0.75, 0.0]]
    assert _external_atlas_uvs(uvs, False).tolist() == uvs.tolist()


def test_multiple_primitives_keep_distinct_editable_component_ids(tmp_path) -> None:
    positions = np.asarray([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    uvs = np.asarray([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]])
    primitives = [
        DecodedPrimitive(
            PrimitiveReference(0, 0, index, None), positions, np.asarray([[0, 1, 2]]), {1: uvs}, ("Room",), np.eye(4)
        )
        for index in (0, 1)
    ]

    components, _ = _write_components_for_primitives(
        tmp_path, primitives, Image.new("RGBA", (8, 8), "white"), Semantic3DConfig(uv_set=1)
    )

    assert [item["component_id"] for item in components] == [
        "primitive_000_component_001",
        "primitive_001_component_001",
    ]
    assert all(item["geometry_evidence"] == "exact" for item in components)


def test_proximity_edges_create_one_composite_object_proposal(tmp_path) -> None:
    for component_id in ("component_001", "component_002"):
        directory = tmp_path / "components" / component_id
        directory.mkdir(parents=True)
        mask = np.full((1, 1), 255, dtype=np.uint8)
        Image.fromarray(mask, "L").save(directory / "uv_mask.png")
    components = [
        {
            "component_id": "component_001",
            "uv_mask": "components/component_001/uv_mask.png",
            "bounding_box_uv": {"x": 1, "y": 1, "width": 1, "height": 1},
        },
        {
            "component_id": "component_002",
            "uv_mask": "components/component_002/uv_mask.png",
            "bounding_box_uv": {"x": 2, "y": 1, "width": 1, "height": 1},
        },
        {
            "component_id": "component_003",
            "uv_mask": "components/component_002/uv_mask.png",
            "bounding_box_uv": {"x": 2, "y": 1, "width": 1, "height": 1},
        },
    ]
    proposals, pieces = _write_proposals(
        tmp_path,
        Image.new("RGBA", (4, 4), "white"),
        components,
        [{"components": ["component_001", "component_002"], "distance": 0.0}],
    )
    assert [item["component_ids"] for item in proposals] == [["component_001", "component_002"], ["component_003"]]
    assert [item.piece_id for item in pieces] == ["proposal_001", "proposal_002"]


def test_manifest_serialization_is_deterministic_and_marks_uncertain(tmp_path) -> None:
    components = [
        {"component_id": "component_001", "bounding_box_3d": {"min": (0, 0, 0), "max": (1, 1, 1)}},
        {"component_id": "component_002", "bounding_box_3d": {"min": (2, 0, 0), "max": (3, 1, 1)}},
    ]
    result = GroupingResult(
        [SemanticGroup("g", "house", "house", ["component_001"], 0.4, "uncertain")], [], "fake", "local", 0.0
    )
    data = _manifest(
        tmp_path / "Room.glb",
        tmp_path / "first-house_day.webp",
        components,
        [
            {"proposal_id": "proposal_001", "component_ids": ["component_001"]},
            {"proposal_id": "proposal_002", "component_ids": ["component_002"]},
        ],
        result,
        [],
        Semantic3DConfig(),
        None,
    )
    destination = tmp_path / "semantic_objects_manifest.json"
    _write_json(destination, data)
    first = destination.read_text(encoding="utf-8")
    _write_json(destination, data)
    assert destination.read_text(encoding="utf-8") == first
    decoded = json.loads(first)
    assert [group["status"] for group in decoded["groups"]] == ["uncertain", "uncertain"]


def test_semantic_blender_script_preserves_components_without_join(tmp_path) -> None:
    script = write_semantic_objects_rebuild_script(
        tmp_path / "blender" / "semantic.py", tmp_path / "Room.glb", tmp_path / "manifest.json"
    )
    contents = script.read_text(encoding="utf-8")
    assert 'bpy.ops.mesh.separate(type="LOOSE")' in contents
    assert "component.parent = parent" in contents
    assert "bpy.ops.object.join" not in contents
    compile(contents, str(script), "exec")
