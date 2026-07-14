"""Inspección local y serializable de modelos glTF y GLB."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from atlas_splitter.geometry.glb_loader import LoadedGltf


class ModelCandidate(BaseModel):
    """Nodo con geometría que puede seleccionarse como objetivo de extracción."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    node_index: int = Field(ge=0)
    node_name: str = Field(min_length=1)
    mesh_index: int = Field(ge=0)
    primitive_count: int = Field(ge=0)
    material_names: list[str] = Field(default_factory=list)
    uv_sets: list[str] = Field(default_factory=list)


class ModelInspection(BaseModel):
    """Resumen completo, sin efectos laterales, de un archivo de modelo local."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    file: str = Field(min_length=1)
    nodes: int = Field(ge=0)
    meshes: int = Field(ge=0)
    primitives: int = Field(ge=0)
    materials: int = Field(ge=0)
    textures: int = Field(ge=0)
    uv_sets: list[str] = Field(default_factory=list)
    animations: int = Field(ge=0)
    draco_compression: bool
    candidates: list[ModelCandidate] = Field(default_factory=list)


def inspect_model(loaded: LoadedGltf) -> ModelInspection:
    """Describe nodos, materiales, UVs y compresión sin modificar el modelo."""
    document = loaded.document
    meshes = list(document.meshes or [])
    materials = list(document.materials or [])
    all_uv_sets: set[str] = set()
    primitive_count = 0
    for mesh in meshes:
        for primitive in mesh.primitives or []:
            primitive_count += 1
            all_uv_sets.update(_uv_sets(primitive))
    candidates: list[ModelCandidate] = []
    for node_index, node in enumerate(document.nodes or []):
        mesh_index = getattr(node, "mesh", None)
        if not isinstance(mesh_index, int) or mesh_index < 0 or mesh_index >= len(meshes):
            continue
        primitives = list(meshes[mesh_index].primitives or [])
        material_names = sorted(
            {
                _material_name(materials, getattr(primitive, "material", None))
                for primitive in primitives
                if getattr(primitive, "material", None) is not None
            }
        )
        uv_sets = sorted({uv_set for primitive in primitives for uv_set in _uv_sets(primitive)})
        candidates.append(
            ModelCandidate(
                node_index=node_index,
                node_name=str(getattr(node, "name", None) or f"node_{node_index}"),
                mesh_index=mesh_index,
                primitive_count=len(primitives),
                material_names=material_names,
                uv_sets=uv_sets,
            )
        )
    return ModelInspection(
        file=str(loaded.source_path),
        nodes=len(document.nodes or []),
        meshes=len(meshes),
        primitives=primitive_count,
        materials=len(materials),
        textures=len(document.textures or []),
        uv_sets=sorted(all_uv_sets),
        animations=len(document.animations or []),
        draco_compression=any(item.extension == "KHR_draco_mesh_compression" for item in loaded.diagnostics),
        candidates=candidates,
    )


def _uv_sets(primitive: object) -> set[str]:
    attributes = getattr(primitive, "attributes", None)
    if isinstance(attributes, dict):
        values = attributes.items()
    else:
        values = vars(attributes).items() if attributes is not None else []
    return {
        str(name)
        for name, value in values
        if str(name).startswith("TEXCOORD_") and value is not None
    }


def _material_name(materials: list[object], index: object) -> str:
    if not isinstance(index, int) or index < 0 or index >= len(materials):
        return f"material_{index}"
    return str(getattr(materials[index], "name", None) or f"material_{index}")
