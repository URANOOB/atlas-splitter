"""Validación pequeña y portable para manifiestos cargados por el add-on."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

MANIFEST_FILENAMES = frozenset({"project.json", "manifest.json", "objects_manifest.json"})
SUPPORTED_SCHEMA_VERSIONS = frozenset({"1.0"})


def resolve_manifest_path(filepath: str | Path) -> Path:
    """Resuelve una ruta local y rechaza nombres de archivo no compatibles."""
    path = Path(filepath).expanduser().resolve()
    if path.name not in MANIFEST_FILENAMES:
        raise ValueError("Selecciona project.json, manifest.json u objects_manifest.json.")
    if not path.is_file():
        raise ValueError(f"No existe el manifiesto: {path}")
    return path


def load_manifest(filepath: str | Path) -> tuple[Path, dict[str, Any]]:
    """Lee y valida el contrato mínimo, sin necesitar Blender."""
    path = resolve_manifest_path(filepath)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"No se pudo leer el manifiesto: {error}") from error
    if not isinstance(data, dict):
        raise ValueError("El manifiesto debe contener un objeto JSON.")
    version = data.get("schema_version")
    if version is not None and version not in SUPPORTED_SCHEMA_VERSIONS:
        raise ValueError(f"Versión de manifiesto no compatible: {version}.")
    if path.name == "project.json" and not isinstance(data.get("atlases"), list):
        raise ValueError("project.json no contiene una lista de atlas válida.")
    if path.name == "objects_manifest.json" and not isinstance(data.get("objects"), list):
        raise ValueError("objects_manifest.json no contiene una lista de objetos válida.")
    if path.name == "manifest.json" and not isinstance(data.get("elements"), list):
        raise ValueError("manifest.json no contiene una lista de elementos válida.")
    return path, data


def collection_name(raw_name: str, existing: set[str] | None = None) -> str:
    """Genera nombres estables, seguros y no duplicados para colecciones."""
    base = re.sub(r"[^A-Za-z0-9 _.-]+", "_", raw_name).strip(" ._") or "sin_nombre"
    names = existing or set()
    if base not in names:
        return base
    index = 2
    while f"{base} ({index})" in names:
        index += 1
    return f"{base} ({index})"
