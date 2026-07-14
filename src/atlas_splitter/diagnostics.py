"""Diagnósticos del entorno local requeridos por atlas-splitter."""

from __future__ import annotations

import importlib.util
import platform
import shutil
import sys
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory


@dataclass(frozen=True)
class DiagnosticCheck:
    """Resultado de una comprobación individual."""

    name: str
    ok: bool
    detail: str
    critical: bool = False

    @property
    def status(self) -> str:
        """Etiqueta apta para una interfaz de usuario no técnica."""
        if self.ok:
            return "LISTO"
        return "REQUIERE ATENCIÓN" if self.critical else "OPCIONAL"


def _module_version(module_name: str) -> str | None:
    if importlib.util.find_spec(module_name) is None:
        return None
    module = __import__(module_name)
    return str(getattr(module, "__version__", "instalado"))


def _check_zip() -> DiagnosticCheck:
    try:
        with TemporaryDirectory() as directory:
            destination = Path(directory) / "probe.zip"
            with zipfile.ZipFile(destination, "w") as archive:
                archive.writestr("probe.txt", "ok")
            valid = zipfile.is_zipfile(destination)
        return DiagnosticCheck("ZIP", valid, "creación y lectura correctas", critical=True)
    except OSError as error:
        return DiagnosticCheck("ZIP", False, str(error), critical=True)


def _check_psd() -> DiagnosticCheck:
    if importlib.util.find_spec("psd_tools") is None:
        return DiagnosticCheck("PSD", False, "psd-tools no instalado")
    try:
        from PIL import Image
        from psd_tools import PSDImage

        with TemporaryDirectory() as directory:
            destination = Path(directory) / "probe.psd"
            document = PSDImage.new("RGB", (2, 2), depth=8)
            document.create_pixel_layer(Image.new("RGBA", (2, 2)), name="Probe")
            document.save(destination)
            valid = PSDImage.open(destination).size == (2, 2)
        return DiagnosticCheck("PSD", valid, "creación y lectura correctas")
    except (OSError, ValueError) as error:
        return DiagnosticCheck("PSD", False, str(error))


def _check_pillow_webp(module_version: Callable[[str], str | None]) -> DiagnosticCheck:
    version = module_version("PIL")
    if version is None:
        return DiagnosticCheck("Pillow con WEBP", False, "Pillow no instalado")
    from PIL import features

    supported = bool(features.check("webp"))
    return DiagnosticCheck(
        "Pillow con WEBP",
        supported,
        f"Pillow {version}; WEBP {'activo' if supported else 'no disponible'}",
    )


def _check_writable_directory(directory: Path) -> DiagnosticCheck:
    """Comprueba escritura temporal sin dejar archivos residuales."""
    try:
        directory.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(dir=directory) as probe:
            Path(probe, "write-probe.txt").write_text("ok", encoding="utf-8")
        return DiagnosticCheck("Permisos de escritura", True, str(directory.resolve()))
    except OSError as error:
        return DiagnosticCheck("Permisos de escritura", False, str(error), critical=True)


def collect_diagnostics(
    checkpoint_dir: Path | None = None,
    module_version: Callable[[str], str | None] = _module_version,
) -> list[DiagnosticCheck]:
    """Recopila información del host sin modificar su estado."""
    checks = [
        DiagnosticCheck(
            "Python",
            sys.version_info >= (3, 11),
            f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            critical=True,
        ),
        DiagnosticCheck("Sistema operativo", True, f"{platform.system()} {platform.release()}"),
    ]
    torch_version = module_version("torch")
    if torch_version is None:
        checks.append(DiagnosticCheck("PyTorch", False, "no instalado", critical=True))
        checks.append(DiagnosticCheck("CUDA", False, "PyTorch no está disponible"))
    else:
        import torch

        cuda_available = bool(torch.cuda.is_available())
        cuda_detail = "no disponible"
        if cuda_available:
            try:
                device_name = torch.cuda.get_device_name(0)
                free, total = torch.cuda.mem_get_info(0)
                cuda_detail = f"{device_name}; {free // 2**20} MiB libres de {total // 2**20} MiB"
            except (RuntimeError, AssertionError) as error:
                cuda_available = False
                cuda_detail = f"no disponible: {error}"
        checks.append(DiagnosticCheck("PyTorch", True, torch_version, critical=True))
        checks.append(DiagnosticCheck("CUDA", cuda_available, cuda_detail))
    checks.append(_check_pillow_webp(module_version))
    for label, module in (("Trimesh", "trimesh"), ("NetworkX", "networkx")):
        version = module_version(module)
        checks.append(DiagnosticCheck(label, version is not None, version or "no instalado"))
    for label, module in (("OpenCV", "cv2"), ("Geometría glTF", "pygltflib")):
        version = module_version(module)
        checks.append(DiagnosticCheck(label, version is not None, version or "no instalado"))
    checkpoint_root = checkpoint_dir or Path.home() / ".cache" / "atlas-splitter" / "checkpoints"
    has_checkpoint = checkpoint_root.exists() and any(checkpoint_root.glob("*.pt"))
    checks.append(DiagnosticCheck("Checkpoint SAM 2", has_checkpoint, str(checkpoint_root)))
    semantic_root = Path.home() / ".cache" / "atlas-splitter" / "semantic-models"
    has_semantic_model = semantic_root.is_dir() and any(semantic_root.glob("*/config.json"))
    checks.append(DiagnosticCheck("Qwen3-VL local", has_semantic_model, str(semantic_root)))
    checks.append(DiagnosticCheck("Caché SAM 2", checkpoint_root.is_dir(), str(checkpoint_root)))
    checks.append(DiagnosticCheck("Caché semántica", semantic_root.is_dir(), str(semantic_root)))
    draco_root = Path.cwd() / "draco" / "gltf"
    has_draco = draco_root.is_dir() and any(draco_root.iterdir())
    checks.append(DiagnosticCheck("Decodificador Draco", has_draco, str(draco_root)))
    checks.append(
        DiagnosticCheck(
            "Blender",
            shutil.which("blender") is not None,
            shutil.which("blender") or "no encontrado en PATH",
        )
    )
    try:
        free = shutil.disk_usage(Path.cwd()).free // 2**30
        checks.append(DiagnosticCheck("Espacio libre", free >= 2, f"{free} GiB libres en la unidad de trabajo"))
    except OSError as error:
        checks.append(DiagnosticCheck("Espacio libre", False, str(error)))
    checks.append(_check_writable_directory(Path.cwd()))
    checks.append(_check_psd())
    checks.append(_check_zip())
    return checks


def has_critical_failures(checks: list[DiagnosticCheck]) -> bool:
    """Indica si falta algún requisito marcado como crítico."""
    return any(check.critical and not check.ok for check in checks)
