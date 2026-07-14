"""Agrupación determinista de triángulos conectados por aristas UV."""

from __future__ import annotations

import numpy as np

from atlas_splitter.exceptions import PrimitiveDecodeError


def uv_island_triangle_groups(
    triangles: np.ndarray, uv_coordinates: np.ndarray | None = None, tolerance: float = 1e-6
) -> list[np.ndarray]:
    """Devuelve islas cuyos triángulos comparten una arista completa.

    Las aristas se identifican por pares de índices de vértices sin orientación,
    o por sus coordenadas UV cuantizadas cuando se proporcionan. Esto permite
    reconocer vértices UV duplicados con índices distintos.
    Por tanto dos triángulos que sólo se tocan en una esquina permanecen en islas
    distintas. El orden sigue el primer triángulo de cada componente.
    """
    indices = np.asarray(triangles)
    if indices.ndim != 2 or indices.shape[1] != 3 or not np.issubdtype(indices.dtype, np.integer):
        raise PrimitiveDecodeError("Las islas UV requieren triángulos enteros con forma (N, 3)")
    coordinates = None if uv_coordinates is None else np.asarray(uv_coordinates, dtype=np.float64)
    if coordinates is not None:
        if tolerance <= 0:
            raise PrimitiveDecodeError("La tolerancia UV debe ser mayor que cero.")
        if coordinates.ndim != 2 or coordinates.shape[1] != 2 or np.any(indices < 0) or np.any(indices >= len(coordinates)):
            raise PrimitiveDecodeError("Las coordenadas UV deben ser VEC2 y cubrir todos los índices de triángulo.")
    owner_by_edge: dict[object, int] = {}
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
        vertices = [int(vertex) for vertex in triangle]
        for first, second in ((vertices[0], vertices[1]), (vertices[1], vertices[2]), (vertices[2], vertices[0])):
            if coordinates is None:
                edge = (first, second) if first < second else (second, first)
            else:
                first_uv = tuple(np.rint(coordinates[first] / tolerance).astype(np.int64).tolist())
                second_uv = tuple(np.rint(coordinates[second] / tolerance).astype(np.int64).tolist())
                edge = (first_uv, second_uv) if first_uv < second_uv else (second_uv, first_uv)
            previous = owner_by_edge.setdefault(edge, triangle_index)
            union(triangle_index, previous)
    groups: dict[int, list[int]] = {}
    for triangle_index in range(len(indices)):
        groups.setdefault(find(triangle_index), []).append(triangle_index)
    return [np.asarray(group, dtype=np.int64) for _, group in sorted(groups.items(), key=lambda item: item[1][0])]
