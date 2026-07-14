from typer.testing import CliRunner

from atlas_splitter.cli import app, interactive_arguments, translate_simple_args

runner = CliRunner()


def _help(arguments: list[str]) -> str:
    """Obtiene ayuda sin depender del ancho de terminal del runner CI."""
    result = runner.invoke(app, arguments, terminal_width=200)
    assert result.exit_code == 0
    return result.stdout


def test_models_list() -> None:
    result = runner.invoke(app, ["models", "list"])
    assert result.exit_code == 0
    assert "sam2-small" in result.stdout


def test_new_modes_expose_help() -> None:
    _help(["glb", "--help"])
    _help(["semantic", "--help"])
    _help(["semantic-3d", "--help"])


def test_debug_is_a_global_cli_option() -> None:
    _help(["--debug", "--help"])


def test_glb_error_exposes_a_stable_code_without_traceback(tmp_path) -> None:
    result = runner.invoke(app, ["glb", str(tmp_path / "missing.gltf")])
    assert result.exit_code != 0
    assert "AS-GLB-002" in result.stderr
    assert "Causa probable:" in result.stderr
    assert "Traceback" not in result.stderr


def test_glb_option_validation_uses_a_stable_cli_code(tmp_path) -> None:
    result = runner.invoke(app, ["glb", str(tmp_path / "model.gltf"), "--group-by", "invalid"])
    assert result.exit_code != 0
    assert "AS-CLI-004" in result.stderr
    assert "Solucion:" in result.stderr


def test_glb_rejects_a_non_positive_uv_tolerance(tmp_path) -> None:
    result = runner.invoke(app, ["glb", str(tmp_path / "model.gltf"), "--uv-tolerance", "0"])
    assert result.exit_code != 0
    assert "--uv-tolerance debe ser mayor que cero" in result.stderr


def test_run_rejects_a_missing_source(tmp_path) -> None:
    result = runner.invoke(app, ["run", str(tmp_path / "atlas.webp")])
    assert result.exit_code != 0


def test_run_help_exposes_expected_stage_one_options() -> None:
    _help(["run", "--help"])


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
    _help(["install", "--help"])


def test_doctor_uses_ascii_readiness_indicators() -> None:
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code in {0, 1}
    assert "[OK] Extraer atlas con GLB y UV" in result.stdout


def test_interactive_atlas_mode_returns_simple_reproducible_run_args(tmp_path, monkeypatch) -> None:
    source = tmp_path / "atlas.webp"
    source.touch()
    answers = iter(["1", str(source), str(tmp_path / "output"), 6])
    monkeypatch.setattr("atlas_splitter.cli.typer.confirm", lambda *args, **kwargs: True)
    monkeypatch.setattr("atlas_splitter.cli.typer.prompt", lambda *args, **kwargs: next(answers))
    arguments = interactive_arguments(tmp_path)
    assert arguments[:2] == ["run", str(source)]
    assert arguments[-1] == "6"


def test_interactive_menu_can_run_doctor_without_requesting_paths(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("atlas_splitter.cli.typer.prompt", lambda *args, **kwargs: "3")
    assert interactive_arguments(tmp_path) == ["doctor"]
