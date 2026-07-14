"""La preparación de release debe publicar sólo archivos públicos planos."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_prepare_release_assets_copies_only_the_public_contract(tmp_path: Path) -> None:
    python_artifacts = tmp_path / "downloaded" / "python"
    windows_artifacts = tmp_path / "downloaded" / "windows" / "AtlasSplitter-Lite"
    python_artifacts.mkdir(parents=True)
    windows_artifacts.mkdir(parents=True)
    version = "9.8.7"
    (python_artifacts / f"atlas_splitter-{version}-py3-none-any.whl").write_bytes(b"wheel")
    (python_artifacts / f"atlas_splitter-{version}.tar.gz").write_bytes(b"sdist")
    (python_artifacts / "atlas_splitter_blender.zip").write_bytes(b"addon")
    (windows_artifacts / "AtlasSplitter-Lite.zip").write_bytes(b"lite")
    (windows_artifacts / "internal.exe").write_bytes(b"not public")
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text("# Changelog", encoding="utf-8")
    output = tmp_path / "release-assets"

    subprocess.run(
        [
            sys.executable,
            "scripts/prepare_release_assets.py",
            "--version",
            version,
            "--python-artifacts",
            str(python_artifacts),
            "--windows-artifacts",
            str(windows_artifacts.parent),
            "--output",
            str(output),
            "--changelog",
            str(changelog),
        ],
        check=True,
        cwd=Path(__file__).parents[1],
    )

    assert {path.name for path in output.iterdir()} == {
        f"atlas_splitter-{version}-py3-none-any.whl",
        f"atlas_splitter-{version}.tar.gz",
        "AtlasSplitter-Lite.zip",
        "atlas_splitter_blender.zip",
        "CHANGELOG.md",
        "SHA256SUMS.txt",
    }
    checksums = (output / "SHA256SUMS.txt").read_text(encoding="ascii")
    assert "internal.exe" not in checksums
