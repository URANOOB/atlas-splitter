"""Prepara los únicos archivos públicos permitidos en una release."""

from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path

PUBLIC_ARTIFACT_FILES = ("AtlasSplitter-Lite.zip", "atlas_splitter_blender.zip")


def _single_file(root: Path, pattern: str) -> Path:
    matches = sorted(path for path in root.rglob(pattern) if path.is_file())
    if len(matches) != 1:
        raise FileNotFoundError(f"Se esperaba exactamente un artefacto {pattern} en {root}; encontrados: {matches}")
    return matches[0]


def prepare_release_assets(
    version: str,
    python_artifacts: Path,
    windows_artifacts: Path,
    output: Path,
    changelog: Path,
) -> list[Path]:
    """Copia artefactos públicos a una carpeta limpia y comprobable localmente."""
    if not version:
        raise ValueError("La versión de release no puede estar vacía.")
    wheel = _single_file(python_artifacts, f"atlas_splitter-{version}-py3-none-any.whl")
    sdist = _single_file(python_artifacts, f"atlas_splitter-{version}.tar.gz")
    addon = _single_file(python_artifacts, PUBLIC_ARTIFACT_FILES[1])
    lite = _single_file(windows_artifacts, PUBLIC_ARTIFACT_FILES[0])
    if not changelog.is_file():
        raise FileNotFoundError(f"No existe CHANGELOG.md: {changelog}")
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    copied: list[Path] = []
    for source in (wheel, sdist, lite, addon, changelog):
        target = output / source.name
        shutil.copy2(source, target)
        copied.append(target)
    checksums = output / "SHA256SUMS.txt"
    checksums.write_text(
        "".join(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n" for path in copied), encoding="ascii"
    )
    return [*copied, checksums]


def main() -> None:
    """Ejecuta la preparación de release sin publicar nada."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--python-artifacts", type=Path, required=True)
    parser.add_argument("--windows-artifacts", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("release-assets"))
    parser.add_argument("--changelog", type=Path, default=Path("CHANGELOG.md"))
    arguments = parser.parse_args()
    prepare_release_assets(
        arguments.version,
        arguments.python_artifacts,
        arguments.windows_artifacts,
        arguments.output,
        arguments.changelog,
    )


if __name__ == "__main__":
    main()
