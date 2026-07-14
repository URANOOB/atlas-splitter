"""Contratos CPU de perfiles de instalación."""

import os
from pathlib import Path

import pytest

from atlas_splitter.installer import InstallationError, create_isolated_environment


def test_installation_rejects_an_unknown_profile_before_creating_a_venv(tmp_path: Path) -> None:
    with pytest.raises(InstallationError, match="Perfil no compatible"):
        create_isolated_environment(tmp_path, tmp_path / "environment", "unsupported")
    assert not (tmp_path / "environment").exists()


def test_installation_accepts_the_visual_segmentation_profile(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[list[str]] = []
    monkeypatch.setattr("atlas_splitter.installer.venv.EnvBuilder.create", lambda *_args: None)
    monkeypatch.setattr("atlas_splitter.installer.subprocess.run", lambda command, **_kwargs: calls.append(command))
    python = tmp_path / "env" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    python.parent.mkdir(parents=True)
    python.touch()

    create_isolated_environment(tmp_path, tmp_path / "env", "vision")

    assert calls[-1][-1] == ".[vision]"
