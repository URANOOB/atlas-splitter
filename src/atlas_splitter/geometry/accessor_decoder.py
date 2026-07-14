"""Decodificación fiel de buffers y accessors glTF con NumPy."""

import base64
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from atlas_splitter.exceptions import AccessorDecodeError
from atlas_splitter.geometry.glb_loader import LoadedGltf, local_uri_path

_COMPONENT_TYPES: dict[int, np.dtype[Any]] = {
    5120: np.dtype("i1"),
    5121: np.dtype("u1"),
    5122: np.dtype("<i2"),
    5123: np.dtype("<u2"),
    5125: np.dtype("<u4"),
    5126: np.dtype("<f4"),
}
_TYPE_WIDTHS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT2": 4, "MAT3": 9, "MAT4": 16}


@dataclass
class AccessorDecoder:
    """Resuelve buffers locales y decodifica accessors, incluidos sparse."""

    loaded: LoadedGltf
    _buffers: dict[int, bytes] = field(default_factory=dict, init=False)

    def decode(self, accessor_index: int) -> np.ndarray:
        try:
            accessor = self.loaded.document.accessors[accessor_index]
            component_dtype = _COMPONENT_TYPES[accessor.componentType]
            width = _TYPE_WIDTHS[accessor.type]
        except (IndexError, KeyError, TypeError, AttributeError) as error:
            raise AccessorDecodeError(f"Accessor inválido: {accessor_index}") from error
        shape = (accessor.count, width)
        values = (
            np.zeros(shape, dtype=component_dtype)
            if accessor.bufferView is None
            else self._decode_buffer_view(
                accessor.bufferView, accessor.byteOffset or 0, accessor.count, width, component_dtype
            )
        )
        if accessor.sparse is not None:
            values = values.copy()
            self._apply_sparse(values, accessor.sparse, width, component_dtype)
        return _normalize(values) if accessor.normalized else values

    def _decode_buffer_view(
        self, view_index: int, accessor_offset: int, count: int, width: int, dtype: np.dtype[Any]
    ) -> np.ndarray:
        try:
            view = self.loaded.document.bufferViews[view_index]
            raw = self._buffer_data(view.buffer)
        except (IndexError, AttributeError) as error:
            raise AccessorDecodeError(f"bufferView inválido: {view_index}") from error
        element_size = dtype.itemsize * width
        stride = view.byteStride or element_size
        if stride < element_size:
            raise AccessorDecodeError("bufferView.byteStride es menor que el elemento del accessor")
        start = (view.byteOffset or 0) + accessor_offset
        end = start if count == 0 else start + (count - 1) * stride + element_size
        view_end = (view.byteOffset or 0) + view.byteLength
        if start < (view.byteOffset or 0) or end > view_end:
            raise AccessorDecodeError("El accessor excede los límites de su bufferView")
        if start < 0 or end > len(raw):
            raise AccessorDecodeError("El accessor excede los límites de su buffer")
        if stride == element_size:
            return np.frombuffer(raw, dtype=dtype, count=count * width, offset=start).reshape(count, width).copy()
        values = np.empty((count, width), dtype=dtype)
        for row in range(count):
            values[row] = np.frombuffer(raw, dtype=dtype, count=width, offset=start + row * stride)
        return values

    def _apply_sparse(self, values: np.ndarray, sparse: Any, width: int, value_dtype: np.dtype[Any]) -> None:
        try:
            index_dtype = _COMPONENT_TYPES[sparse.indices.componentType]
            if index_dtype.kind not in "ui":
                raise KeyError(sparse.indices.componentType)
            indices = self._decode_buffer_view(
                sparse.indices.bufferView, sparse.indices.byteOffset or 0, sparse.count, 1, index_dtype
            ).reshape(-1)
            replacements = self._decode_buffer_view(
                sparse.values.bufferView, sparse.values.byteOffset or 0, sparse.count, width, value_dtype
            )
        except (AttributeError, IndexError, KeyError) as error:
            raise AccessorDecodeError("Accessor sparse inválido") from error
        if np.any(indices >= len(values)):
            raise AccessorDecodeError("Un índice sparse excede el accessor")
        if len(np.unique(indices)) != len(indices):
            raise AccessorDecodeError("Un accessor sparse contiene índices duplicados")
        values[indices] = replacements

    def _buffer_data(self, buffer_index: int) -> bytes:
        if buffer_index in self._buffers:
            return self._buffers[buffer_index]
        try:
            buffer = self.loaded.document.buffers[buffer_index]
        except IndexError as error:
            raise AccessorDecodeError(f"Buffer inválido: {buffer_index}") from error
        if buffer.uri is None:
            data = self.loaded.document.binary_blob()
            if data is None:
                raise AccessorDecodeError("El GLB no contiene un buffer binario")
            data = bytes(data)
        elif buffer.uri.startswith("data:"):
            try:
                data = base64.b64decode(buffer.uri.split(",", 1)[1], validate=True)
            except (IndexError, ValueError) as error:
                raise AccessorDecodeError("URI data de buffer inválida") from error
        else:
            path = local_uri_path(self.loaded.resource_directory, buffer.uri)
            try:
                data = path.read_bytes()
            except OSError as error:
                raise AccessorDecodeError(f"No se pudo leer el buffer externo '{buffer.uri}'") from error
        if len(data) < buffer.byteLength:
            raise AccessorDecodeError("El buffer es menor que byteLength")
        binary_data = bytes(data)
        self._buffers[buffer_index] = binary_data
        return binary_data


def _normalize(values: np.ndarray) -> np.ndarray:
    if values.dtype.kind == "f":
        return values
    if values.dtype.kind == "u":
        return values.astype(np.float32) / np.iinfo(values.dtype).max
    info = np.iinfo(values.dtype)
    return np.maximum(values.astype(np.float32) / info.max, -1.0)
