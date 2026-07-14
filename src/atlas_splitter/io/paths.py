"""Resolución segura de rutas declaradas por manifiestos locales."""

from __future__ import annotations

from pathlib import Path


class ProjectPathError(ValueError):
    """Una ruta de manifiesto intenta escapar del directorio del proyecto."""


def resolve_project_path(root: Path, relative_path: str) -> Path:
    """Devuelve una ruta existente o futura confinada a ``root``.

    Los manifiestos son datos editables. Por ello no aceptamos rutas absolutas,
    ni ``..``, ni enlaces simbólicos que apunten fuera del resultado local.
    """
    if not isinstance(relative_path, str) or not relative_path:
        raise ProjectPathError("La ruta del manifiesto debe ser texto no vacío.")
    candidate = Path(relative_path)
    # Pure Windows paths are not absolute on POSIX, and vice versa.
    if candidate.is_absolute() or (len(relative_path) > 1 and relative_path[1] == ":"):
        raise ProjectPathError("Las rutas absolutas no están permitidas en manifiestos.")
    if any(part == ".." for part in candidate.parts):
        raise ProjectPathError("La ruta del manifiesto no puede contener '..'.")
    resolved_root = root.resolve()
    resolved = (resolved_root / candidate).resolve(strict=False)
    try:
        resolved.relative_to(resolved_root)
    except ValueError as error:
        raise ProjectPathError("La ruta del manifiesto sale del directorio del proyecto.") from error
    return resolved
