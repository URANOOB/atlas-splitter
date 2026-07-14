"""Asociacion local, conservadora y auditable entre atlas externos y glTF."""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml
from PIL import Image

from atlas_splitter.exceptions import GltfLoadError
from atlas_splitter.geometry.glb_loader import LoadedGltf
from atlas_splitter.geometry.texture_resolver import material_texture_bindings, read_texture_image

LOGGER = logging.getLogger(__name__)
AssociationMethod = Literal["yaml", "image_hash", "normalized_name", "legacy_name"]
_ORDINAL_TEXTURES = {
    "first": "first-house", "second": "second-photos", "third": "third-desk", "fourth": "fourth-extras",
    "fifth": "fifth-background", "sixth": "sixth-plants", "seventh": "seventh-large-stuff",
    "eighth": "eighth-decor", "ninth": "ninth-attachment",
}
_ATLAS_SUFFIXES = {".webp", ".png", ".jpg", ".jpeg"}


@dataclass(frozen=True)
class AtlasAssociation:
    """Una asociacion confirmada y suficiente para ejecutar una exportacion."""

    atlas_path: Path
    node_indices: frozenset[int]
    method: AssociationMethod
    confidence: float
    uv_set: int | None = None
    flip_v: bool = False
    manual_confirmation: bool = False
    texture_slot: str = "baseColor"
    image_index: int | None = None


def load_atlas_bindings(bindings_file: Path, loaded: LoadedGltf) -> list[AtlasAssociation]:
    """Carga bindings YAML explicitos sin aceptar rutas o nodos dudosos."""
    try:
        data = yaml.safe_load(bindings_file.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise GltfLoadError(f"No se pudo leer el YAML de bindings '{bindings_file}': {error}") from error
    if (
        not isinstance(data, dict)
        or set(data) - {"version", "atlas_bindings"}
        or data.get("version", 1) != 1
        or not isinstance(data.get("atlas_bindings"), list)
    ):
        raise GltfLoadError("El YAML debe contener version: 1 y 'atlas_bindings: [...]'.")
    associations: list[AtlasAssociation] = []
    seen_atlases: set[Path] = set()
    for position, item in enumerate(data["atlas_bindings"], start=1):
        if not isinstance(item, dict) or not {"atlas", "nodes"} <= set(item) or set(item) - {
            "atlas", "nodes", "texture_slot", "uv_set", "flip_v"
        }:
            raise GltfLoadError(f"Binding YAML #{position} debe incluir atlas y nodes; revise sus claves.")
        atlas_value, nodes_value = item["atlas"], item["nodes"]
        if not isinstance(atlas_value, str) or not isinstance(nodes_value, list) or not nodes_value:
            raise GltfLoadError(f"Binding YAML #{position} requiere atlas textual y nodes no vacio.")
        atlas = Path(atlas_value).expanduser()
        atlas = (bindings_file.parent / atlas).resolve() if not atlas.is_absolute() else atlas.resolve()
        if not atlas.is_file() or atlas.suffix.lower() not in _ATLAS_SUFFIXES:
            raise GltfLoadError(f"El atlas del binding YAML #{position} no es una imagen local valida: {atlas}")
        if atlas in seen_atlases:
            raise GltfLoadError(f"El atlas '{atlas.name}' aparece mas de una vez en los bindings YAML.")
        seen_atlases.add(atlas)
        uv_set = item.get("uv_set")
        if isinstance(uv_set, bool) or not isinstance(uv_set, int) or uv_set < 0:
            raise GltfLoadError(f"Binding YAML #{position}: uv_set debe ser un entero mayor o igual a cero.")
        flip_v = item.get("flip_v", False)
        if not isinstance(flip_v, bool):
            raise GltfLoadError(f"Binding YAML #{position}: flip_v debe ser true o false.")
        texture_slot = item.get("texture_slot", "baseColor")
        if texture_slot not in {"baseColor", "normal", "metallicRoughness", "occlusion", "emissive"}:
            raise GltfLoadError(f"Binding YAML #{position}: texture_slot no es válido.")
        associations.append(
            AtlasAssociation(
                atlas,
                frozenset(_resolve_nodes(loaded, nodes_value)),
                "yaml",
                1.0,
                uv_set,
                flip_v,
                True,
                texture_slot,
            )
        )
    if not associations:
        raise GltfLoadError("El YAML no contiene bindings de atlas.")
    return associations


def resolve_external_atlases(
    loaded: LoadedGltf, atlas_directory: Path, texture_slot: str = "baseColor"
) -> list[AtlasAssociation]:
    """Resuelve asociaciones automaticas solo cuando cada evidencia es unica."""
    if not atlas_directory.is_dir():
        raise GltfLoadError(f"El directorio de atlas no existe: {atlas_directory}")
    atlases = sorted(
        path.resolve() for path in atlas_directory.iterdir()
        if path.is_file() and path.suffix.lower() in _ATLAS_SUFFIXES and ".original" not in path.stem
    )
    if not atlases:
        raise GltfLoadError(f"No hay atlas de imagen compatibles en: {atlas_directory}")
    if texture_slot not in {"baseColor", "normal", "metallicRoughness", "occlusion", "emissive"}:
        raise GltfLoadError(f"texture_slot no es válido: {texture_slot}")
    by_hash = _associations_by_hash(loaded, atlases, texture_slot)
    unresolved = [atlas for atlas in atlases if atlas not in {item.atlas_path for item in by_hash}]
    by_name = _associations_by_name(loaded, unresolved, texture_slot, {item.image_index for item in by_hash})
    associations = [*by_hash, *by_name]
    if associations:
        return associations
    raise GltfLoadError(
        "No fue posible asociar atlas de forma confiable. Usa --bindings con atlas, nodes, uv_set y flip_v "
        "para confirmar la asociacion manualmente."
    )


def associate_named_external_atlases(loaded: LoadedGltf, atlas_directory: Path) -> dict[Path, set[int]]:
    """API heredada para el ejemplo ordinal; la CLI nunca recurre a ella."""
    try:
        associations = resolve_external_atlases(loaded, atlas_directory)
    except GltfLoadError:
        atlases = sorted(
            path.resolve()
            for path in atlas_directory.iterdir()
            if path.is_file() and path.suffix.lower() in _ATLAS_SUFFIXES and ".original" not in path.stem
        )
        associations = _legacy_associations(loaded, atlases)
        if not associations:
            raise
        LOGGER.warning("associate_named_external_atlases está deprecado; use bindings YAML o material/hash.")
    return {association.atlas_path: set(association.node_indices) for association in associations}


def _associations_by_name(
    loaded: LoadedGltf, atlases: list[Path], texture_slot: str, used_images: set[int | None]
) -> list[AtlasAssociation]:
    images = list(getattr(loaded.document, "images", None) or [])
    declared: dict[str, list[int]] = {}
    for index, image in enumerate(images):
        uri = getattr(image, "uri", None)
        if isinstance(uri, str) and not uri.startswith("data:"):
            declared.setdefault(_normalized_name(Path(uri).stem), []).append(index)
    associations: list[AtlasAssociation] = []
    for atlas in atlases:
        image_indices = declared.get(_normalized_name(atlas.stem), [])
        if len(image_indices) > 1:
            raise GltfLoadError(_ambiguity_message(atlas, "nombre de textura", image_indices))
        if len(image_indices) == 1:
            image_index = image_indices[0]
            if image_index in used_images:
                raise GltfLoadError(_ambiguity_message(atlas, "nombre normalizado", image_indices))
            nodes = _nodes_using_image(loaded, image_index, texture_slot)
            if nodes:
                associations.append(
                    AtlasAssociation(
                        atlas,
                        frozenset(nodes),
                        "normalized_name",
                        0.70,
                        texture_slot=texture_slot,
                        image_index=image_index,
                    )
                )
    if associations:
        LOGGER.info("Asociados %s atlas por nombre de textura material.", len(associations))
    return associations


def _associations_by_hash(loaded: LoadedGltf, atlases: list[Path], texture_slot: str) -> list[AtlasAssociation]:
    associations: list[AtlasAssociation] = []
    used_images: set[int] = set()
    image_count = len(getattr(loaded.document, "images", None) or [])
    for atlas in atlases:
        matched = _matching_image_indices(loaded, atlas, image_count)
        if len(matched) > 1:
            raise GltfLoadError(_ambiguity_message(atlas, "hash y dimensiones", matched))
        if len(matched) == 1:
            image_index = matched[0]
            if image_index in used_images:
                raise GltfLoadError(_ambiguity_message(atlas, "hash y dimensiones", matched))
            nodes = _nodes_using_image(loaded, image_index, texture_slot)
            if nodes:
                used_images.add(image_index)
                associations.append(
                    AtlasAssociation(
                        atlas,
                        frozenset(nodes),
                        "image_hash",
                        0.99,
                        texture_slot=texture_slot,
                        image_index=image_index,
                    )
                )
    if associations:
        LOGGER.info("Asociados %s atlas por hash RGBA y dimensiones.", len(associations))
    return associations


def _legacy_associations(loaded: LoadedGltf, atlases: list[Path]) -> list[AtlasAssociation]:
    legacy = {path.stem.removesuffix("_day"): path for path in atlases if path.suffix.lower() == ".webp"}
    found: dict[Path, set[int]] = {}
    for node_index, node in enumerate(loaded.document.nodes or []):
        ordinal = (getattr(node, "name", None) or "").lower().split("_", 1)[0]
        atlas = legacy.get(_ORDINAL_TEXTURES.get(ordinal, ""))
        if atlas is not None:
            found.setdefault(atlas, set()).add(node_index)
    if found:
        LOGGER.info("Asociados %s atlas por compatibilidad ordinal heredada.", len(found))
    return [AtlasAssociation(path, frozenset(nodes), "legacy_name", 0.50) for path, nodes in sorted(found.items())]


def _resolve_nodes(loaded: LoadedGltf, requested: list[Any]) -> list[int]:
    names: dict[str, list[int]] = {}
    for index, node in enumerate(loaded.document.nodes or []):
        if isinstance(getattr(node, "name", None), str):
            names.setdefault(node.name, []).append(index)
    indices: list[int] = []
    for value in requested:
        if isinstance(value, bool):
            raise GltfLoadError("Los nodos YAML deben ser indices enteros o nombres exactos.")
        if isinstance(value, int):
            if value < 0 or value >= len(loaded.document.nodes or []):
                raise GltfLoadError(f"El nodo YAML {value} no existe.")
            indices.append(value)
        elif isinstance(value, str):
            matches = names.get(value, [])
            if len(matches) != 1:
                suffix = "no existe" if not matches else f"es ambiguo: {matches}"
                raise GltfLoadError(f"El nombre de nodo YAML '{value}' {suffix}; usa su indice.")
            indices.append(matches[0])
        else:
            raise GltfLoadError("Los nodos YAML deben ser indices enteros o nombres exactos.")
    return sorted(set(indices))


def _matching_image_indices(loaded: LoadedGltf, atlas: Path, image_count: int) -> list[int]:
    try:
        with Image.open(atlas) as source:
            candidate = source.convert("RGBA")
    except (OSError, ValueError):
        return []
    digest = hashlib.sha256(candidate.tobytes()).digest()
    matches: list[int] = []
    for image_index in range(image_count):
        try:
            declared = read_texture_image(loaded, image_index)
        except GltfLoadError:
            continue
        if declared.size == candidate.size and hashlib.sha256(declared.tobytes()).digest() == digest:
            matches.append(image_index)
    return matches


def _nodes_using_image(loaded: LoadedGltf, image_index: int, texture_slot: str | None = None) -> set[int]:
    nodes: set[int] = set()
    for node_index, node in enumerate(loaded.document.nodes or []):
        mesh_index = getattr(node, "mesh", None)
        if mesh_index is None:
            continue
        try:
            primitives = loaded.document.meshes[mesh_index].primitives
        except (IndexError, TypeError):
            continue
        for primitive in primitives:
            material_index = getattr(primitive, "material", None)
            if material_index is not None and any(
                binding.image_index == image_index and (texture_slot is None or binding.slot == texture_slot)
                for binding in material_texture_bindings(loaded, material_index)
            ):
                nodes.add(node_index)
    return nodes


def _ambiguity_message(atlas: Path, method: str, alternatives: list[int]) -> str:
    values = ", ".join(str(value) for value in alternatives)
    return (
        f"El atlas '{atlas.name}' tiene una asociacion ambigua por {method}: imagenes [{values}]. "
        "No se exporto nada. Crea un --bindings YAML con el atlas y los indices de nodo deseados."
    )


def _normalized_name(value: str) -> str:
    cleaned = value.lower()
    while True:
        simplified = re.sub(r"(?:[_\-\s](?:day|night|diffuse|base_?color|baked))$", "", cleaned)
        if simplified == cleaned:
            break
        cleaned = simplified
    return re.sub(r"[^a-z0-9]+", "", cleaned)
