"""Entidades independientes de la lectura de glTF y de la escritura de archivos."""

from __future__ import annotations

import hashlib
import re
import unicodedata

from pydantic import BaseModel, ConfigDict, Field, field_validator

_UNSAFE_SLUG = re.compile(r"[^a-z0-9]+")


def slugify(value: str, *, fallback: str = "element", maximum_length: int = 80) -> str:
    """Devuelve un nombre de archivo estable, limitado y sin componentes de ruta."""
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii").lower()
    slug = _UNSAFE_SLUG.sub("-", normalized).strip("-")[:maximum_length].strip("-")
    return slug or fallback


def stable_element_id(
    scene_index: int,
    node_index: int,
    mesh_index: int,
    primitive_index: int,
    group_key: str,
) -> str:
    """Crea un ID determinista desde referencias glTF, nunca desde el orden visual."""
    material = f"{scene_index}:{node_index}:{mesh_index}:{primitive_index}:{group_key}".encode()
    return f"element_{hashlib.sha256(material).hexdigest()[:16]}"


class BoundingBox(BaseModel):
    """Rectángulo en píxeles del atlas, con dimensiones positivas."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    x: int
    y: int
    width: int = Field(gt=0)
    height: int = Field(gt=0)


class UvIsland(BaseModel):
    """Una isla UV rasterizada y sus triángulos de origen."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    island_id: str = Field(min_length=1, max_length=120)
    bounding_box: BoundingBox
    triangle_indices: list[int] = Field(default_factory=list)


class AtlasCapabilities(BaseModel):
    """Declara la fidelidad que puede esperar un consumidor del manifiesto."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    uv_available: bool
    geometry_available: bool
    reconstruction_quality: str

    @classmethod
    def geometry_guided(cls) -> AtlasCapabilities:
        return cls(uv_available=True, geometry_available=True, reconstruction_quality="geometry_guided")

    @classmethod
    def approximate_2d_only(cls) -> AtlasCapabilities:
        return cls(uv_available=False, geometry_available=False, reconstruction_quality="approximate_2d_only")


class AtlasElement(BaseModel):
    """Relación estable entre una región exportada y su origen geométrico."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    element_id: str = Field(pattern=r"^element_[a-f0-9]{16}$")
    original_name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=80)
    scene_index: int = Field(ge=0)
    node_index: int = Field(ge=0)
    node_path: list[str] = Field(default_factory=list)
    mesh_index: int = Field(ge=0)
    primitive_index: int = Field(ge=0)
    material_index: int | None = Field(default=None, ge=0)
    material_name: str | None = Field(default=None, max_length=255)
    texture_slot: str | None = Field(default=None, max_length=64)
    image_index: int | None = Field(default=None, ge=0)
    texture_index: int | None = Field(default=None, ge=0)
    texcoord: int | None = Field(default=None, ge=0)
    original_uvs: list[list[float]] = Field(default_factory=list)
    transformed_uvs: list[list[float]] = Field(default_factory=list)
    triangle_indices: list[list[int]] = Field(default_factory=list)
    pixel_polygons: list[list[list[int]]] = Field(default_factory=list)
    bounding_box: BoundingBox
    uv_islands: list[UvIsland] = Field(default_factory=list)
    exported_files: dict[str, str] = Field(default_factory=dict)
    node_transform: list[float] = Field(default_factory=list)
    shared_region_consumers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    compatibility_level: str = Field(default="geometry_guided", max_length=64)

    @field_validator("slug")
    @classmethod
    def _validate_slug(cls, value: str) -> str:
        if value != slugify(value):
            raise ValueError("slug must be a safe lowercase filename")
        return value
