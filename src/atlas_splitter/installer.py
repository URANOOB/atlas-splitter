"""Instalación explícita del runtime local de SAM 2 para WSL/Linux."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from atlas_splitter.models.manager import download_model


class InstallationError(RuntimeError):
    """No se pudo preparar el runtime local de atlas-splitter."""


def install_runtime(model: str) -> Path:
    """Instala PyTorch CUDA, SAM 2 y un checkpoint local con pasos visibles."""
    if shutil.which("git") is None:
        raise InstallationError("Se necesita Git para descargar SAM 2.")
    sam2_root = Path.home() / ".local" / "share" / "atlas-splitter" / "sam2"
    try:
        subprocess.run(
            [
                sys.executable,
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
            [sys.executable, "-m", "pip", "install", "-e", str(sam2_root)],
            check=True,
            env=environment,
        )
        return download_model(model)
    except subprocess.CalledProcessError as error:
        raise InstallationError(f"La instalación falló con código {error.returncode}.") from error
