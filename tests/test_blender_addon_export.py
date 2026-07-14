"""El ZIP del add-on se arma desde recursos, sin Blender instalado."""

import zipfile
from pathlib import Path

from atlas_splitter.blender_addon import export_blender_addon, validate_blender_addon_zip


def test_export_blender_addon_has_required_files(tmp_path: Path) -> None:
    archive = export_blender_addon(tmp_path)

    validate_blender_addon_zip(archive)
    with zipfile.ZipFile(archive) as contents:
        names = set(contents.namelist())
    assert "atlas_splitter_blender/__init__.py" in names
    assert "atlas_splitter_blender/manifest.py" in names
