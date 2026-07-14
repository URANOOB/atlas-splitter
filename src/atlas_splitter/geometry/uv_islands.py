"""Agrupación determinista de triángulos que comparten vértices UV."""

from __future__ import annotations

import numpy as np

from atlas_splitter.exceptions import PrimitiveDecodeError


def uv_island_triangle_groups(triangles: np.ndarray) -> list[np.ndarray]:
    """Devuelve componentes conexos por índice de vértice, ordenados por su primer triángulo."""
    indices = np.asarray(triangles)
    if indices.ndim != 2 or indices.shape[1] != 3 or not np.issubdtype(indices.dtype, np.integer):
        raise PrimitiveDecodeError("Las islas UV requieren triángulos enteros con forma (N, 3)")
    owner_by_vertex: dict[int, int] = {}
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

    for triangle_index, triangle in enumerate(indices):
        for vertex in triangle:
            vertex_index = int(vertex)
            previous = owner_by_vertex.setdefault(vertex_index, triangle_index)
            union(triangle_index, previous)
    groups: dict[int, list[int]] = {}
    for triangle_index in range(len(indices)):
        groups.setdefault(find(triangle_index), []).append(triangle_index)
    return [np.asarray(group, dtype=np.int64) for _, group in sorted(groups.items(), key=lambda item: item[1][0])]
