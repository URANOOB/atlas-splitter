"""Esquemas versionados y escritura atómica de manifiestos de los nuevos modos."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from atlas_splitter.domain.element import AtlasCapabilities, AtlasElement

SCHEMA_VERSION: Literal["1.0"] = "1.0"


class _VersionedManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = SCHEMA_VERSION
    source_file: str = Field(min_length=1)
    capabilities: AtlasCapabilities
    warnings: list[str] = Field(default_factory=list)


class SceneManifest(_VersionedManifest):
    """Índice de escena que conserva la procedencia de todos los elementos."""

    scenes: list[dict[str, object]] = Field(default_factory=list)
    elements: list[AtlasElement] = Field(default_factory=list)


class UvManifest(_VersionedManifest):
    """Índice UV y de exportaciones físicas para la reconstrucción en Blender."""

    atlas_width: int = Field(gt=0)
    atlas_height: int = Field(gt=0)
    elements: list[AtlasElement] = Field(default_factory=list)


class ObjectTexturePart(BaseModel):
    """Una región UV dentro del material que usa un objeto GLB."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    element_id: str = Field(pattern=r"^element_[a-f0-9]{16}$")
    atlas_directory: str = Field(min_length=1)
    exported_files: dict[str, str] = Field(default_factory=dict)


class ObjectGroup(BaseModel):
    """Objeto editable identificado por el nodo original de la escena."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    object_id: str = Field(pattern=r"^object_[a-f0-9]{16}$")
    node_index: int = Field(ge=0)
    node_name: str = Field(min_length=1)
    node_path: list[str] = Field(default_factory=list)
    atlas_path: str = Field(min_length=1)
    flip_v: bool = False
    parts: list[ObjectTexturePart] = Field(default_factory=list)


class ObjectManifest(_VersionedManifest):
    """Índice de nodos editables, atlas externos y partes UV."""

    objects: list[ObjectGroup] = Field(default_factory=list)


def write_versioned_manifest(destination: Path, manifest: SceneManifest | UvManifest | ObjectManifest) -> None:
    """Escribe JSON canónico y atómico para no dejar resultados parciales."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    temporary.replace(destination)
