"""Asociación explícita por nombres entre nodos exportados y atlas externos locales."""

from __future__ import annotations

import logging
from pathlib import Path

from atlas_splitter.exceptions import GltfLoadError
from atlas_splitter.geometry.glb_loader import LoadedGltf

LOGGER = logging.getLogger(__name__)
_ORDINAL_TEXTURES = {
    "first": "first-house",
    "second": "second-photos",
    "third": "third-desk",
    "fourth": "fourth-extras",
    "fifth": "fifth-background",
    "sixth": "sixth-plants",
    "seventh": "seventh-large-stuff",
    "eighth": "eighth-decor",
    "ninth": "ninth-attachment",
}


def associate_named_external_atlases(loaded: LoadedGltf, atlas_directory: Path) -> dict[Path, set[int]]:
    """Relaciona nodos ``First_*`` … ``Ninth_*`` con sus WEBP ``*_day`` locales.

    Sólo se aceptan coincidencias exactas tras retirar ``_day``. Las variantes
    ``.original`` se excluyen deliberadamente para no crear asociaciones ambiguas.
    """
    if not atlas_directory.is_dir():
        raise GltfLoadError(f"El directorio de atlas no existe: {atlas_directory}")
    available = {
        path.stem.removesuffix("_day"): path
        for path in atlas_directory.glob("*_day.webp")
        if not path.stem.endswith(".original")
    }
    result: dict[Path, set[int]] = {}
    for node_index, node in enumerate(loaded.document.nodes or []):
        name = getattr(node, "name", None) or ""
        ordinal = name.lower().split("_", 1)[0]
        texture_stem = _ORDINAL_TEXTURES.get(ordinal)
        if texture_stem is None:
            continue
        atlas = available.get(texture_stem)
        if atlas is None:
            raise GltfLoadError(f"No existe {texture_stem}_day.webp para el nodo {name}.")
        result.setdefault(atlas, set()).add(node_index)
    if not result:
        raise GltfLoadError("No se encontró ningún nodo con una asociación de atlas por nombre.")
    LOGGER.info("Asociados %s atlas externos a %s nodos por nombre.", len(result), sum(map(len, result.values())))
    return result
