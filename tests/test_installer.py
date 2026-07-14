"""Contratos CPU de perfiles de instalación."""

from pathlib import Path

import pytest

from atlas_splitter.installer import InstallationError, create_isolated_environment


def test_installation_rejects_an_unknown_profile_before_creating_a_venv(tmp_path: Path) -> None:
    with pytest.raises(InstallationError, match="Perfil no compatible"):
        create_isolated_environment(tmp_path, tmp_path / "environment", "unsupported")
    assert not (tmp_path / "environment").exists()
