"""Asociación local y conservadora entre atlas externos y materiales glTF."""

from __future__ import annotations

import hashlib
import logging
import re
from pathlib import Path

from PIL import Image

from atlas_splitter.exceptions import GltfLoadError
from atlas_splitter.geometry.glb_loader import LoadedGltf
from atlas_splitter.geometry.texture_resolver import material_texture_bindings, read_texture_image

LOGGER = logging.getLogger(__name__)
_ORDINAL_TEXTURES = {
    "first": "first-house", "second": "second-photos", "third": "third-desk", "fourth": "fourth-extras",
    "fifth": "fifth-background", "sixth": "sixth-plants", "seventh": "seventh-large-stuff",
    "eighth": "eighth-decor", "ninth": "ninth-attachment",
}


def associate_named_external_atlases(loaded: LoadedGltf, atlas_directory: Path) -> dict[Path, set[int]]:
    """Asocia atlas sólo con evidencia y conserva el fallback ordinal histórico.

    Prioridad: textura material declarada por nombre normalizado, hash RGBA y
    dimensiones, y finalmente los nombres de las muestras. Si no hay evidencia
    suficiente, no devuelve una asociación automática.
    """
    if not atlas_directory.is_dir():
        raise GltfLoadError(f"El directorio de atlas no existe: {atlas_directory}")
    atlases = [
        path for path in atlas_directory.iterdir()
        if path.is_file() and path.suffix.lower() in {".webp", ".png", ".jpg", ".jpeg"} and ".original" not in path.stem
    ]
    images = list(getattr(loaded.document, "images", None) or [])
    declared_names = {
        _normalized_name(Path(image.uri).stem): index
        for index, image in enumerate(images)
        if isinstance(getattr(image, "uri", None), str) and not image.uri.startswith("data:")
    }
    result = {
        atlas: nodes
        for atlas in atlases
        if (image_index := declared_names.get(_normalized_name(atlas.stem))) is not None
        if (nodes := _nodes_using_image(loaded, image_index))
    }
    if result:
        LOGGER.info("Asociados %s atlas por textura declarada y nombre normalizado.", len(result))
        return result
    for atlas in atlases:
        matched = _matching_image_indices(loaded, atlas, len(images))
        nodes = set().union(*(_nodes_using_image(loaded, index) for index in matched)) if matched else set()
        if len(matched) == 1 and nodes:
            result[atlas] = nodes
    if result:
        LOGGER.info("Asociados %s atlas por hash RGBA y dimensiones.", len(result))
        return result
    legacy = {path.stem.removesuffix("_day"): path for path in atlases if path.suffix.lower() == ".webp"}
    for node_index, node in enumerate(loaded.document.nodes or []):
        ordinal = (getattr(node, "name", None) or "").lower().split("_", 1)[0]
        texture_stem = _ORDINAL_TEXTURES.get(ordinal)
        matched_atlas = legacy.get(texture_stem) if texture_stem is not None else None
        if matched_atlas is not None:
            result.setdefault(matched_atlas, set()).add(node_index)
    if result:
        LOGGER.info("Asociados %s atlas por compatibilidad ordinal heredada.", len(result))
        return result
    raise GltfLoadError(
        "No fue posible asociar atlas de forma confiable. Selecciona un nodo/atlas manualmente "
        "o usa el modo sin geometría."
    )


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


def _nodes_using_image(loaded: LoadedGltf, image_index: int) -> set[int]:
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
                binding.image_index == image_index for binding in material_texture_bindings(loaded, material_index)
            ):
                nodes.add(node_index)
    return nodes


def _normalized_name(value: str) -> str:
    cleaned = re.sub(r"(?:_day|_baked)$", "", value.lower())
    return re.sub(r"[^a-z0-9]+", "", cleaned)
