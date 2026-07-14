"""Resolución local de texturas glTF y recortes por una misma región UV."""

from __future__ import annotations

import base64
import hashlib
import io
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import numpy as np
from PIL import Image

from atlas_splitter.exceptions import GltfLoadError
from atlas_splitter.geometry.glb_loader import LoadedGltf, local_uri_path
from atlas_splitter.geometry.uv_rasterizer import SamplerWrap, rasterize_uv_triangles

TextureSlot = Literal["baseColor", "normal", "metallicRoughness", "occlusion", "emissive"]
_NON_PBR_SLOTS: tuple[tuple[TextureSlot, str], ...] = (
    ("normal", "normalTexture"),
    ("occlusion", "occlusionTexture"),
    ("emissive", "emissiveTexture"),
)
_WRAP_CODES: dict[int, SamplerWrap] = {10497: "REPEAT", 33648: "MIRRORED_REPEAT", 33071: "CLAMP_TO_EDGE"}


@dataclass(frozen=True)
class TextureTransform:
    offset: tuple[float, float] = (0.0, 0.0)
    scale: tuple[float, float] = (1.0, 1.0)
    rotation: float = 0.0

    def apply(self, uvs: np.ndarray) -> np.ndarray:
        """Aplica el orden definido por KHR_texture_transform: escala, rota y desplaza."""
        values = np.asarray(uvs, dtype=np.float64)
        scaled = values * np.asarray(self.scale, dtype=np.float64)
        cosine, sine = math.cos(self.rotation), math.sin(self.rotation)
        rotated = np.column_stack(
            (cosine * scaled[:, 0] - sine * scaled[:, 1], sine * scaled[:, 0] + cosine * scaled[:, 1])
        )
        return rotated + np.asarray(self.offset, dtype=np.float64)


@dataclass(frozen=True)
class TextureBinding:
    slot: TextureSlot
    texture_index: int
    image_index: int
    texcoord: int
    transform: TextureTransform
    wrap_s: SamplerWrap
    wrap_t: SamplerWrap
    color_space: Literal["sRGB", "linear"]


def material_texture_bindings(loaded: LoadedGltf, material_index: int) -> list[TextureBinding]:
    """Obtiene todos los mapas de un material y su conjunto UV efectivo."""
    try:
        material = loaded.document.materials[material_index]
    except (IndexError, TypeError) as error:
        raise GltfLoadError(f"Material inexistente: {material_index}") from error
    texture_infos: list[tuple[TextureSlot, Any]] = []
    pbr = getattr(material, "pbrMetallicRoughness", None)
    if pbr is not None and getattr(pbr, "baseColorTexture", None) is not None:
        texture_infos.append(("baseColor", pbr.baseColorTexture))
    if pbr is not None and getattr(pbr, "metallicRoughnessTexture", None) is not None:
        texture_infos.append(("metallicRoughness", pbr.metallicRoughnessTexture))
    for slot, attribute in _NON_PBR_SLOTS:
        info = getattr(material, attribute, None)
        if info is not None:
            texture_infos.append((slot, info))
    return [_binding_from_info(loaded, slot, info) for slot, info in texture_infos]


def read_texture_image(loaded: LoadedGltf, image_index: int) -> Image.Image:
    """Carga una imagen embebida, data URI o archivo local, sin redes ni descargas."""
    try:
        image = loaded.document.images[image_index]
    except (IndexError, TypeError) as error:
        raise GltfLoadError(f"Imagen inexistente: {image_index}") from error
    if image.bufferView is not None:
        raw = _buffer_view_data(loaded, image.bufferView)
    elif image.uri is not None and image.uri.startswith("data:"):
        try:
            raw = base64.b64decode(image.uri.split(",", 1)[1], validate=True)
        except (IndexError, ValueError) as error:
            raise GltfLoadError(f"Data URI de imagen inválida: {image_index}") from error
    elif image.uri is not None:
        try:
            raw = local_uri_path(loaded.resource_directory, image.uri).read_bytes()
        except OSError as error:
            raise GltfLoadError(f"No se pudo leer la imagen local '{image.uri}'") from error
    else:
        raise GltfLoadError(f"La imagen {image_index} no declara uri ni bufferView")
    try:
        with Image.open(io.BytesIO(raw)) as decoded:
            return decoded.convert("RGBA")
    except (OSError, ValueError) as error:
        raise GltfLoadError(f"No se pudo decodificar la imagen {image_index}") from error


def export_material_crops(
    destination: Path,
    loaded: LoadedGltf,
    bindings: list[TextureBinding],
    uvs: np.ndarray,
    triangles: np.ndarray,
    padding: int = 0,
    image_overrides: dict[int, Image.Image] | None = None,
) -> dict[TextureSlot, Path]:
    """Exporta todos los mapas del material usando sus UV y máscara exactas compartidas."""
    if padding < 0:
        raise ValueError("padding no puede ser negativo")
    destination.mkdir(parents=True, exist_ok=True)
    exported: dict[TextureSlot, Path] = {}
    cache: dict[tuple[int, bytes], Path] = {}
    for binding in bindings:
        image = (image_overrides or {}).get(binding.image_index) or read_texture_image(loaded, binding.image_index)
        transformed_uvs = binding.transform.apply(uvs)
        region = rasterize_uv_triangles(
            transformed_uvs, triangles, image.width, image.height, binding.wrap_s, binding.wrap_t
        )
        key = (binding.image_index, hashlib.sha256(region.mask.tobytes()).digest())
        output = cache.get(key)
        if output is None:
            x, y, width, height = _padded_box(region.bounding_box, image.width, image.height, padding)
            pixels = np.asarray(image).copy()
            pixels[:, :, 3] = np.where(region.mask, pixels[:, :, 3], 0)
            digest = hashlib.sha256(region.mask.tobytes()).hexdigest()[:12]
            output = destination / f"image_{binding.image_index}_{digest}.png"
            Image.fromarray(pixels[y : y + height, x : x + width], "RGBA").save(output)
            cache[key] = output
        exported[binding.slot] = output
    return exported


def _binding_from_info(loaded: LoadedGltf, slot: TextureSlot, info: Any) -> TextureBinding:
    texture_index = getattr(info, "index", None)
    if texture_index is None:
        raise GltfLoadError(f"La textura {slot} no tiene índice")
    try:
        texture = loaded.document.textures[texture_index]
        image_index = texture.source
    except (IndexError, TypeError) as error:
        raise GltfLoadError(f"Índice de textura inválido para {slot}: {texture_index}") from error
    if image_index is None:
        raise GltfLoadError(f"La textura {texture_index} no tiene imagen compatible")
    transform_data = (getattr(info, "extensions", None) or {}).get("KHR_texture_transform", {})
    transform = TextureTransform(
        offset=tuple(transform_data.get("offset", [0.0, 0.0])),
        scale=tuple(transform_data.get("scale", [1.0, 1.0])),
        rotation=float(transform_data.get("rotation", 0.0)),
    )
    texcoord = int(transform_data.get("texCoord", getattr(info, "texCoord", 0) or 0))
    sampler = loaded.document.samplers[texture.sampler] if texture.sampler is not None else None
    wrap_s = _WRAP_CODES.get(getattr(sampler, "wrapS", 10497) or 10497, "REPEAT")
    wrap_t = _WRAP_CODES.get(getattr(sampler, "wrapT", 10497) or 10497, "REPEAT")
    color_space: Literal["sRGB", "linear"] = "sRGB" if slot in {"baseColor", "emissive"} else "linear"
    return TextureBinding(slot, texture_index, image_index, texcoord, transform, wrap_s, wrap_t, color_space)


def _buffer_view_data(loaded: LoadedGltf, view_index: int) -> bytes:
    try:
        view = loaded.document.bufferViews[view_index]
        buffer = loaded.document.buffers[view.buffer]
    except (IndexError, TypeError) as error:
        raise GltfLoadError(f"bufferView de imagen inválido: {view_index}") from error
    if buffer.uri is not None:
        if buffer.uri.startswith("data:"):
            raw = base64.b64decode(buffer.uri.split(",", 1)[1], validate=True)
        else:
            raw = local_uri_path(loaded.resource_directory, buffer.uri).read_bytes()
    else:
        raw = loaded.document.binary_blob()
    if raw is None:
        raise GltfLoadError("El GLB no contiene datos binarios de imagen")
    start, end = view.byteOffset or 0, (view.byteOffset or 0) + view.byteLength
    if end > len(raw):
        raise GltfLoadError("La imagen embebida excede su bufferView")
    return bytes(raw[start:end])


def _padded_box(
    box: tuple[int, int, int, int], image_width: int, image_height: int, padding: int
) -> tuple[int, int, int, int]:
    x, y, width, height = box
    left, top = max(0, x - padding), max(0, y - padding)
    right, bottom = min(image_width, x + width + padding), min(image_height, y + height + padding)
    return left, top, right - left, bottom - top
