"""Descarga explícita y comprobación local de modelos semánticos."""

from __future__ import annotations

import os
from pathlib import Path

from atlas_splitter.semantic_models.registry import get_semantic_model


def default_semantic_model_dir() -> Path:
    """Devuelve la raíz de caché exclusiva de modelos semánticos."""
    configured = os.environ.get("ATLAS_SPLITTER_SEMANTIC_MODEL_DIR")
    return (
        Path(configured).expanduser() if configured else Path.home() / ".cache" / "atlas-splitter" / "semantic-models"
    )


def semantic_model_path(name: str, directory: Path | None = None) -> Path:
    """Devuelve el directorio local esperado para un modelo registrado."""
    spec = get_semantic_model(name)
    return (directory or default_semantic_model_dir()) / spec.local_directory_name


def is_semantic_model_downloaded(name: str, directory: Path | None = None) -> bool:
    """Comprueba una instalación completa mínima sin contactar Internet."""
    path = semantic_model_path(name, directory)
    return path.is_dir() and (path / "config.json").is_file()


def download_semantic_model(name: str, directory: Path | None = None) -> Path:
    """Descarga un snapshot solo por una orden explícita del usuario."""
    spec = get_semantic_model(name)
    destination = semantic_model_path(name, directory)
    if is_semantic_model_downloaded(name, directory):
        return destination
    try:
        from huggingface_hub import snapshot_download
    except ImportError as error:
        raise RuntimeError('Instale el extra opcional: pip install -e ".[semantic]"') from error
    destination.parent.mkdir(parents=True, exist_ok=True)
    downloaded = snapshot_download(repo_id=spec.repository_id, local_dir=destination)
    path = Path(downloaded)
    if not (path / "config.json").is_file():
        raise OSError(f"El modelo descargado no contiene config.json: {path}")
    return path
