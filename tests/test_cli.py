from typer.testing import CliRunner

from atlas_splitter.cli import app, interactive_arguments, translate_simple_args

runner = CliRunner()


def test_models_list() -> None:
    result = runner.invoke(app, ["models", "list"])
    assert result.exit_code == 0
    assert "sam2-small" in result.stdout


def test_new_modes_expose_help() -> None:
    assert runner.invoke(app, ["glb", "--help"]).exit_code == 0
    assert runner.invoke(app, ["semantic", "--help"]).exit_code == 0
    semantic_3d_help = runner.invoke(app, ["semantic-3d", "--help"])
    assert semantic_3d_help.exit_code == 0
    assert "--texture-index" in semantic_3d_help.stdout
    assert "--uv-set" in semantic_3d_help.stdout


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


def test_simple_command_translates_output_and_calibration() -> None:
    arguments = translate_simple_args(["atlas.webp", "simple-output", "--calibration-pixels", "4"])
    assert arguments == ["run", "atlas.webp", "--output", "simple-output", "--calibration-pixels", "4"]


def test_simple_command_keeps_glb_subcommand() -> None:
    assert translate_simple_args(["glb", "room.glb", "--atlas", "atlas.webp"]) == [
        "glb",
        "room.glb",
        "--atlas",
        "atlas.webp",
    ]


def test_install_help_is_available_without_installing_dependencies() -> None:
    result = runner.invoke(app, ["install", "--help"])
    assert result.exit_code == 0
    assert "virtualenv" in result.stdout


def test_interactive_atlas_mode_creates_a_yaml_and_simple_run_args(tmp_path, monkeypatch) -> None:
    answers = iter([False, str(tmp_path / "atlas.webp"), str(tmp_path / "output"), 6])
    monkeypatch.setattr("atlas_splitter.cli.typer.confirm", lambda *args, **kwargs: next(answers))
    monkeypatch.setattr("atlas_splitter.cli.typer.prompt", lambda *args, **kwargs: next(answers))
    arguments = interactive_arguments(tmp_path)
    assert arguments[:2] == ["run", str(tmp_path / "atlas.webp")]
    assert arguments[-1] == "6"
    assert (tmp_path / "atlas-splitter.yaml").is_file()
