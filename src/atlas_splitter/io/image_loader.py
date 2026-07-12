"""Descubrimiento y carga segura de atlas WEBP."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, UnidentifiedImageError

from atlas_splitter.exceptions import AtlasSplitterError

LOGGER = logging.getLogger(__name__)
SUPPORTED_SUFFIXES = {".webp"}


class ImageLoadError(AtlasSplitterError):
    """La entrada no es una imagen WEBP legible."""


@dataclass(frozen=True)
class LoadedImage:
    """Imagen RGBA normalizada y sus metadatos esenciales."""

    path: Path
    pixels: np.ndarray
    sha256: str

    @property
    def width(self) -> int:
        return int(self.pixels.shape[1])

    @property
    def height(self) -> int:
        return int(self.pixels.shape[0])


def discover_images(source: Path, recursive: bool = False) -> list[Path]:
    """Encuentra WEBP de forma determinista e informa de archivos ignorados."""
    if source.is_file():
        if source.suffix.lower() not in SUPPORTED_SUFFIXES:
            LOGGER.warning("Se ignora el formato no soportado: %s", source)
            return []
        return [source]
    if not source.is_dir():
        raise ImageLoadError(f"No existe la entrada: {source}")
    candidates = source.rglob("*") if recursive else source.glob("*")
    files = sorted((item for item in candidates if item.is_file()), key=lambda item: str(item).lower())
    for item in files:
        if item.suffix.lower() not in SUPPORTED_SUFFIXES:
            LOGGER.warning("Se ignora el formato no soportado: %s", item)
    return [item for item in files if item.suffix.lower() in SUPPORTED_SUFFIXES]


def load_image(path: Path) -> LoadedImage:
    """Abre un WEBP, lo normaliza a RGBA y calcula el hash del archivo original."""
    try:
        with Image.open(path) as image:
            image.load()
            rgba = image.convert("RGBA")
            pixels = np.asarray(rgba, dtype=np.uint8).copy()
    except (OSError, UnidentifiedImageError) as error:
        raise ImageLoadError(f"No se pudo abrir '{path}': imagen WEBP corrupta o inválida") from error
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return LoadedImage(path=path, pixels=pixels, sha256=digest)
