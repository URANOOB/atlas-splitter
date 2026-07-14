"""Tipos de dominio independientes del pipeline visual."""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class PrimitiveReference:
    """Ubicación estable de una primitiva dentro de un documento glTF."""

    node_index: int
    mesh_index: int
    primitive_index: int
    material_index: int | None


@dataclass
class DecodedPrimitive:
    """Geometría de una primitiva expresada siempre como triángulos."""

    reference: PrimitiveReference
    positions: np.ndarray
    triangle_indices: np.ndarray
    texcoords: dict[int, np.ndarray]
    node_path: tuple[str, ...]
    node_transform: np.ndarray


@dataclass(frozen=True)
class MaterialTextureReference:
    """Textura declarada por un material, sin seleccionar aún una región UV."""

    material_index: int
    channel: str
    texture_index: int
    texcoord_set: int
