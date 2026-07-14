"""Rutas de manifiestos: deben quedar confinadas al resultado local."""

from pathlib import Path

import pytest

from atlas_splitter.io.paths import ProjectPathError, resolve_project_path


@pytest.mark.parametrize("value", ["../private.png", "C:\\private.png", "/private.png"])
def test_resolve_project_path_rejects_escape_paths(tmp_path: Path, value: str) -> None:
    with pytest.raises(ProjectPathError):
        resolve_project_path(tmp_path, value)


def test_resolve_project_path_accepts_nested_unicode_and_spaces(tmp_path: Path) -> None:
    assert resolve_project_path(tmp_path, "grupo ñ/pieza uno.png") == tmp_path / "grupo ñ" / "pieza uno.png"
