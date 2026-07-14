"""Resolución segura de rutas declaradas por manifiestos locales."""

from __future__ import annotations

import warnings
from pathlib import Path, PureWindowsPath


class ProjectPathError(ValueError):
    """Una ruta de manifiesto intenta escapar del directorio del proyecto."""


class LegacyProjectWarning(UserWarning):
    """Un proyecto anterior conserva una dependencia de una ruta externa."""


def resolve_project_path(root: Path, relative_path: str) -> Path:
    """Devuelve una ruta existente o futura confinada a ``root``.

    Los manifiestos son datos editables. Por ello no aceptamos rutas absolutas,
    ni ``..``, ni enlaces simbólicos que apunten fuera del resultado local.
    """
    if not isinstance(relative_path, str) or not relative_path:
        raise ProjectPathError("La ruta del manifiesto debe ser texto no vacío.")
    candidate = Path(relative_path)
    # Pure Windows paths are not absolute on POSIX, and vice versa.
    if candidate.is_absolute() or PureWindowsPath(relative_path).is_absolute():
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


def resolve_source_image(project_root: Path, manifest: dict[str, object]) -> Path:
    """Resuelve el atlas de un proyecto, incluyendo manifiestos antiguos.

    Los proyectos nuevos declaran una ruta relativa y confinada. Los manifiestos
    previos a la copia local no tenían el marcador ``source_file_portable`` y
    pueden conservar una ruta absoluta existente para que sigan siendo legibles.
    """
    source_file = manifest.get("source_file")
    if not isinstance(source_file, str) or not source_file:
        raise ProjectPathError("El manifiesto no identifica un atlas fuente válido.")
    if Path(source_file).is_absolute() or PureWindowsPath(source_file).is_absolute():
        if manifest.get("source_file_portable") is True:
            raise ProjectPathError("Un manifiesto portable no puede usar una ruta fuente absoluta.")
        source = Path(source_file).expanduser()
        if not source.is_file():
            raise FileNotFoundError(
                "El atlas del proyecto antiguo ya no existe. Regenera o migra el proyecto para hacerlo portable."
            )
        warnings.warn(
            "Este proyecto antiguo depende de un atlas externo y no es portable. "
            "Regénéralo o migra el proyecto para copiar el atlas dentro del resultado.",
            LegacyProjectWarning,
            stacklevel=2,
        )
        return source.resolve()
    source = resolve_project_path(project_root, source_file)
    if not source.is_file():
        raise FileNotFoundError(f"No se encontró el atlas copiado del proyecto: {source_file}")
    return source
