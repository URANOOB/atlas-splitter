import zipfile

import pytest

from atlas_splitter.io.zip_writer import write_zip


def test_zip_writer_preserves_atlas_folder_and_is_not_overwritable(tmp_path) -> None:
    atlas = tmp_path / "results" / "atlas_one"
    atlas.mkdir(parents=True)
    (atlas / "manifest.json").write_text("{}", encoding="utf-8")
    destination = tmp_path / "bundle.zip"
    write_zip(destination, [atlas])
    with zipfile.ZipFile(destination) as archive:
        assert archive.namelist() == ["atlas_one/manifest.json"]
    with pytest.raises(FileExistsError):
        write_zip(destination, [atlas])


def test_zip_writer_never_includes_its_destination_inside_the_result(tmp_path) -> None:
    atlas = tmp_path / "atlas"
    atlas.mkdir()
    (atlas / "manifest.json").write_text("{}", encoding="utf-8")
    destination = atlas / "atlas.zip"

    write_zip(destination, [atlas])

    with zipfile.ZipFile(destination) as archive:
        assert "atlas/atlas.zip" not in archive.namelist()
