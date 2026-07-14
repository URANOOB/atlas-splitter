"""Rutas de manifiestos: deben quedar confinadas al resultado local."""

from pathlib import Path

import pytest

from atlas_splitter.io.paths import LegacyProjectWarning, ProjectPathError, resolve_project_path, resolve_source_image


@pytest.mark.parametrize("value", ["../private.png", "C:\\private.png", "/private.png"])
def test_resolve_project_path_rejects_escape_paths(tmp_path: Path, value: str) -> None:
    with pytest.raises(ProjectPathError):
        resolve_project_path(tmp_path, value)


def test_resolve_project_path_accepts_nested_unicode_and_spaces(tmp_path: Path) -> None:
    assert resolve_project_path(tmp_path, "grupo ñ/pieza uno.png") == tmp_path / "grupo ñ" / "pieza uno.png"


def test_resolve_source_image_uses_a_relative_project_path(tmp_path: Path) -> None:
    source = tmp_path / "source" / "atlas.webp"
    source.parent.mkdir()
    source.write_bytes(b"atlas")

    assert resolve_source_image(tmp_path, {"source_file": "source/atlas.webp", "source_file_portable": True}) == source


def test_resolve_source_image_accepts_an_existing_legacy_absolute_path(tmp_path: Path) -> None:
    source = tmp_path / "legacy.webp"
    source.write_bytes(b"atlas")

    with pytest.warns(LegacyProjectWarning, match="no es portable"):
        assert resolve_source_image(tmp_path, {"source_file": str(source)}) == source


def test_resolve_source_image_rejects_a_missing_legacy_absolute_path(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Regenera o migra"):
        resolve_source_image(tmp_path, {"source_file": str(tmp_path / "missing.webp")})


def test_resolve_project_path_rejects_a_symlink_that_escapes(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.webp"
    outside.write_bytes(b"outside")
    link = tmp_path / "source"
    try:
        link.symlink_to(tmp_path.parent, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"No se pueden crear enlaces simbólicos en este entorno: {error}")

    with pytest.raises(ProjectPathError):
        resolve_project_path(tmp_path, "source/outside.webp")
