"""Empaquetado ZIP transaccional de resultados por atlas."""

from __future__ import annotations

import zipfile
from pathlib import Path


def write_zip(destination: Path, atlas_directories: list[Path]) -> None:
    """Crea un ZIP estándar y lo publica solo cuando está completo."""
    destination = destination.resolve()
    if destination.exists():
        raise FileExistsError(f"El ZIP ya existe y no se sobrescribirá: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    # Un intento interrumpido no debe contaminar una nueva publicación.
    temporary.unlink(missing_ok=True)
    published = False
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for atlas_directory in atlas_directories:
                root = atlas_directory.resolve()
                for item in sorted(atlas_directory.rglob("*")):
                    if not item.is_file() or item.is_symlink():
                        continue
                    resolved_item = item.resolve()
                    try:
                        resolved_item.relative_to(root)
                    except ValueError:
                        continue
                    if resolved_item in {destination, temporary} or resolved_item.suffix.lower() == ".zip":
                        continue
                    archive.write(resolved_item, resolved_item.relative_to(root.parent))
        temporary.replace(destination)
        published = True
    finally:
        if not published:
            temporary.unlink(missing_ok=True)
