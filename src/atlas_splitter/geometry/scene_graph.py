"""Recorrido de escenas, nodos y transformaciones glTF."""

from collections.abc import Iterator

import numpy as np

from atlas_splitter.geometry.glb_loader import LoadedGltf


def iter_scene_nodes(loaded: LoadedGltf) -> Iterator[tuple[int, tuple[str, ...], np.ndarray]]:
    """Devuelve nodos alcanzables de todas las escenas y su matriz mundial."""
    document = loaded.document
    roots_per_scene = (
        (scene.nodes or [] for scene in document.scenes) if document.scenes else [_implicit_roots(document.nodes)]
    )
    for roots in roots_per_scene:
        for root in roots:
            yield from _walk(document.nodes, root, (), np.eye(4, dtype=np.float64), set())


def _walk(
    nodes: list[object], index: int, prefix: tuple[str, ...], parent: np.ndarray, ancestors: set[int]
) -> Iterator[tuple[int, tuple[str, ...], np.ndarray]]:
    if index in ancestors:
        return
    node = nodes[index]
    name = getattr(node, "name", None) or f"node_{index}"
    transform = parent @ node_matrix(node)
    path = (*prefix, name)
    yield index, path, transform
    for child in getattr(node, "children", None) or []:
        yield from _walk(nodes, child, path, transform, {*ancestors, index})


def _implicit_roots(nodes: list[object]) -> list[int]:
    children = {child for node in nodes for child in (getattr(node, "children", None) or [])}
    return [index for index in range(len(nodes)) if index not in children]


def node_matrix(node: object) -> np.ndarray:
    """Construye la matriz del nodo desde ``matrix`` o TRS, según glTF."""
    matrix = getattr(node, "matrix", None)
    if matrix:
        return np.asarray(matrix, dtype=np.float64).reshape(4, 4).T
    translation = np.asarray(getattr(node, "translation", None) or [0.0, 0.0, 0.0], dtype=np.float64)
    rotation = np.asarray(getattr(node, "rotation", None) or [0.0, 0.0, 0.0, 1.0], dtype=np.float64)
    scale = np.asarray(getattr(node, "scale", None) or [1.0, 1.0, 1.0], dtype=np.float64)
    x, y, z, w = rotation
    rotation_matrix = np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w), 0],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w), 0],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y), 0],
            [0, 0, 0, 1],
        ],
        dtype=np.float64,
    )
    result = rotation_matrix @ np.diag([*scale, 1.0])
    result[:3, 3] = translation
    return result
