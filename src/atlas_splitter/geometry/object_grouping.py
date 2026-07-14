"""Agrupación de regiones UV por nodo GLB para la reconstrucción editable."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path

from atlas_splitter.domain import (
    AtlasCapabilities,
    AtlasElement,
    ObjectGroup,
    ObjectManifest,
    ObjectTexturePart,
    UvManifest,
    write_versioned_manifest,
)

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExportedAtlas:
    """Un atlas ya exportado junto con los nodos que cubre."""

    atlas_path: Path
    output_directory: Path
    manifest: UvManifest
    flip_v: bool


def write_object_manifest(destination: Path, source_glb: Path, atlases: list[ExportedAtlas]) -> ObjectManifest:
    """Crea un manifiesto determinista que preserva las piezas por nodo, no las aplana."""
    grouped: dict[int, list[tuple[ExportedAtlas, AtlasElement]]] = {}
    for atlas in atlases:
        for element in atlas.manifest.elements:
            grouped.setdefault(element.node_index, []).append((atlas, element))
    objects: list[ObjectGroup] = []
    for node_index, entries in sorted(grouped.items()):
        first_atlas, first_element = entries[0]
        atlas_paths = {str(atlas.atlas_path.resolve()) for atlas, _ in entries}
        if len(atlas_paths) != 1:
            raise ValueError(f"El nodo {node_index} usa más de un atlas externo; requiere una política explícita.")
        node_name = first_element.node_path[-1] if first_element.node_path else f"node_{node_index}"
        object_id = f"object_{hashlib.sha256(f'{node_index}:{node_name}'.encode()).hexdigest()[:16]}"
        parts = [
            ObjectTexturePart(
                element_id=element.element_id,
                atlas_directory=atlas.output_directory.name,
                exported_files=element.exported_files,
            )
            for atlas, element in entries
        ]
        objects.append(
            ObjectGroup(
                object_id=object_id,
                node_index=node_index,
                node_name=node_name,
                node_path=first_element.node_path,
                atlas_path=next(iter(atlas_paths)),
                flip_v=first_atlas.flip_v,
                parts=parts,
            )
        )
    manifest = ObjectManifest(
        source_file=str(source_glb.resolve()),
        capabilities=AtlasCapabilities.geometry_guided(),
        warnings=["Los atlas externos se asociaron por nombre de nodo y se conservan como materiales editables."],
        objects=objects,
    )
    write_versioned_manifest(destination, manifest)
    LOGGER.info("Agrupadas %s regiones en %s objetos GLB.", sum(map(len, grouped.values())), len(objects))
    return manifest
