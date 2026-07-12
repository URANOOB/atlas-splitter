from typer.testing import CliRunner

from atlas_splitter.cli import app

runner = CliRunner()


def test_models_list() -> None:
    result = runner.invoke(app, ["models", "list"])
    assert result.exit_code == 0
    assert "sam2-small" in result.stdout


def test_run_rejects_a_missing_source(tmp_path) -> None:
    result = runner.invoke(app, ["run", str(tmp_path / "atlas.webp")])
    assert result.exit_code != 0


def test_run_help_exposes_expected_stage_one_options() -> None:
    result = runner.invoke(app, ["run", "--help"])
    assert result.exit_code == 0
    assert "--device" in result.stdout
    assert "--min-area" in result.stdout


def test_cli_processes_a_webp(tmp_path) -> None:
    from PIL import Image

    source = tmp_path / "atlas.webp"
    image = Image.new("RGBA", (20, 20), (0, 0, 0, 0))
    image.paste((255, 0, 0, 255), (3, 3, 15, 15))
    image.save(source, "WEBP", lossless=True)
    result = runner.invoke(app, ["run", str(source), "--output", str(tmp_path / "output"), "--min-area", "20"])
    assert result.exit_code == 0
    assert "Procesado" in result.stdout


def test_cli_creates_and_inspects_zip(tmp_path) -> None:
    from PIL import Image

    source = tmp_path / "atlas.webp"
    image = Image.new("RGBA", (20, 20), (0, 0, 0, 0))
    image.paste((255, 0, 0, 255), (3, 3, 15, 15))
    image.save(source, "WEBP", lossless=True)
    archive = tmp_path / "result.zip"
    result = runner.invoke(
        app,
        [
            "run",
            str(source),
            "--output",
            str(tmp_path / "output"),
            "--zip",
            str(archive),
            "--min-area",
            "20",
        ],
    )
    assert result.exit_code == 0
    assert archive.is_file()
    inspected = runner.invoke(app, ["inspect", str(archive)])
    assert inspected.exit_code == 0
    assert "1 elementos" in inspected.stdout
