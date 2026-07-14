"""Instalación explícita del runtime local de SAM 2 para WSL/Linux."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path

from atlas_splitter.models.manager import download_model


class InstallationError(RuntimeError):
    """No se pudo preparar el runtime local de atlas-splitter."""


def create_isolated_environment(
    project_root: Path, environment: Path | None = None, profile: str = "basic"
) -> Path:
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
        subprocess.run(
            [str(python), "-m", "pip", "install", "-e", extras[profile]], cwd=project_root, check=True
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise InstallationError(f"No se pudo crear el entorno aislado: {error}") from error
    return target


def install_runtime(model: str, python_executable: Path | None = None) -> Path:
    """Instala PyTorch CUDA, SAM 2 y un checkpoint local con pasos visibles."""
    if shutil.which("git") is None:
        raise InstallationError("Se necesita Git para descargar SAM 2.")
    python = python_executable or Path(sys.executable)
    sam2_root = Path.home() / ".local" / "share" / "atlas-splitter" / "sam2"
    try:
        subprocess.run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "torch==2.5.1",
                "torchvision==0.20.1",
                "--index-url",
                "https://download.pytorch.org/whl/cu121",
            ],
            check=True,
        )
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
        return download_model(model)
    except subprocess.CalledProcessError as error:
        raise InstallationError(f"La instalación falló con código {error.returncode}.") from error
