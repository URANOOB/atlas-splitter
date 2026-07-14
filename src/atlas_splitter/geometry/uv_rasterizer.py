"""Conversión precisa de triángulos UV glTF a máscaras de píxeles del atlas."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, cast

import cv2
import numpy as np

from atlas_splitter.exceptions import PrimitiveDecodeError

SamplerWrap = Literal["REPEAT", "MIRRORED_REPEAT", "CLAMP_TO_EDGE"]


@dataclass(frozen=True)
class RasterizedUvRegion:
    """Máscara de una región UV y su rectángulo exacto dentro del atlas."""

    mask: np.ndarray
    bounding_box: tuple[int, int, int, int]
    pixel_polygons: tuple[tuple[tuple[int, int], ...], ...]


def uv_to_pixel_coordinates(
    uvs: np.ndarray,
    width: int,
    height: int,
    wrap_s: SamplerWrap = "REPEAT",
    wrap_t: SamplerWrap = "REPEAT",
) -> np.ndarray:
    """Mapea UV glTF a píxeles, invirtiendo V porque la imagen empieza arriba."""
    if width <= 0 or height <= 0:
        raise ValueError("El atlas debe tener dimensiones positivas")
    values = np.asarray(uvs, dtype=np.float64)
    if values.ndim != 2 or values.shape[1] != 2:
        raise ValueError("Las coordenadas UV deben tener forma (N, 2)")
    u = _apply_wrap(values[:, 0], wrap_s)
    v = _apply_wrap(values[:, 1], wrap_t)
    x = np.rint(u * (width - 1)).astype(np.int32)
    y = np.rint((1.0 - v) * (height - 1)).astype(np.int32)
    return np.column_stack((x, y))


def rasterize_uv_triangles(
    uvs: np.ndarray,
    triangles: np.ndarray,
    width: int,
    height: int,
    wrap_s: SamplerWrap = "REPEAT",
    wrap_t: SamplerWrap = "REPEAT",
) -> RasterizedUvRegion:
    """Rasteriza polígonos triangulares; nunca sustituye la región por su min/max."""
    coordinates = np.asarray(uvs, dtype=np.float64)
    indices = np.asarray(triangles)
    if coordinates.ndim != 2 or coordinates.shape[1] != 2:
        raise PrimitiveDecodeError("Las UV de la primitiva deben ser VEC2")
    if indices.ndim != 2 or indices.shape[1] != 3:
        raise PrimitiveDecodeError("La rasterización UV requiere índices TRIANGLES de forma (N, 3)")
    if not np.issubdtype(indices.dtype, np.integer):
        raise PrimitiveDecodeError("Los índices de triángulos UV deben ser enteros")
    if np.any(indices < 0) or np.any(indices >= len(coordinates)):
        raise PrimitiveDecodeError("Los índices de triángulos UV exceden las coordenadas disponibles")
    mask = np.zeros((height, width), dtype=np.uint8)
    polygons: list[tuple[tuple[int, int], ...]] = []
    for triangle in indices:
        polygon = _uv_to_pixel_coordinates(
            coordinates[triangle], width, height, wrap_s, wrap_t, preserve_repeat_boundaries=True
        )
        cv2.fillConvexPoly(mask, polygon, color=255, lineType=cv2.LINE_8)
        polygons.append(tuple((int(x), int(y)) for x, y in polygon))
    active_y, active_x = np.nonzero(mask)
    if len(active_x) == 0:
        raise PrimitiveDecodeError("La rasterización UV no produjo píxeles dentro del atlas")
    x, y = int(active_x.min()), int(active_y.min())
    return RasterizedUvRegion(
        mask=mask.astype(bool),
        bounding_box=(x, y, int(active_x.max()) - x + 1, int(active_y.max()) - y + 1),
        pixel_polygons=tuple(polygons),
    )


def _uv_to_pixel_coordinates(
    uvs: np.ndarray,
    width: int,
    height: int,
    wrap_s: SamplerWrap,
    wrap_t: SamplerWrap,
    *,
    preserve_repeat_boundaries: bool,
) -> np.ndarray:
    values = np.asarray(uvs, dtype=np.float64)
    u = _apply_wrap(values[:, 0], wrap_s, preserve_repeat_boundaries)
    v = _apply_wrap(values[:, 1], wrap_t, preserve_repeat_boundaries)
    x = np.rint(u * (width - 1)).astype(np.int32)
    y = np.rint((1.0 - v) * (height - 1)).astype(np.int32)
    return np.column_stack((x, y))


def _apply_wrap(values: np.ndarray, mode: SamplerWrap, preserve_repeat_boundaries: bool = False) -> np.ndarray:
    if mode == "CLAMP_TO_EDGE":
        return cast(np.ndarray, np.clip(values, 0.0, 1.0))
    if mode == "REPEAT":
        wrapped = cast(np.ndarray, np.mod(values, 1.0))
        if preserve_repeat_boundaries:
            return np.where((values > 0.0) & np.isclose(wrapped, 0.0), 1.0, wrapped)
        return wrapped
    if mode == "MIRRORED_REPEAT":
        return cast(np.ndarray, 1.0 - np.abs(np.mod(values, 2.0) - 1.0))
    raise ValueError(f"Modo de sampler no soportado: {mode}")
