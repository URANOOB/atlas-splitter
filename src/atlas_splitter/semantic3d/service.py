"""Primera fase: First_House_Baked a objetos semánticos editables."""

from __future__ import annotations

import json
import logging
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, cast

import numpy as np
from PIL import Image

from atlas_splitter.blender.script_writer import write_semantic_objects_rebuild_script
from atlas_splitter.exceptions import GltfLoadError
from atlas_splitter.geometry.glb_loader import load_gltf
from atlas_splitter.geometry.primitive_decoder import decode_scene_primitives
from atlas_splitter.geometry.texture_resolver import material_texture_bindings
from atlas_splitter.geometry.types import DecodedPrimitive
from atlas_splitter.geometry.uv_rasterizer import rasterize_uv_triangles
from atlas_splitter.reporting.semantic_contact_sheet import write_semantic_contact_sheet
from atlas_splitter.semantic.prompt_builder import build_grouping_prompt
from atlas_splitter.semantic.types import GroupingContext, GroupingResult, PieceReference
from atlas_splitter.semantic3d.topology import bounding_box_3d, bounding_box_distance, mesh_connected_components

LOGGER = logging.getLogger(__name__)
_NODE_NAME = "First_House_Baked"


class GroupingBackend(Protocol):
    runtime_device: str

    def group(self, context: GroupingContext) -> GroupingResult: ...


@dataclass(frozen=True, slots=True)
class Semantic3DConfig:
    """Parámetros explícitos y conservadores del agrupamiento semántico 3D."""

    minimum_confidence: float = 0.70
    proximity_factor: float = 0.08
    flip_v: bool = True
    texture_index: int | None = None
    uv_set: int = 0


def group_first_house(
    model_path: Path,
    atlas_path: Path,
    output_root: Path,
    backend: GroupingBackend,
    config: Semantic3DConfig | None = None,
) -> Path:
    """Alias heredado para el nodo ``First_House_Baked``.

    No modifica el GLB ni une geometría: sólo registra componentes y genera un
    script Blender que los separa de nuevo como objetos editables.
    """
    LOGGER.warning("group_first_house está deprecado; use group_semantic_3d con un selector --node explícito.")
    return group_semantic_3d(model_path, atlas_path, output_root, backend, config, node_name=_NODE_NAME)


def group_semantic_3d(
    model_path: Path,
    atlas_path: Path,
    output_root: Path,
    backend: GroupingBackend,
    config: Semantic3DConfig | None = None,
    *,
    node_name: str | None = None,
    node_index: int | None = None,
    mesh_index: int | None = None,
) -> Path:
    """Agrupa un nodo UV explícito sin depender de nombres de ejemplo.

    Si hay más de un candidato, exige ``--node`` o ``--mesh-index``; el atlas
    suministrado por la persona usuaria se registra como una selección manual.
    """
    effective_config = config or Semantic3DConfig()
    loaded = load_gltf(model_path)
    if not atlas_path.is_file():
        raise GltfLoadError(f"No existe el atlas local: {atlas_path}")
    if effective_config.uv_set < 0:
        raise GltfLoadError("uv_set debe ser un entero mayor o igual a cero.")
    if effective_config.proximity_factor < 0:
        raise GltfLoadError("proximity_factor no puede ser negativo.")
    candidates = [item for item in decode_scene_primitives(loaded) if effective_config.uv_set in item.texcoords]
    if node_index is not None:
        candidates = [item for item in candidates if item.reference.node_index == node_index]
    if mesh_index is not None:
        candidates = [item for item in candidates if item.reference.mesh_index == mesh_index]
    if node_name is not None:
        candidates = [item for item in candidates if item.node_path and item.node_path[-1] == node_name]
    if effective_config.texture_index is not None:
        candidates = [
            item for item in candidates if _primitive_uses_texture(loaded, item, effective_config.texture_index)
        ]
    node_ids = sorted({item.reference.node_index for item in candidates})
    if not candidates:
        raise GltfLoadError("No se encontró una primitiva que coincida con los selectores de nodo, textura y UV.")
    if len(node_ids) > 1:
        raise GltfLoadError(
            "Hay varios nodos con UV compatibles. Use --node o --mesh-index para seleccionar uno explícitamente."
        )
    destination = output_root.resolve() / atlas_path.stem / "semantic_objects"
    if destination.exists():
        raise FileExistsError(f"La salida semántica ya existe y no se sobrescribirá: {destination}")
    destination.mkdir(parents=True)
    try:
        with Image.open(atlas_path) as image:
            atlas = image.convert("RGBA")
        components, _ = _write_components_for_primitives(destination, candidates, atlas, effective_config)
        proximity_edges = _proximity_proposals(components, effective_config.proximity_factor)
        proposals, pieces = _write_proposals(destination, atlas, components, proximity_edges)
        sheet = destination / "contact_sheets" / "proposals.png"
        sheet.parent.mkdir(parents=True)
        write_semantic_contact_sheet(sheet, pieces)
        context = GroupingContext(pieces, sheet, [sheet], _prompt_with_geometry(proposals))
        inference_error: str | None
        try:
            result = backend.group(context)
        except Exception as error:
            LOGGER.exception("La inferencia local falló; se conservarán grupos inciertos.")
            result = GroupingResult([], [piece.piece_id for piece in pieces], "qwen3-vl", "qwen3-vl-2b", 0.0)
            inference_error = str(error)
        else:
            inference_error = None
        manifest = _manifest(
            loaded.source_path,
            atlas_path,
            components,
            proposals,
            result,
            proximity_edges,
            effective_config,
            inference_error,
            candidates,
        )
        _write_group_previews(destination, manifest, atlas)
        _write_json(destination / "semantic_objects_manifest.json", manifest)
        write_semantic_objects_rebuild_script(
            destination / "blender" / "rebuild_semantic_objects.py",
            loaded.source_path,
            destination / "semantic_objects_manifest.json",
        )
    except (Exception, KeyboardInterrupt):
        shutil.rmtree(destination, ignore_errors=True)
        raise
    return destination


def _write_components_for_primitives(
    destination: Path, primitives: list[DecodedPrimitive], atlas: Image.Image, config: Semantic3DConfig
) -> tuple[list[dict[str, object]], list[PieceReference]]:
    """Conserva componentes por primitiva, incluso cuando un nodo tiene varias."""
    components: list[dict[str, object]] = []
    pieces: list[PieceReference] = []
    for primitive in primitives:
        primitive_components, primitive_pieces = _write_components(
            destination,
            primitive,
            atlas,
            flip_v=config.flip_v,
            uv_set=config.uv_set,
        )
        components.extend(primitive_components)
        pieces.extend(primitive_pieces)
    return components, pieces


def _write_components(
    destination: Path, primitive: DecodedPrimitive, atlas: Image.Image, *, flip_v: bool, uv_set: int
) -> tuple[list[dict[str, object]], list[PieceReference]]:
    positions = np.asarray(primitive.positions, dtype=np.float64)
    triangles = np.asarray(primitive.triangle_indices, dtype=np.int64)
    uvs = _external_atlas_uvs(np.asarray(primitive.texcoords[uv_set], dtype=np.float64), flip_v)
    transform = np.asarray(primitive.node_transform, dtype=np.float64)
    atlas_pixels = np.asarray(atlas)
    homogeneous = np.column_stack((positions, np.ones(len(positions))))
    world_positions = (transform @ homogeneous.T).T[:, :3]
    components: list[dict[str, object]] = []
    pieces: list[PieceReference] = []
    for part in mesh_connected_components(triangles):
        component_id = f"primitive_{primitive.reference.primitive_index:03d}_component_{part.component_index:03d}"
        component_triangles = triangles[part.triangle_rows]
        region = rasterize_uv_triangles(uvs, component_triangles, atlas.width, atlas.height)
        component_dir = destination / "components" / component_id
        component_dir.mkdir(parents=True)
        mask_path = component_dir / "uv_mask.png"
        crop_path = component_dir / "uv_crop.png"
        x, y, width, height = region.bounding_box
        local_mask = region.mask[y : y + height, x : x + width]
        Image.fromarray((local_mask * 255).astype(np.uint8), "L").save(mask_path)
        pixels = atlas_pixels[y : y + height, x : x + width].copy()
        pixels[:, :, 3] = np.where(local_mask, pixels[:, :, 3], 0)
        Image.fromarray(pixels, "RGBA").save(crop_path)
        bbox = bounding_box_3d(world_positions[part.vertex_indices])
        components.append(
            {
                "component_id": component_id,
                "source_primitive": {
                    "node_index": primitive.reference.node_index,
                    "mesh_index": primitive.reference.mesh_index,
                    "primitive_index": primitive.reference.primitive_index,
                    "uv_set": uv_set,
                },
                "geometry_evidence": "exact",
                "triangle_rows": part.triangle_rows.tolist(),
                "vertex_indices": part.vertex_indices.tolist(),
                "triangle_count": int(len(part.triangle_rows)),
                "bounding_box_3d": {"min": bbox[0], "max": bbox[1]},
                "bounding_box_uv": {"x": x, "y": y, "width": width, "height": height},
                "uv_mask": str(mask_path.relative_to(destination).as_posix()),
                "uv_crop": str(crop_path.relative_to(destination).as_posix()),
            }
        )
        pieces.append(
            PieceReference(
                component_id,
                part.component_index,
                crop_path,
                mask_path,
                None,
                (x, y, width, height),
                int(region.mask.sum()),
                "uv_component",
            )
        )
    return components, pieces


def _external_atlas_uvs(uvs: np.ndarray, flip_v: bool) -> np.ndarray:
    """Convierte UV glTF al origen superior del atlas WEBP externo cuando procede."""
    if not flip_v:
        return uvs
    transformed = uvs.copy()
    transformed[:, 1] = 1.0 - transformed[:, 1]
    return transformed


def _primitive_uses_texture(loaded: Any, primitive: DecodedPrimitive, texture_index: int) -> bool:
    """Comprueba la textura declarada sin inferir asociaciones por nombre."""
    material_index = primitive.reference.material_index
    if material_index is None:
        return False
    return any(binding.texture_index == texture_index for binding in material_texture_bindings(loaded, material_index))


def _proximity_proposals(components: list[dict[str, object]], factor: float) -> list[dict[str, object]]:
    boxes = [cast(dict[str, Any], item["bounding_box_3d"]) for item in components]
    diagonal = max((np.linalg.norm(np.asarray(box["max"]) - np.asarray(box["min"])) for box in boxes), default=1.0)
    threshold = max(diagonal * factor, 1e-6)
    proposals: list[dict[str, object]] = []
    for first in range(len(components)):
        for second in range(first + 1, len(components)):
            a, b = boxes[first], boxes[second]
            distance = bounding_box_distance((tuple(a["min"]), tuple(a["max"])), (tuple(b["min"]), tuple(b["max"])))
            if distance <= threshold:
                proposals.append(
                    {
                        "components": [components[first]["component_id"], components[second]["component_id"]],
                        "distance": round(distance, 8),
                    }
                )
    return proposals


def _write_proposals(
    destination: Path,
    atlas: Image.Image,
    components: list[dict[str, object]],
    edges: list[dict[str, object]],
) -> tuple[list[dict[str, object]], list[PieceReference]]:
    """Une por proximidad propuestas de objeto, sin fusionar mallas originales."""
    component_ids = [str(item["component_id"]) for item in components]
    parent = {component_id: component_id for component_id in component_ids}

    def find(item: str) -> str:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(first: str, second: str) -> None:
        first_root, second_root = find(first), find(second)
        if first_root != second_root:
            parent[second_root] = first_root

    for edge in edges:
        first, second = cast(list[str], edge["components"])
        union(first, second)
    members_by_root: dict[str, list[str]] = {}
    for component_id in component_ids:
        members_by_root.setdefault(find(component_id), []).append(component_id)
    by_id = {str(item["component_id"]): item for item in components}
    proposals: list[dict[str, object]] = []
    pieces: list[PieceReference] = []
    for index, members in enumerate(sorted(members_by_root.values(), key=lambda item: item[0]), start=1):
        proposal_id = f"proposal_{index:03d}"
        mask = np.zeros((atlas.height, atlas.width), dtype=bool)
        for component_id in members:
            component = by_id[component_id]
            box = cast(dict[str, int], component["bounding_box_uv"])
            with Image.open(destination / str(component["uv_mask"])) as source:
                local_mask = np.asarray(source.convert("L"), dtype=np.uint8) > 0
            y, x = box["y"], box["x"]
            mask[y : y + box["height"], x : x + box["width"]] |= local_mask
        active_y, active_x = np.nonzero(mask)
        x, y = int(active_x.min()), int(active_y.min())
        width, height = int(active_x.max()) - x + 1, int(active_y.max()) - y + 1
        proposal_dir = destination / "proposals" / proposal_id
        proposal_dir.mkdir(parents=True)
        mask_path, crop_path = proposal_dir / "uv_mask.png", proposal_dir / "uv_crop.png"
        Image.fromarray((mask * 255).astype(np.uint8), "L").save(mask_path)
        pixels = np.asarray(atlas).copy()
        pixels[:, :, 3] = np.where(mask, pixels[:, :, 3], 0)
        Image.fromarray(pixels[y : y + height, x : x + width], "RGBA").save(crop_path)
        proposals.append(
            {
                "proposal_id": proposal_id,
                "component_ids": members,
                "bounding_box_uv": {"x": x, "y": y, "width": width, "height": height},
                "uv_mask": str(mask_path.relative_to(destination).as_posix()),
                "uv_crop": str(crop_path.relative_to(destination).as_posix()),
            }
        )
        pieces.append(
            PieceReference(
                proposal_id, index, crop_path, mask_path, None, (x, y, width, height), int(mask.sum()), "proximity_3d"
            )
        )
    return proposals, pieces


def _prompt_with_geometry(proposals: list[dict[str, object]]) -> str:
    ids = [str(item["proposal_id"]) for item in proposals]
    return f"""{build_grouping_prompt()}

Each ID below is already a 3D proximity object proposal, made from disconnected mesh components
and an exact combined UV mask.
Label each proposal from its texture and shape. Do not split it into its components and do not group proposals together.
Every proposal ID must appear exactly once in a one-ID group or in unassigned_piece_ids: {json.dumps(ids)}.
Use unknown_object and unassigned when the visual evidence is insufficient."""


def _manifest(
    source: Path,
    atlas: Path,
    components: list[dict[str, object]],
    proposals: list[dict[str, object]],
    result: GroupingResult,
    proximity_edges: list[dict[str, object]],
    config: Semantic3DConfig,
    inference_error: str | None,
    primitives: list[DecodedPrimitive] | None = None,
) -> dict[str, object]:
    known = {str(item["proposal_id"]): item for item in proposals}
    groups: list[dict[str, object]] = []
    assigned: set[str] = set()
    for index, group in enumerate(sorted(result.groups, key=lambda item: item.group_id), start=1):
        members = sorted(piece_id for piece_id in group.piece_ids if piece_id in known)
        if len(members) != 1 or any(piece_id in assigned for piece_id in members):
            continue
        assigned.update(members)
        accepted = group.confidence >= config.minimum_confidence and group.status == "accepted"
        status = "accepted" if accepted else "uncertain"
        component_ids = sorted(
            component for proposal_id in members for component in cast(list[str], known[proposal_id]["component_ids"])
        )
        groups.append(_group_record(index, group.name, component_ids, group.confidence, status, proximity_edges))
    for proposal_id in sorted(set(known) - assigned):
        component_ids = cast(list[str], known[proposal_id]["component_ids"])
        groups.append(
            _group_record(len(groups) + 1, "unknown_object", component_ids, 0.0, "uncertain", proximity_edges)
        )
    return {
        "schema_version": "1.0",
        "phase": "semantic_3d",
        "source_file": str(source.resolve()),
        "atlas_file": str(atlas.resolve()),
        "node": {
            "name": (primitives[0].node_path[-1] if primitives and primitives[0].node_path else _NODE_NAME),
            "node_index": primitives[0].reference.node_index if primitives else 0,
            "mesh_index": primitives[0].reference.mesh_index if primitives else None,
            "uv_set": config.uv_set,
            "association_method": "manual_explicit_atlas",
        },
        "source_primitives": [
            {
                "node_index": item.reference.node_index,
                "mesh_index": item.reference.mesh_index,
                "primitive_index": item.reference.primitive_index,
            }
            for item in primitives or []
        ],
        "components": components,
        "proximity_objects": proposals,
        "groups": groups,
        "proximity_edges": proximity_edges,
        "backend": {"name": result.backend, "model": result.model, "device": "local"},
        "parameters": {
            "minimum_confidence": config.minimum_confidence,
            "proximity_factor": config.proximity_factor,
            "flip_v": config.flip_v,
            "texture_index": config.texture_index,
            "uv_set": config.uv_set,
        },
        "evidence": {
            "geometry_components": "exact",
            "proximity_proposals": "exact_geometry",
            "semantic_group_names": "semantic_inference",
        },
        "inference_error": inference_error,
        "non_destructive": True,
    }


def _group_record(
    index: int, name: str, members: list[str], confidence: float, status: str, proposals: list[dict[str, object]]
) -> dict[str, object]:
    safe_name = "".join(char if char.isalnum() or char == "_" else "_" for char in name.lower()).strip("_")
    safe_name = safe_name or "unknown_object"
    nearby = [item for item in proposals if set(cast(list[str], item["components"])).issubset(members)]
    reason = "evidencia visual local Qwen3-VL; " if confidence else "sin etiqueta visual suficiente; "
    reason += (
        "componentes cercanos en 3D y compatibles"
        if nearby
        else "componente conservado sin unión por evidencia insuficiente"
    )
    return {
        "group_id": f"semantic_{index:03d}_{safe_name}",
        "name": safe_name,
        "component_ids": members,
        "confidence": round(float(confidence), 4),
        "status": status,
        "reason": reason,
        "geometry_evidence": "exact",
        "semantic_evidence": "inference" if confidence else "none",
    }


def _write_group_previews(destination: Path, manifest: dict[str, object], atlas: Image.Image) -> None:
    del atlas
    component_records = cast(list[dict[str, Any]], manifest["components"])
    group_records = cast(list[dict[str, Any]], manifest["groups"])
    components = {str(item["component_id"]): item for item in component_records}
    for group in group_records:
        images: list[Image.Image] = []
        for component_id in cast(list[str], group["component_ids"]):
            with Image.open(destination / str(components[component_id]["uv_crop"])) as crop:
                images.append(crop.convert("RGBA"))
        width = sum(image.width for image in images)
        preview = Image.new("RGBA", (max(width, 1), max((image.height for image in images), default=1)), (0, 0, 0, 0))
        cursor = 0
        for image in images:
            preview.alpha_composite(image, (cursor, 0))
            cursor += image.width
        path = destination / "previews" / f"{group['group_id']}.png"
        path.parent.mkdir(exist_ok=True)
        preview.save(path)


def _write_json(destination: Path, data: dict[str, object]) -> None:
    temporary = destination.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    temporary.replace(destination)
