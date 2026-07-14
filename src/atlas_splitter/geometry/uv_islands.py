"""Agrupación determinista de triángulos conectados por aristas UV reales."""

from __future__ import annotations

from collections.abc import Callable
from itertools import product

import numpy as np

from atlas_splitter.exceptions import PrimitiveDecodeError

UnionTriangles = Callable[[int, int], None]


def uv_island_triangle_groups(
    triangles: np.ndarray, uv_coordinates: np.ndarray | None = None, tolerance: float = 1e-6
) -> list[np.ndarray]:
    """Devuelve islas cuyos triángulos comparten una arista UV completa.

    Cuando se proporcionan UV, los índices geométricos no deciden la conexión:
    ambos extremos de una arista deben coincidir dentro de ``tolerance``. Esto
    permite costuras con índices distintos y evita unir triángulos que sólo
    comparten un vértice. Los triángulos UV degenerados permanecen aislados.
    """
    indices = np.asarray(triangles)
    if indices.ndim != 2 or indices.shape[1] != 3 or not np.issubdtype(indices.dtype, np.integer):
        raise PrimitiveDecodeError("Las islas UV requieren triángulos enteros con forma (N, 3)")
    if tolerance <= 0:
        raise PrimitiveDecodeError("La tolerancia UV debe ser mayor que cero.")
    coordinates = None if uv_coordinates is None else np.asarray(uv_coordinates, dtype=np.float64)
    if coordinates is not None:
        invalid_coordinates = (
            coordinates.ndim != 2
            or coordinates.shape[1] != 2
            or not np.isfinite(coordinates).all()
            or np.any(indices < 0)
            or np.any(indices >= len(coordinates))
        )
        if invalid_coordinates:
            raise PrimitiveDecodeError("Las coordenadas UV deben ser VEC2 finitas y cubrir todos los triángulos.")
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

    if coordinates is None:
        _connect_index_edges(indices, union)
    else:
        _connect_uv_edges(indices, coordinates, tolerance, union)
    groups: dict[int, list[int]] = {}
    for triangle_index in range(len(indices)):
        groups.setdefault(find(triangle_index), []).append(triangle_index)
    return [np.asarray(group, dtype=np.int64) for _, group in sorted(groups.items(), key=lambda item: item[1][0])]


def _connect_index_edges(triangles: np.ndarray, union: UnionTriangles) -> None:
    """Conserva el comportamiento útil para clientes que no tienen UVs."""
    owner_by_edge: dict[tuple[int, int], int] = {}
    for triangle_index, triangle in enumerate(triangles):
        vertices = [int(vertex) for vertex in triangle]
        for first, second in ((vertices[0], vertices[1]), (vertices[1], vertices[2]), (vertices[2], vertices[0])):
            edge = (first, second) if first < second else (second, first)
            previous = owner_by_edge.setdefault(edge, triangle_index)
            union(triangle_index, previous)


def _connect_uv_edges(triangles: np.ndarray, coordinates: np.ndarray, tolerance: float, union: UnionTriangles) -> None:
    """Une sólo aristas cuyos extremos UV son iguales dentro de tolerancia."""
    edges_by_cell: dict[tuple[int, int, int, int], list[int]] = {}
    edge_records: list[tuple[int, np.ndarray, np.ndarray]] = []
    for triangle_index, triangle in enumerate(triangles):
        triangle_uvs = coordinates[triangle]
        if _is_degenerate(triangle_uvs, tolerance):
            continue
        for first, second in ((0, 1), (1, 2), (2, 0)):
            start, end = triangle_uvs[first], triangle_uvs[second]
            candidates: set[int] = set()
            for key in _neighbouring_edge_cells(start, end, tolerance):
                candidates.update(edges_by_cell.get(key, []))
            for candidate_index in candidates:
                owner, owner_start, owner_end = edge_records[candidate_index]
                if _same_uv_edge(start, end, owner_start, owner_end, tolerance):
                    union(triangle_index, owner)
            cell = _edge_cell(start, end, tolerance)
            edges_by_cell.setdefault(cell, []).append(len(edge_records))
            edge_records.append((triangle_index, start, end))


def _neighbouring_edge_cells(start: np.ndarray, end: np.ndarray, tolerance: float) -> list[tuple[int, int, int, int]]:
    start_cell, end_cell = _uv_cell(start, tolerance), _uv_cell(end, tolerance)
    offsets = (-1, 0, 1)
    direct = [
        (start_cell[0] + first_x, start_cell[1] + first_y, end_cell[0] + second_x, end_cell[1] + second_y)
        for first_x, first_y, second_x, second_y in product(offsets, repeat=4)
    ]
    reversed_cells = [
        (end_cell[0] + first_x, end_cell[1] + first_y, start_cell[0] + second_x, start_cell[1] + second_y)
        for first_x, first_y, second_x, second_y in product(offsets, repeat=4)
    ]
    return [*direct, *reversed_cells]


def _edge_cell(start: np.ndarray, end: np.ndarray, tolerance: float) -> tuple[int, int, int, int]:
    start_cell, end_cell = _uv_cell(start, tolerance), _uv_cell(end, tolerance)
    return start_cell[0], start_cell[1], end_cell[0], end_cell[1]


def _uv_cell(point: np.ndarray, tolerance: float) -> tuple[int, int]:
    return int(np.floor(point[0] / tolerance)), int(np.floor(point[1] / tolerance))


def _same_uv_edge(
    start: np.ndarray, end: np.ndarray, other_start: np.ndarray, other_end: np.ndarray, tolerance: float
) -> bool:
    return (_same_uv_point(start, other_start, tolerance) and _same_uv_point(end, other_end, tolerance)) or (
        _same_uv_point(start, other_end, tolerance) and _same_uv_point(end, other_start, tolerance)
    )


def _same_uv_point(first: np.ndarray, second: np.ndarray, tolerance: float) -> bool:
    return bool(np.all(np.abs(first - second) <= tolerance))


def _is_degenerate(triangle_uvs: np.ndarray, tolerance: float) -> bool:
    first, second, third = triangle_uvs
    double_area = (second[0] - first[0]) * (third[1] - first[1]) - (second[1] - first[1]) * (third[0] - first[0])
    return bool(abs(double_area) <= tolerance * tolerance)
