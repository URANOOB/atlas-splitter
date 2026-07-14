"""Descomposición determinista de primitivas en componentes de malla."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from atlas_splitter.exceptions import PrimitiveDecodeError


@dataclass(frozen=True, slots=True)
class MeshComponent:
    """Filas de triángulos y vértices que forman una pieza topológicamente conexa."""

    component_index: int
    triangle_rows: np.ndarray
    vertex_indices: np.ndarray


def mesh_connected_components(triangles: np.ndarray) -> list[MeshComponent]:
    """Separa triángulos que no comparten índices de vértice, en orden estable."""
    indices = np.asarray(triangles)
    if indices.ndim != 2 or indices.shape[1] != 3 or not np.issubdtype(indices.dtype, np.integer):
        raise PrimitiveDecodeError("La conectividad requiere triángulos enteros con forma (N, 3).")
    if len(indices) == 0:
        return []
    parents = list(range(len(indices)))

    def find(item: int) -> int:
        while parents[item] != item:
            parents[item] = parents[parents[item]]
            item = parents[item]
        return item

    def union(first: int, second: int) -> None:
        first_root, second_root = find(first), find(second)
        if first_root != second_root:
            parents[second_root] = first_root

    owner_by_vertex: dict[int, int] = {}
    for row, triangle in enumerate(indices):
        for vertex in triangle:
            previous = owner_by_vertex.setdefault(int(vertex), row)
            union(row, previous)
    rows_by_root: dict[int, list[int]] = {}
    for row in range(len(indices)):
        rows_by_root.setdefault(find(row), []).append(row)
    result: list[MeshComponent] = []
    for component_index, rows in enumerate(sorted(rows_by_root.values(), key=lambda values: values[0]), start=1):
        triangle_rows = np.asarray(rows, dtype=np.int64)
        vertices = np.unique(indices[triangle_rows].reshape(-1)).astype(np.int64)
        result.append(MeshComponent(component_index, triangle_rows, vertices))
    return result


def bounding_box_3d(points: np.ndarray) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """Devuelve mínimo y máximo XYZ, validando una nube de puntos no vacía."""
    values = np.asarray(points, dtype=np.float64)
    if values.ndim != 2 or values.shape[1] != 3 or len(values) == 0:
        raise PrimitiveDecodeError("El bounding box 3D requiere puntos XYZ no vacíos.")
    return tuple(values.min(axis=0).tolist()), tuple(values.max(axis=0).tolist())


def bounding_box_distance(
    first: tuple[tuple[float, float, float], tuple[float, float, float]],
    second: tuple[tuple[float, float, float], tuple[float, float, float]],
) -> float:
    """Distancia euclídea entre AABB; cero cuando se tocan o solapan."""
    first_min, first_max = np.asarray(first[0]), np.asarray(first[1])
    second_min, second_max = np.asarray(second[0]), np.asarray(second[1])
    gap = np.maximum(0.0, np.maximum(first_min - second_max, second_min - first_max))
    return float(np.linalg.norm(gap))
