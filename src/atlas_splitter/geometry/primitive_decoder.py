"""Decodifica primitivas de malla sin aplicar aún transformaciones UV."""

import logging
from typing import Any

import numpy as np

from atlas_splitter.exceptions import PrimitiveDecodeError
from atlas_splitter.geometry.accessor_decoder import AccessorDecoder
from atlas_splitter.geometry.draco_decoder import DracoDecoder
from atlas_splitter.geometry.glb_loader import LoadedGltf
from atlas_splitter.geometry.scene_graph import iter_scene_nodes
from atlas_splitter.geometry.types import DecodedPrimitive, PrimitiveReference

LOGGER = logging.getLogger(__name__)
_TRIANGLES, _TRIANGLE_STRIP, _TRIANGLE_FAN = 4, 5, 6
_UNSUPPORTED_PRIMITIVE_EXTENSIONS = frozenset({"EXT_meshopt_compression"})


def decode_scene_primitives(loaded: LoadedGltf) -> list[DecodedPrimitive]:
    """Decodifica primitivas triangulares alcanzables de todas las escenas."""
    decoder = AccessorDecoder(loaded)
    decoded: list[DecodedPrimitive] = []
    draco = DracoDecoder()
    for node_index, node_path, node_transform in iter_scene_nodes(loaded):
        node = loaded.document.nodes[node_index]
        if node.mesh is None:
            continue
        try:
            mesh = loaded.document.meshes[node.mesh]
        except IndexError as error:
            raise PrimitiveDecodeError(f"Nodo {node_index} referencia una malla inexistente") from error
        for primitive_index, primitive in enumerate(mesh.primitives):
            mode = primitive.mode if primitive.mode is not None else _TRIANGLES
            if mode not in {_TRIANGLES, _TRIANGLE_STRIP, _TRIANGLE_FAN}:
                LOGGER.warning(
                    "La primitiva %s/%s usa modo no superficial %s; se omite.", node.mesh, primitive_index, mode
                )
                continue
            reference = PrimitiveReference(node_index, node.mesh, primitive_index, primitive.material)
            decoded.append(_decode_primitive(decoder, draco, primitive, mode, reference, node_path, node_transform))
    return decoded


def _decode_primitive(
    decoder: AccessorDecoder,
    draco: DracoDecoder,
    primitive: Any,
    mode: int,
    reference: PrimitiveReference,
    node_path: tuple[str, ...],
    node_transform: np.ndarray,
) -> DecodedPrimitive:
    extensions = getattr(primitive, "extensions", None) or {}
    if isinstance(extensions, dict):
        unsupported = sorted(set(extensions) & _UNSUPPORTED_PRIMITIVE_EXTENSIONS)
        if unsupported:
            raise PrimitiveDecodeError(
                f"La primitiva nodo={reference.node_index}, malla={reference.mesh_index}, "
                f"primitiva={reference.primitive_index} usa la extensión no soportada {unsupported[0]}"
            )
    draco_extension = extensions.get("KHR_draco_mesh_compression") if isinstance(extensions, dict) else None
    if isinstance(draco_extension, dict):
        geometry = draco.decode(decoder.loaded, draco_extension)
        texcoords = {
            int(name.removeprefix("TEXCOORD_")): values
            for name, values in geometry.attributes.items()
            if name.startswith("TEXCOORD_") and values.shape[1:] == (2,)
        }
        return DecodedPrimitive(
            reference, geometry.attributes["POSITION"], geometry.triangle_indices, texcoords, node_path, node_transform
        )
    attributes = primitive.attributes
    position_accessor = getattr(attributes, "POSITION", None)
    if position_accessor is None:
        raise PrimitiveDecodeError(f"La primitiva {reference} no tiene atributo POSITION")
    positions = decoder.decode(position_accessor)
    if positions.shape[1:] != (3,):
        raise PrimitiveDecodeError(f"POSITION de {reference} debe ser VEC3")
    raw_indices = (
        np.arange(len(positions), dtype=np.int64)
        if primitive.indices is None
        else decoder.decode(primitive.indices).reshape(-1).astype(np.int64)
    )
    if np.any(raw_indices < 0) or np.any(raw_indices >= len(positions)):
        raise PrimitiveDecodeError(f"Índices fuera de rango en {reference}")
    texcoords = _decode_texcoords(decoder, attributes, len(positions), reference)
    return DecodedPrimitive(
        reference, positions, _to_triangles(raw_indices, mode, reference), texcoords, node_path, node_transform
    )


def _decode_texcoords(
    decoder: AccessorDecoder, attributes: Any, vertex_count: int, reference: PrimitiveReference
) -> dict[int, np.ndarray]:
    result: dict[int, np.ndarray] = {}
    for name, accessor_index in vars(attributes).items():
        if accessor_index is None or not name.startswith("TEXCOORD_"):
            continue
        values = decoder.decode(accessor_index)
        if values.shape != (vertex_count, 2):
            raise PrimitiveDecodeError(f"{name} de {reference} debe ser VEC2 y coincidir con POSITION")
        result[int(name.removeprefix("TEXCOORD_"))] = values
    return result


def _to_triangles(indices: np.ndarray, mode: int, reference: PrimitiveReference) -> np.ndarray:
    if mode == _TRIANGLES:
        if len(indices) % 3:
            raise PrimitiveDecodeError(f"TRIANGLES de {reference} no es múltiplo de tres")
        return indices.reshape(-1, 3)
    triangles: list[tuple[int, int, int]] = []
    if mode == _TRIANGLE_STRIP:
        for index in range(len(indices) - 2):
            a, b, c = indices[index : index + 3]
            triangles.append((a, b, c) if index % 2 == 0 else (b, a, c))
    else:
        for index in range(1, len(indices) - 1):
            triangles.append((indices[0], indices[index], indices[index + 1]))
    return np.asarray(triangles, dtype=np.int64).reshape(-1, 3)
