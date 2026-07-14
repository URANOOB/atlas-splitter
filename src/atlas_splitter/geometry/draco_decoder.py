"""Adaptador aislado para el decodificador Draco local distribuido con el proyecto."""

# ruff: noqa: E501
from __future__ import annotations

import base64
import json
import logging
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NoReturn

import numpy as np

from atlas_splitter.exceptions import DracoDecodeError, DracoDecoderUnavailableError
from atlas_splitter.geometry.glb_loader import LoadedGltf

LOGGER = logging.getLogger(__name__)
_NODE_WSL = Path("/mnt/c/Program Files/nodejs/node.exe")


@dataclass(frozen=True)
class DracoDiagnostic:
    """Diagnóstico estructurado de una invocación del proceso aislado."""

    code: str
    message: str
    decoder_js: Path | None = None
    decoder_wasm: Path | None = None
    returncode: int | None = None


@dataclass(frozen=True)
class DracoGeometry:
    """Geometría descomprimida sin interpretación adicional del material."""

    attributes: dict[str, np.ndarray]
    triangle_indices: np.ndarray


class DracoDecoder:
    """Ejecuta Node local y sólo los dos artefactos Draco proporcionados."""

    def __init__(self, project_root: Path | None = None, node_executable: Path | None = None) -> None:
        root = project_root or Path(__file__).resolve().parents[3]
        candidate = root / "Draco" / "gltf"
        if not candidate.is_dir():
            candidate = root / "draco" / "gltf"  # Compatibilidad con árboles existentes sensibles a mayúsculas.
        self.decoder_js = candidate / "draco_decoder.js"
        self.decoder_wasm = candidate / "draco_decoder.wasm"
        configured = os.environ.get("ATLAS_SPLITTER_NODE")
        self.node_executable = node_executable or (Path(configured) if configured else self._find_node())
        self.last_diagnostic: DracoDiagnostic | None = None

    def decode(self, loaded: LoadedGltf, extension: dict[str, Any]) -> DracoGeometry:
        """Decodifica una extensión KHR Draco y valida todo su contrato de salida."""
        self._check_available()
        view_index = extension.get("bufferView")
        attributes = extension.get("attributes")
        if not isinstance(view_index, int) or not isinstance(attributes, dict) or not attributes:
            self._fail("invalid_draco_extension", "KHR_draco_mesh_compression no declara bufferView/attributes válidos.")
        encoded = _buffer_view_bytes(loaded, view_index)
        request = {"bytes": base64.b64encode(encoded).decode("ascii"), "attributes": attributes}
        try:
            completed = subprocess.run(
                [
                    str(self.node_executable),
                    "-e",
                    _NODE_PROGRAM,
                    _node_process_path(self.decoder_js, self.node_executable),
                    _node_process_path(self.decoder_wasm, self.node_executable),
                ],
                input=json.dumps(request), text=True, capture_output=True, check=False, timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            self._fail("draco_process_failed", f"No se pudo ejecutar el decodificador Draco local: {error}")
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or "sin detalle"
            self._fail("draco_decode_failed", detail, completed.returncode)
        try:
            payload = json.loads(completed.stdout)
            raw_attributes = payload["attributes"]
            raw_faces = payload["faces"]
            result = {
                str(name): np.asarray(values, dtype=np.float64)
                for name, values in dict(raw_attributes).items()
            }
            faces = np.asarray(raw_faces, dtype=np.int64)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            self._fail("invalid_draco_output", f"La salida de Draco no tiene el formato esperado: {error}")
        positions = result.get("POSITION")
        if positions is None or positions.ndim != 2 or positions.shape[1] != 3:
            self._fail("missing_draco_position", "Draco no devolvió POSITION VEC3.")
        if faces.ndim != 2 or faces.shape[1] != 3 or np.any(faces < 0) or np.any(faces >= len(positions)):
            self._fail("invalid_draco_faces", "Draco devolvió índices de caras inválidos.")
        for name, values in result.items():
            if values.ndim != 2 or len(values) != len(positions):
                self._fail("invalid_draco_attribute", f"El atributo Draco {name} no coincide con POSITION.")
        LOGGER.info("Primitiva Draco decodificada localmente: %s vértices, %s triángulos", len(positions), len(faces))
        return DracoGeometry(result, faces)

    def _find_node(self) -> Path | None:
        found = shutil.which("node")
        if found:
            return Path(found)
        return _NODE_WSL if _NODE_WSL.is_file() else None

    def _check_available(self) -> None:
        missing = [path for path in (self.decoder_js, self.decoder_wasm) if not path.is_file()]
        if missing or self.node_executable is None or not self.node_executable.exists():
            self._fail(
                "draco_decoder_unavailable",
                "KHR_draco_mesh_compression requiere Node y draco_decoder.js/draco_decoder.wasm locales.",
            )

    def _fail(self, code: str, message: str, returncode: int | None = None) -> NoReturn:
        self.last_diagnostic = DracoDiagnostic(code, message, self.decoder_js, self.decoder_wasm, returncode)
        error_type = DracoDecoderUnavailableError if code == "draco_decoder_unavailable" else DracoDecodeError
        raise error_type(f"{code}: {message}")


def _buffer_view_bytes(loaded: LoadedGltf, view_index: int) -> bytes:
    try:
        view = loaded.document.bufferViews[view_index]
        data = loaded.document.binary_blob()
    except (IndexError, TypeError) as error:
        raise DracoDecodeError(f"invalid_draco_buffer_view: bufferView inválido: {view_index}") from error
    if data is None or view.buffer != 0:
        raise DracoDecodeError("invalid_draco_buffer_view: Draco requiere un buffer binario GLB local.")
    start = view.byteOffset or 0
    end = start + view.byteLength
    if end > len(data):
        raise DracoDecodeError("invalid_draco_buffer_view: bufferView Draco fuera de rango.")
    return bytes(data[start:end])


def _node_process_path(path: Path, node_executable: Path | None) -> str:
    """Convierte una ruta WSL para el Node de Windows, sin depender de ``wslpath``."""
    path_text = path.as_posix()
    if node_executable is None or not node_executable.as_posix().startswith("/mnt/"):
        return str(path.resolve())
    parts = path_text.split("/")
    if len(parts) >= 4 and parts[1] == "mnt" and len(parts[2]) == 1:
        return f"{parts[2].upper()}:\\" + "\\".join(parts[3:])
    return str(path.resolve())


_NODE_PROGRAM = r'''const fs = require("fs");
const [decoderPath, wasmPath] = process.argv.slice(1);
const DracoDecoderModule = require(decoderPath);
const input = JSON.parse(fs.readFileSync(0, "utf8"));
(async () => {
  const module = await DracoDecoderModule({ wasmBinary: fs.readFileSync(wasmPath) });
  const buffer = new module.DecoderBuffer();
  const bytes = Buffer.from(input.bytes, "base64");
  buffer.Init(new Int8Array(bytes), bytes.length);
  const decoder = new module.Decoder();
  if (decoder.GetEncodedGeometryType(new Int8Array(bytes)) !== module.TRIANGULAR_MESH) throw new Error("El flujo sólo admite mallas triangulares Draco.");
  const mesh = new module.Mesh(); const status = decoder.DecodeBufferToMesh(buffer, mesh);
  if (!status.ok() || mesh.num_points() < 1) throw new Error(status.error_msg() || "Draco no pudo decodificar la malla.");
  const attributes = {};
  for (const [name, uniqueId] of Object.entries(input.attributes)) {
    const attribute = decoder.GetAttributeByUniqueId(mesh, uniqueId);
    if (!attribute || attribute.ptr === 0) throw new Error(`No existe el atributo Draco ${name}.`);
    const out = new module.DracoFloat32Array();
    if (!decoder.GetAttributeFloatForAllPoints(mesh, attribute, out)) throw new Error(`No se pudo leer ${name}.`);
    const values = []; for (let i = 0; i < out.size(); i++) values.push(out.GetValue(i));
    const components = attribute.num_components(); const rows = [];
    for (let i = 0; i < values.length; i += components) rows.push(values.slice(i, i + components));
    attributes[name] = rows; module.destroy(out);
  }
  const faces = []; const face = new module.DracoInt32Array();
  for (let i = 0; i < mesh.num_faces(); i++) { decoder.GetFaceFromMesh(mesh, i, face); faces.push([face.GetValue(0), face.GetValue(1), face.GetValue(2)]); }
  module.destroy(face); module.destroy(mesh); module.destroy(decoder); module.destroy(buffer);
  process.stdout.write(JSON.stringify({ attributes, faces }));
})().catch(error => { process.stderr.write(String(error.stack || error)); process.exitCode = 1; });'''
