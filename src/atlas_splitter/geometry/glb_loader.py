"""Carga local de documentos GLB y glTF sin descargar recursos."""

import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from urllib.parse import unquote, urlparse

from pygltflib import GLTF2  # type: ignore[import-untyped]

from atlas_splitter.exceptions import GltfLoadError

_UNSUPPORTED_COMPRESSED_EXTENSIONS = frozenset({"EXT_meshopt_compression", "KHR_texture_basisu"})


@dataclass(frozen=True)
class GltfDiagnostic:
    """Diagnóstico estructurado para funciones glTF que no pueden decodificarse localmente."""

    code: str
    severity: Literal["warning", "error"]
    message: str
    extension: str | None = None


@dataclass(frozen=True)
class LoadedGltf:
    """Documento glTF junto con su directorio de recursos locales."""

    document: GLTF2
    source_path: Path
    resource_directory: Path
    diagnostics: tuple[GltfDiagnostic, ...] = ()


def load_gltf(path: Path) -> LoadedGltf:
    """Carga un ``.glb`` o ``.gltf`` local y conserva sus rutas de recursos."""
    source_path = path.expanduser().resolve()
    if not source_path.is_file():
        raise GltfLoadError(f"No existe el archivo glTF: {source_path}")
    suffix = source_path.suffix.lower()
    if suffix not in {".glb", ".gltf"}:
        raise GltfLoadError("Se esperaba un archivo .glb o .gltf")
    try:
        document = GLTF2().load_binary(str(source_path)) if suffix == ".glb" else GLTF2().load(str(source_path))
    except (OSError, ValueError, TypeError, IndexError, struct.error) as error:
        raise GltfLoadError(f"No se pudo leer el glTF '{source_path.name}': {error}") from error
    return LoadedGltf(
        document=document,
        source_path=source_path,
        resource_directory=source_path.parent,
        diagnostics=_extension_diagnostics(document),
    )


def local_uri_path(resource_directory: Path, uri: str) -> Path:
    """Resuelve una URI relativa local, rechazando esquemas de red."""
    parsed = urlparse(uri)
    if parsed.scheme or parsed.netloc:
        raise GltfLoadError(f"No se permiten recursos remotos en glTF: {uri}")
    resolved = (resource_directory / unquote(uri)).resolve()
    try:
        resolved.relative_to(resource_directory.resolve())
    except ValueError as error:
        raise GltfLoadError(f"La URI sale del directorio del modelo: {uri}") from error
    return resolved


def _extension_diagnostics(document: GLTF2) -> tuple[GltfDiagnostic, ...]:
    """Expone extensiones comprimidas para que el pipeline no las procese en silencio."""
    used = set(getattr(document, "extensionsUsed", None) or [])
    for mesh in document.meshes or []:
        for primitive in mesh.primitives:
            extensions = getattr(primitive, "extensions", None) or {}
            if isinstance(extensions, dict):
                used.update(extensions)
    diagnostics = [
        GltfDiagnostic(
            code="draco_local_decoder_required",
            severity="warning",
            message="La extensión 'KHR_draco_mesh_compression' se decodificará con el adaptador local.",
            extension="KHR_draco_mesh_compression",
        )
        for extension in sorted(used & {"KHR_draco_mesh_compression"})
    ] + [
        GltfDiagnostic(
            code="unsupported_compressed_extension",
            severity="error",
            message=f"La extensión '{extension}' requiere un decodificador que no está instalado.",
            extension=extension,
        )
        for extension in sorted(used & _UNSUPPORTED_COMPRESSED_EXTENSIONS)
    ]
    return tuple(diagnostics)
