"""Interfaz de línea de comandos de atlas-splitter."""

import sys
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table
from typer.main import get_command

from atlas_splitter.config import apply_cli_overrides, load_config
from atlas_splitter.diagnostics import collect_diagnostics, has_critical_failures
from atlas_splitter.exceptions import AtlasSplitterError
from atlas_splitter.installer import InstallationError, install_runtime
from atlas_splitter.io.image_loader import ImageLoadError, discover_images
from atlas_splitter.io.zip_writer import write_zip
from atlas_splitter.models.manager import download_model as fetch_model
from atlas_splitter.models.manager import is_downloaded
from atlas_splitter.models.registry import MODELS, get_model
from atlas_splitter.pipeline import process_image
from atlas_splitter.segmentation.sam2_engine import Sam2Engine

app = typer.Typer(help="Separa atlas de texturas mediante procesamiento local.", no_args_is_help=True)
models_app = typer.Typer(help="Gestiona checkpoints de SAM 2.", no_args_is_help=True)
app.add_typer(models_app, name="models")
console = Console()


def _planned(command: str) -> None:
    console.print(f"[yellow]'{command}' estará disponible en una etapa posterior.[/yellow]")
    raise typer.Exit(code=2)


@app.command()
def doctor() -> None:
    """Comprueba los requisitos locales sin descargar ni modificar nada."""
    checks = collect_diagnostics()
    table = Table(title="atlas-split doctor")
    table.add_column("Comprobación")
    table.add_column("Estado")
    table.add_column("Detalle")
    for check in checks:
        table.add_row(check.name, "OK" if check.ok else "FALTA", check.detail)
    console.print(table)
    if has_critical_failures(checks):
        raise typer.Exit(code=1)


@app.command()
def run(
    source: Annotated[Path, typer.Argument(help="Archivo WEBP o directorio de entrada")],
    config: Annotated[Path | None, typer.Option(help="Archivo de configuración YAML")] = None,
    device: Annotated[str | None, typer.Option(help="auto, cpu o cuda")] = None,
    model: Annotated[str | None, typer.Option(help="sam2-tiny o sam2-small")] = None,
    output: Annotated[Path | None, typer.Option(help="Directorio de resultados")] = None,
    zip_path: Annotated[Path | None, typer.Option("--zip", help="ZIP de salida")] = None,
    min_area: Annotated[int | None, typer.Option(help="Área mínima de máscara")] = None,
    confidence: Annotated[float | None, typer.Option(help="Confianza mínima")] = None,
    stability: Annotated[float | None, typer.Option(help="Estabilidad mínima")] = None,
    duplicate_iou: Annotated[float | None, typer.Option(help="IoU para duplicados")] = None,
    calibration_pixels: Annotated[
        int | None,
        typer.Option(
            "--calibration-pixels",
            "--edge-padding",
            help="Expande en píxeles las máscaras SAM 2 para recuperar bordes",
        ),
    ] = None,
    padding: Annotated[int | None, typer.Option(help="Margen de recorte")] = None,
    crop_elements: Annotated[bool | None, typer.Option(help="Recortar al bounding box")] = None,
    recursive: Annotated[bool, typer.Option(help="Recorrer directorios recursivamente")] = False,
    fail_fast: Annotated[bool, typer.Option(help="Detenerse al primer error")] = False,
    max_inference_size: Annotated[int | None, typer.Option(help="Máximo para inferencia SAM 2")] = None,
    tile_size: Annotated[int | None, typer.Option(help="Tamaño de tile para SAM 2")] = None,
    tile_overlap: Annotated[int | None, typer.Option(help="Solapamiento de tiles")] = None,
) -> None:
    """Procesa WEBP locales mediante segmentación clásica."""
    try:
        loaded_config = load_config(config)
        effective_config = apply_cli_overrides(
            loaded_config,
            {
                "device": device,
                "model": model,
                "segmentation.min_area": min_area,
                "segmentation.confidence": confidence,
                "segmentation.stability": stability,
                "segmentation.duplicate_iou": duplicate_iou,
                "segmentation.sam2_edge_padding": calibration_pixels,
                "processing.padding": padding,
                "processing.crop_elements": crop_elements,
            },
        )
    except (OSError, ValidationError, ValueError) as error:
        raise typer.BadParameter(str(error), param_hint="--config") from error
    if max_inference_size or tile_size or tile_overlap:
        console.print("[yellow]Las opciones de inferencia SAM 2 se activarán en una etapa posterior.[/yellow]")
    try:
        images = discover_images(source, recursive)
    except ImageLoadError as error:
        raise typer.BadParameter(str(error), param_hint="source") from error
    if not images:
        raise typer.BadParameter("No se encontraron archivos WEBP válidos.", param_hint="source")
    output_root = output or Path("outputs")
    if output is None:
        console.print("[cyan]Salida predeterminada:[/cyan] outputs/")
    failures = 0
    completed: list[Path] = []
    sam_engine = Sam2Engine(
        effective_config.model,
        effective_config.device,
        effective_config.segmentation.sam2_points_per_side,
        effective_config.segmentation.sam2_points_per_batch,
        effective_config.segmentation.sam2_edge_padding,
    )
    for image_path in images:
        try:
            result = process_image(
                image_path,
                output_root,
                effective_config,
                sam_engine,
            )
            completed.append(result)
            console.print(f"[green]Procesado:[/green] {image_path} -> {result}")
        except (AtlasSplitterError, OSError, ValueError) as error:
            failures += 1
            console.print(f"[red]Error en {image_path}: {error}[/red]")
            if fail_fast:
                break
    if failures:
        raise typer.Exit(code=1)
    if zip_path:
        try:
            write_zip(zip_path, completed)
            console.print(f"[green]ZIP creado:[/green] {zip_path}")
        except OSError as error:
            console.print(f"[red]No se pudo crear el ZIP: {error}[/red]")
            raise typer.Exit(code=1) from error


def translate_simple_args(arguments: list[str]) -> list[str]:
    """Traduce ``atlas-splitter archivo [salida]`` a la interfaz avanzada."""
    commands = {"doctor", "install", "inspect", "models", "run"}
    if not arguments or arguments[0] in commands or arguments[0].startswith("-"):
        return arguments
    translated = ["run", arguments[0]]
    remaining = arguments[1:]
    if remaining and not remaining[0].startswith("-"):
        translated.extend(("--output", remaining[0]))
        remaining = remaining[1:]
    return [*translated, *remaining]


def main() -> None:
    """Punto de entrada que conserva subcomandos y ofrece la sintaxis corta."""
    get_command(app).main(args=translate_simple_args(sys.argv[1:]), prog_name="atlas-splitter")


@app.command()
def install(
    model: Annotated[str, typer.Option(help="Checkpoint SAM 2 que se descargará")] = "sam2-small",
) -> None:
    """Prepara PyTorch CUDA, SAM 2 y el checkpoint en WSL/Linux."""
    console.print("Instalando PyTorch CUDA, SAM 2 y el checkpoint local. Esto puede tardar varios minutos.")
    try:
        checkpoint = install_runtime(model)
    except (InstallationError, OSError, ValueError) as error:
        raise typer.BadParameter(str(error), param_hint="--model") from error
    console.print(f"[green]Instalación lista:[/green] {checkpoint}")


@models_app.command("list")
def list_models() -> None:
    """Lista los modelos disponibles y el estado de su checkpoint local."""
    table = Table(title="Modelos SAM 2")
    table.add_column("Modelo")
    table.add_column("Checkpoint")
    table.add_column("Estado")
    for name, spec in MODELS.items():
        table.add_row(name, spec.checkpoint_filename, "instalado" if is_downloaded(name) else "no descargado")
    console.print(table)


@models_app.command("download")
def download_model(model: Annotated[str, typer.Argument(help="Nombre del modelo")]) -> None:
    """Descarga explícitamente un checkpoint de SAM 2 a la caché local."""
    try:
        get_model(model)
        with console.status(f"Descargando {model}..."):
            destination = fetch_model(model)
    except (OSError, ValueError) as error:
        raise typer.BadParameter(str(error), param_hint="model") from error
    console.print(f"[green]Checkpoint disponible:[/green] {destination}")


@app.command()
def inspect(archive: Annotated[Path, typer.Argument(help="ZIP generado por atlas-split")]) -> None:
    """Muestra los manifiestos contenidos en un ZIP de resultados."""
    import json
    import zipfile

    try:
        with zipfile.ZipFile(archive) as contents:
            manifests = [name for name in contents.namelist() if name.endswith("manifest.json")]
            if not manifests:
                raise ValueError("El ZIP no contiene manifest.json")
            for name in manifests:
                manifest = json.loads(contents.read(name))
                console.print(f"{name}: {manifest['final_elements']} elementos; fuente {manifest['source_file']}")
    except (OSError, ValueError, zipfile.BadZipFile, KeyError) as error:
        raise typer.BadParameter(str(error), param_hint="archive") from error
