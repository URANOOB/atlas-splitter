from pathlib import Path
from types import SimpleNamespace

from atlas_splitter.geometry.glb_loader import GltfDiagnostic, LoadedGltf
from atlas_splitter.geometry.model_inspector import inspect_model


def test_inspect_model_reports_generic_scene_contents() -> None:
    document = SimpleNamespace(
        nodes=[SimpleNamespace(name="House", mesh=0), SimpleNamespace(name="Light", mesh=None)],
        meshes=[
            SimpleNamespace(
                primitives=[
                    SimpleNamespace(attributes=SimpleNamespace(TEXCOORD_0=1, TEXCOORD_1=2), material=0),
                    SimpleNamespace(attributes=SimpleNamespace(TEXCOORD_0=1), material=1),
                ]
            )
        ],
        materials=[SimpleNamespace(name="Wall"), SimpleNamespace(name="Roof")],
        textures=[SimpleNamespace(), SimpleNamespace()],
        animations=[SimpleNamespace()],
    )
    loaded = LoadedGltf(
        document=document,
        source_path=Path("model.glb"),
        resource_directory=Path("."),
        diagnostics=(GltfDiagnostic("draco", "warning", "", "KHR_draco_mesh_compression"),),
    )

    inspection = inspect_model(loaded)

    assert inspection.model_dump() == {
        "file": "model.glb",
        "nodes": 2,
        "meshes": 1,
        "primitives": 2,
        "materials": 2,
        "textures": 2,
        "uv_sets": ["TEXCOORD_0", "TEXCOORD_1"],
        "animations": 1,
        "draco_compression": True,
        "candidates": [
            {
                "node_index": 0,
                "node_name": "House",
                "mesh_index": 0,
                "primitive_count": 2,
                "material_names": ["Roof", "Wall"],
                "uv_sets": ["TEXCOORD_0", "TEXCOORD_1"],
            }
        ],
    }
