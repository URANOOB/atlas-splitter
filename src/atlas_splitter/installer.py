"""Instalación explícita del runtime local de SAM 2 para WSL/Linux."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
import venv
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from atlas_splitter.models.manager import checkpoint_path


class InstallationError(RuntimeError):
    """No se pudo preparar el runtime local de atlas-splitter."""


OFFICIAL_REPOSITORY = "git+https://github.com/URANOOB/atlas-splitter.git"


def build_optional_install_command(
    component: str, *, device: str = "auto", python_executable: Path | None = None, system: str | None = None
) -> list[str]:
    """Construye una instalación portable sin descargar ni asumir CUDA."""
    extras = {"geometry": "geometry", "ai": "vision,semantic", "all": "vision,semantic,geometry"}
    if component not in extras:
        raise InstallationError("Componente no compatible. Use geometry, ai o all.")
    if device not in {"auto", "cpu", "cuda", "mps"}:
        raise InstallationError("Dispositivo no compatible. Use auto, cpu, cuda o mps.")
    current_system = system or platform.system()
    if device == "mps" and current_system != "Darwin":
        raise InstallationError("MPS sólo está disponible en macOS.")
    if device == "cuda" and current_system == "Darwin":
        raise InstallationError("CUDA no está disponible en macOS; use mps o cpu.")
    python = python_executable or Path(sys.executable)
    try:
        version("atlas-splitter")
        requirement = f"atlas-splitter[{extras[component]}]"
    except PackageNotFoundError:
        requirement = f"atlas-splitter[{extras[component]}] @ {OFFICIAL_REPOSITORY}"
    return [str(python), "-m", "pip", "install", requirement]


def install_optional_components(component: str, python_executable: Path | None = None, *, device: str = "auto") -> None:
    """Instala extras sin depender del directorio actual ni fijar CUDA."""
    try:
        subprocess.run(
            build_optional_install_command(component, device=device, python_executable=python_executable), check=True
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise InstallationError(f"No se pudo instalar {component}: {error}") from error


def create_isolated_environment(project_root: Path, environment: Path | None = None, profile: str = "basic") -> Path:
    """Instala atlas-splitter y sus extras en un virtualenv local multiplataforma."""
    extras = {
        "basic": ".",
        "geometry": ".[geometry]",
        "vision": ".[vision]",
        "semantic": ".[semantic]",
        "all": ".[vision,semantic,geometry]",
    }
    if profile not in extras:
        raise InstallationError("Perfil no compatible. Use basic, geometry, vision, semantic o all.")
    target = environment or project_root / ".atlas-splitter-venv"
    try:
        if not target.exists():
            venv.EnvBuilder(with_pip=True).create(target)
        python = target / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        if not python.is_file():
            raise InstallationError(f"El entorno aislado no contiene Python: {python}")
        subprocess.run([str(python), "-m", "pip", "install", "--upgrade", "pip"], check=True)
        subprocess.run([str(python), "-m", "pip", "install", "-e", extras[profile]], cwd=project_root, check=True)
    except (OSError, subprocess.CalledProcessError) as error:
        raise InstallationError(f"No se pudo crear el entorno aislado: {error}") from error
    return target


def install_runtime(model: str, python_executable: Path | None = None) -> Path:
    """Compatibilidad heredada: prepara dependencias, nunca descarga el modelo."""
    if shutil.which("git") is None:
        raise InstallationError("Se necesita Git para descargar SAM 2.")
    python = python_executable or Path(sys.executable)
    sam2_root = Path.home() / ".local" / "share" / "atlas-splitter" / "sam2"
    try:
        subprocess.run([str(python), "-m", "pip", "install", "torch", "torchvision"], check=True)
        if not (sam2_root / ".git").is_dir():
            sam2_root.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                ["git", "clone", "https://github.com/facebookresearch/sam2.git", str(sam2_root)],
                check=True,
            )
        environment = os.environ | {"SAM2_BUILD_CUDA": "0"}
        subprocess.run(
            [str(python), "-m", "pip", "install", "-e", str(sam2_root)],
            check=True,
            env=environment,
        )
        return checkpoint_path(model)
    except subprocess.CalledProcessError as error:
        raise InstallationError(f"La instalación falló con código {error.returncode}.") from error
