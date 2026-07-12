"""Descarga deliberada, atómica y local de checkpoints."""

from __future__ import annotations

import shutil
from pathlib import Path
from urllib.request import urlopen

from atlas_splitter.models.registry import ModelSpec, get_model


def default_checkpoint_dir() -> Path:
    """Ubicación de caché por usuario, independiente del directorio del proyecto."""
    return Path.home() / ".cache" / "atlas-splitter" / "checkpoints"


def checkpoint_path(name: str, directory: Path | None = None) -> Path:
    """Ruta local esperada para un checkpoint registrado."""
    spec = get_model(name)
    return (directory or default_checkpoint_dir()) / spec.checkpoint_filename


def is_downloaded(name: str, directory: Path | None = None) -> bool:
    """Comprueba que el checkpoint local existe y no está vacío."""
    destination = checkpoint_path(name, directory)
    return destination.is_file() and destination.stat().st_size > 0


def download_model(name: str, directory: Path | None = None) -> Path:
    """Descarga un checkpoint solo tras invocación explícita y lo publica atómicamente."""
    spec: ModelSpec = get_model(name)
    destination = checkpoint_path(name, directory)
    if is_downloaded(name, directory):
        return destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")
    try:
        with urlopen(spec.download_url, timeout=60) as response, temporary.open("wb") as output:
            shutil.copyfileobj(response, output)
        if temporary.stat().st_size == 0:
            raise OSError("La descarga del checkpoint quedó vacía")
        temporary.replace(destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return destination
