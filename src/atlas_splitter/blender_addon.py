"""Exportación portable del add-on de Blender incluido en el wheel."""

from __future__ import annotations

import importlib.resources
import zipfile
from pathlib import Path

from atlas_splitter import __version__

ADDON_ARCHIVE_NAME = "atlas_splitter_blender.zip"
_REQUIRED_FILES = frozenset({"__init__.py", "operators.py", "panels.py", "properties.py", "manifest.py"})


def addon_info() -> dict[str, str]:
    """Metadatos que no requieren Blender ni acceso a red."""
    return {
        "version": __version__,
        "minimum_blender": "4.0",
        "manifest_schema": "1.0",
        "installation": "En Blender: Edit > Preferences > Add-ons > Install..., selecciona el ZIP y actívalo.",
    }


def export_blender_addon(output: Path, *, overwrite: bool = False) -> Path:
    """Crea un ZIP instalable usando recursos del paquete instalado."""
    destination = output / ADDON_ARCHIVE_NAME if output.suffix.lower() != ".zip" else output
    destination = destination.expanduser().resolve()
    if destination.exists() and not overwrite:
        raise FileExistsError(f"El add-on ya existe y no se sobrescribirá: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.unlink(missing_ok=True)
    resource_root = importlib.resources.files("atlas_splitter.resources").joinpath("blender_addon")
    # Durante desarrollo el recurso se fuerza al wheel al construir; en el
    # árbol fuente sigue en su directorio público original.
    if not resource_root.is_dir():
        resource_root = Path(__file__).resolve().parents[2] / "blender_addon"
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            _write_resources(archive, resource_root, "atlas_splitter_blender")
        validate_blender_addon_zip(temporary)
        temporary.replace(destination)
    except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile):
        temporary.unlink(missing_ok=True)
        raise
    return destination


def _write_resources(archive: zipfile.ZipFile, source: object, prefix: str) -> None:
    """Escribe un árbol de ``Traversable`` o ``Path`` sin depender del repo instalado."""
    directory = source
    if not hasattr(directory, "iterdir"):
        raise ValueError("No se encontraron los recursos del add-on de Blender.")
    for child in directory.iterdir():
        name = f"{prefix}/{child.name}"
        if child.is_dir():
            _write_resources(archive, child, name)
        elif child.is_file() and "__pycache__" not in child.parts:
            contents = child.read_bytes()
            if child.name == "__init__.py":
                contents = contents.replace(b"__ATLAS_SPLITTER_VERSION__", __version__.encode("ascii"))
            archive.writestr(name, contents)


def validate_blender_addon_zip(path: Path) -> None:
    """Comprueba el contrato mínimo antes de anunciar el archivo al usuario."""
    with zipfile.ZipFile(path) as archive:
        names = {Path(name).name for name in archive.namelist() if not name.endswith("/")}
    missing = sorted(_REQUIRED_FILES - names)
    if missing:
        raise ValueError(f"El ZIP del add-on está incompleto: faltan {', '.join(missing)}.")
