"""Empaquetado ZIP transaccional de resultados por atlas."""

from __future__ import annotations

import zipfile
from pathlib import Path


def write_zip(destination: Path, atlas_directories: list[Path]) -> None:
    """Crea un ZIP estándar y lo publica solo cuando está completo."""
    if destination.exists():
        raise FileExistsError(f"El ZIP ya existe y no se sobrescribirá: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for atlas_directory in atlas_directories:
                for item in sorted(atlas_directory.rglob("*")):
                    if item.is_file():
                        archive.write(item, item.relative_to(atlas_directory.parent))
        temporary.replace(destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
