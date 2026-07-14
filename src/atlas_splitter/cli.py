"""Interfaz de línea de comandos de atlas-splitter."""

import json
import logging
import sys
from pathlib import Path
from typing import Annotated, cast

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table
from typer.main import get_command

from atlas_splitter.blender.script_writer import (
    write_atlas_rebuild_script,
    write_object_rebuild_script,
    write_single_object_rebuild_script,
)
from atlas_splitter.config import apply_cli_overrides, load_config
from atlas_splitter.diagnostics import collect_diagnostics, has_critical_failures
from atlas_splitter.domain import slugify
from atlas_splitter.exceptions import (
    AtlasSplitterError,
    GltfLoadError,
    InputValidationError,
    InvalidReviewError,
    PrimitiveDecodeError,
    SemanticInferenceError,
    SemanticModelUnavailableError,
)
from atlas_splitter.geometry.glb_exporter import GroupBy, export_glb
from atlas_splitter.geometry.glb_loader import load_gltf
from atlas_splitter.geometry.model_inspector import inspect_model
from atlas_splitter.geometry.object_grouping import ExportedAtlas, write_object_manifest
from atlas_splitter.geometry.project_writer import write_project_manifest
from atlas_splitter.geometry.texture_association import load_atlas_bindings, resolve_external_atlases
from atlas_splitter.installer import InstallationError, create_isolated_environment, install_runtime
from atlas_splitter.io.image_loader import ImageLoadError, discover_images
from atlas_splitter.io.zip_writer import write_zip
from atlas_splitter.models.manager import download_model as fetch_model
from atlas_splitter.models.manager import is_downloaded
from atlas_splitter.models.registry import MODELS, get_model
from atlas_splitter.pipeline import process_image
from atlas_splitter.reporting.html_report import generate_html_report
from atlas_splitter.review import apply_review, create_review_template
from atlas_splitter.segmentation.sam2_engine import Sam2Engine
from atlas_splitter.semantic.grouping_service import group_extracted_atlas
from atlas_splitter.semantic.qwen3_vl_engine import Qwen3VLSemanticGroupingBackend
from atlas_splitter.semantic3d import Semantic3DConfig, group_semantic_3d
from atlas_splitter.semantic_models.manager import download_semantic_model, is_semantic_model_downloaded
from atlas_splitter.semantic_models.registry import SEMANTIC_MODELS, get_semantic_model

app = typer.Typer(help="Separa atlas de texturas mediante procesamiento local.", no_args_is_help=False)
models_app = typer.Typer(help="Gestiona checkpoints de SAM 2.", no_args_is_help=True)
semantic_models_app = typer.Typer(help="Gestiona modelos semánticos locales.", no_args_is_help=True)
app.add_typer(models_app, name="models")
app.add_typer(semantic_models_app, name="semantic-models")
console = Console()
LOGGER = logging.getLogger(__name__)


@app.callback()
def common_options(
    debug: Annotated[bool, typer.Option("--debug", help="Muestra traceback completo si ocurre un error.")] = False,
) -> None:
    """Opciones comunes; el traceback se reserva para depuracion explicita."""
    if debug:
        LOGGER.info("Modo de depuracion CLI activado.")


def _planned(command: str) -> None:
    console.print(f"[yellow]'{command}' estará disponible en una etapa posterior.[/yellow]")
    raise typer.Exit(code=2)


def interactive_arguments(cwd: Path) -> list[str]:
    """Guía local con rutas validadas y devuelve un comando reproducible."""
    while True:
        console.print("\n[bold]Atlas Splitter[/bold] — un atlas es una imagen con varias texturas.")
        choice = typer.prompt(
            "Elige: 1) atlas 2D, 2) atlas + GLB/UV, 3) doctor, 4) modelos locales",
            default="1",
        ).strip()
        if choice == "3":
            return ["doctor"]
        if choice == "4":
            return ["models", "list"]
        if choice not in {"1", "2"}:
            console.print("[yellow]Elige 1, 2, 3 o 4.[/yellow]")
            continue
        if choice == "2":
            arguments = _interactive_glb_arguments(cwd)
        else:
            arguments = _interactive_atlas_arguments(cwd)
        if arguments is None:
            console.print("[yellow]Volviste al menú principal.[/yellow]")
            continue
        console.print("\n[bold]Resumen antes de ejecutar[/bold]")
        console.print(f"[cyan]Comando reproducible:[/cyan] atlas-splitter {' '.join(arguments)}")
        if typer.confirm("¿Ejecutar este comando?", default=True):
            return arguments


def _interactive_atlas_arguments(cwd: Path) -> list[str] | None:
    source = _prompt_existing_path("Ruta de un atlas WEBP o carpeta (vacío = atrás)", file_or_directory=True)
    if source is None:
        return None
    output = Path(typer.prompt("Carpeta de salida", default=str(cwd / "outputs"))).expanduser()
    padding = typer.prompt("Píxeles extra para recuperar bordes", default=4, type=int)
    return ["run", str(source), "--output", str(output), "--calibration-pixels", str(padding)]


def _interactive_glb_arguments(cwd: Path) -> list[str] | None:
    model = _prompt_existing_path("Ruta del archivo GLB/glTF (vacío = atrás)", suffixes={".glb", ".gltf"})
    if model is None:
        return None
    atlas_directory = _prompt_existing_path("Carpeta de atlas (vacío = atrás)", directory=True)
    if atlas_directory is None:
        return None
    output = Path(typer.prompt("Carpeta de salida", default=str(cwd / "outputs"))).expanduser()
    console.print("[dim]UV indica qué zona del atlas usa cada cara del modelo; no se modifica el GLB.[/dim]")
    console.print(f"[yellow]Si usa Draco, se comprobará el decodificador local en {cwd / 'draco' / 'gltf'}.[/yellow]")
    console.print("Al terminar, abre output/blender/rebuild_scene.py en Blender y ejecútalo desde Scripting.")
    return ["glb", str(model), "--atlas-dir", str(atlas_directory), "--output", str(output)]


def _prompt_existing_path(
    label: str,
    *,
    file_or_directory: bool = False,
    directory: bool = False,
    suffixes: set[str] | None = None,
) -> Path | None:
    """Pide una ruta local; una entrada vacía permite retroceder sin error."""
    while True:
        raw = typer.prompt(label, default="").strip()
        if not raw:
            return None
        path = Path(raw).expanduser()
        valid = (file_or_directory and (path.is_file() or path.is_dir())) or (directory and path.is_dir()) or (
            suffixes is not None and path.is_file() and path.suffix.lower() in suffixes
        )
        if valid:
            return path
        console.print(f"[red]Ruta no válida: {path}. Revisa que exista y vuelve a intentarlo.[/red]")


@app.command()
def doctor(format: Annotated[str, typer.Option("--format", help="text o json")] = "text") -> None:
    """Comprueba los requisitos locales sin descargar ni modificar nada."""
    checks = collect_diagnostics()
    if format == "json":
        payload = [{"name": item.name, "ok": item.ok, "status": item.status, "detail": item.detail} for item in checks]
        console.print_json(
            json.dumps(payload)
        )
        if has_critical_failures(checks):
            raise typer.Exit(code=1)
        return
    if format != "text":
        raise typer.BadParameter("--format debe ser text o json")
    table = Table(title="atlas-split doctor")
    table.add_column("Comprobación")
    table.add_column("Estado")
    table.add_column("Detalle")
    for check in checks:
        style = "green" if check.ok else "yellow" if not check.critical else "red"
        table.add_row(check.name, f"[{style}]{check.status}[/{style}]", check.detail)
    console.print(table)
    ready = {check.name for check in checks if check.ok}
    console.print("\n[bold]Tu equipo está listo para:[/bold]")
    console.print(f"{'[OK]' if 'Geometría glTF' in ready else '[X]'} Extraer atlas con GLB y UV")
    console.print(f"{'[OK]' if 'OpenCV' in ready else '[X]'} Separar atlas con procesamiento clásico")
    console.print(f"{'[OK]' if 'Qwen3-VL local' in ready else '[X]'} Usar Qwen3-VL local")
    if has_critical_failures(checks):
        raise typer.Exit(code=1)


@app.command()
def glb(
    model: Annotated[Path, typer.Argument(help="Archivo GLB o glTF local")],
    atlas: Annotated[Path | None, typer.Option(help="Atlas externo opcional")] = None,
    atlas_dir: Annotated[
        Path | None, typer.Option(help="Directorio de atlas WEBP asociados por nombre de nodo")
    ] = None,
    bindings: Annotated[Path | None, typer.Option(help="YAML de bindings atlas/nodos confirmado manualmente")] = None,
    output: Annotated[Path, typer.Option(help="Directorio de resultados")] = Path("outputs"),
    texture_index: Annotated[int | None, typer.Option(help="Índice de textura a usar")] = None,
    texture_slot: Annotated[str, typer.Option(help="Mapa de material a extraer")] = "baseColor",
    group_by: Annotated[str, typer.Option(help="node, mesh, primitive o uv-island")] = "uv-island",
    uv_tolerance: Annotated[float, typer.Option(help="Tolerancia para comparar extremos de aristas UV")] = 1e-6,
    allow_unbound_atlas: Annotated[
        bool,
        typer.Option("--allow-unbound-atlas", help="Confirma una asociación manual para GLB sin materiales"),
    ] = False,
    flip_v: Annotated[
        bool, typer.Option("--flip-v", help="Invierte V para atlas externos con origen superior")
    ] = False,
) -> None:
    """Exporta regiones UV y materiales de un GLB/glTF enteramente local."""
    if group_by not in {"node", "mesh", "primitive", "uv-island"}:
        raise typer.BadParameter(str(InputValidationError("--group-by debe ser node, mesh, primitive o uv-island")))
    if uv_tolerance <= 0:
        raise typer.BadParameter(str(InputValidationError("--uv-tolerance debe ser mayor que cero")))
    if texture_slot not in {"baseColor", "normal", "metallicRoughness", "occlusion", "emissive"}:
        raise typer.BadParameter("--texture-slot no es válido")
    if atlas is not None and not atlas.is_file():
        raise typer.BadParameter(str(InputValidationError("El atlas externo no existe")), param_hint="--atlas")
    if sum(value is not None for value in (atlas, atlas_dir, bindings)) > 1:
        raise typer.BadParameter(str(InputValidationError("Use solo uno de --atlas, --atlas-dir o --bindings")))
    if bindings is not None and not bindings.is_file():
        raise typer.BadParameter(str(InputValidationError("El YAML de bindings no existe")), param_hint="--bindings")
    try:
        loaded = load_gltf(model)
        if atlas_dir is not None or bindings is not None:
            associations = (
                load_atlas_bindings(bindings, loaded)
                if bindings is not None
                else resolve_external_atlases(loaded, _required_atlas_directory(atlas_dir), texture_slot)
            )
            exported_atlases = [
                ExportedAtlas(
                    atlas_path=association.atlas_path,
                    output_directory=output / association.atlas_path.stem,
                    manifest=export_glb(
                        loaded,
                        output / association.atlas_path.stem,
                        atlas=association.atlas_path,
                        texture_index=texture_index,
                        image_index=association.image_index,
                        texture_slot=association.texture_slot,
                        group_by=cast(GroupBy, group_by),
                        allow_unbound_atlas=allow_unbound_atlas or association.manual_confirmation,
                        node_indices=set(association.node_indices),
                        flip_v=association.flip_v if bindings is not None else flip_v,
                        uv_set=association.uv_set,
                        force_external_atlas=association.manual_confirmation,
                        uv_tolerance=uv_tolerance,
                    ),
                    flip_v=association.flip_v if bindings is not None else flip_v,
                    association_method=association.method,
                    association_confidence=association.confidence,
                    manual_confirmation=association.manual_confirmation,
                    uv_set=association.uv_set,
                    texture_slot=association.texture_slot,
                )
                for association in associations
            ]
            object_manifest = write_object_manifest(
                output / "objects_manifest.json", loaded.source_path, exported_atlases
            )
            write_project_manifest(output / "project.json", loaded.source_path, exported_atlases)
            write_object_rebuild_script(
                output / "blender" / "rebuild_scene.py", loaded.source_path, output / "objects_manifest.json"
            )
            for exported_atlas in exported_atlases:
                write_atlas_rebuild_script(
                    exported_atlas.output_directory / "blender" / "rebuild_scene.py",
                    loaded.source_path,
                    output / "objects_manifest.json",
                    exported_atlas.atlas_path,
                    separate_loose_parts=True,
                )
            for object_group in object_manifest.objects:
                write_single_object_rebuild_script(
                    output
                    / "objects"
                    / f"{object_group.node_index:02d}-{slugify(object_group.node_name)}"
                    / "rebuild_object.py",
                    loaded.source_path,
                    output / "objects_manifest.json",
                    object_group.object_id,
                )
            element_count = sum(len(atlas.manifest.elements) for atlas in exported_atlases)
        else:
            manifest = export_glb(
                loaded,
                output,
                atlas=atlas,
                texture_index=texture_index,
                texture_slot=texture_slot,
                group_by=cast(GroupBy, group_by),
                allow_unbound_atlas=allow_unbound_atlas,
                flip_v=flip_v,
                uv_tolerance=uv_tolerance,
            )
            element_count = len(manifest.elements)
    except (GltfLoadError, PrimitiveDecodeError, OSError, ValueError) as error:
        raise typer.BadParameter(str(error), param_hint="model") from error
    for diagnostic in loaded.diagnostics:
        console.print(f"[yellow]{diagnostic.code}: {diagnostic.message}[/yellow]")
    console.print(f"[green]GLB exportado:[/green] {element_count} regiones; grupo={group_by}; slot={texture_slot}")
    console.print(
        f"[cyan]Salida:[/cyan] {output.resolve()}; manifiesto=uv_manifest.json; Blender=blender/rebuild_scene.py"
    )


def _required_atlas_directory(value: Path | None) -> Path:
    """Estrecha el tipo tras validar el modo de asociacion del comando GLB."""
    if value is None:
        raise ValueError("Se requiere un directorio de atlas para la asociacion automatica.")
    return value


@app.command()
def preview(output: Annotated[Path, typer.Argument(help="Directorio de una ejecución existente")]) -> None:
    """Regenera el reporte HTML local de una extracción visual ya terminada."""
    try:
        report = generate_html_report(output)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise typer.BadParameter(str(error), param_hint="output") from error
    console.print(f"[green]Reporte local:[/green] {report}")


@app.command("review")
def review(output: Annotated[Path, typer.Argument(help="Directorio de una ejecución existente")]) -> None:
    """Crea la plantilla review.json sin ejecutar inferencia otra vez."""
    try:
        template = create_review_template(output)
    except InvalidReviewError as error:
        raise typer.BadParameter(str(error), param_hint="output") from error
    console.print(f"[green]Revisión creada:[/green] {template}")


@app.command("apply-review")
def apply_manual_review(review_file: Annotated[Path, typer.Argument(help="Archivo review.json editable")]) -> None:
    """Aplica grupos manuales sin modificar los PNG ni las máscaras originales."""
    try:
        applied = apply_review(review_file)
    except InvalidReviewError as error:
        raise typer.BadParameter(str(error), param_hint="review_file") from error
    console.print(f"[green]Revisión aplicada:[/green] {applied}")


@app.command()
def semantic(
    atlas: Annotated[Path, typer.Argument(help="Atlas local sin GLB")],
    output: Annotated[Path, typer.Option(help="Directorio de resultados")] = Path("outputs"),
) -> None:
    """Informa las limitaciones del modo semántico sin geometría."""
    if not atlas.is_file():
        raise typer.BadParameter("El atlas no existe", param_hint="atlas")
    console.print(
        "[yellow]ADVERTENCIA: este modo no dispone de geometría ni coordenadas UV.\n"
        "Los resultados son inferencias visuales 2D y no permiten reconstruir\n"
        "de forma fiable el objeto 3D original.[/yellow]"
    )
    console.print(f"[cyan]Atlas:[/cyan] {atlas}; salida prevista: {output}")


@app.command("semantic-3d")
def semantic_3d(
    model: Annotated[Path, typer.Argument(help="GLB/glTF local")],
    atlas: Annotated[Path, typer.Argument(help="Atlas local confirmado por la persona usuaria")],
    output: Annotated[Path, typer.Option(help="Raíz de salida GLB")] = Path("outputs"),
    device: Annotated[str, typer.Option(help="auto, cpu o cuda para Qwen3-VL local")] = "auto",
    minimum_confidence: Annotated[float, typer.Option(help="Confianza mínima para aceptar un grupo")] = 0.70,
    node: Annotated[int | None, typer.Option(help="Índice del nodo glTF a analizar")] = None,
    mesh_index: Annotated[int | None, typer.Option(help="Índice de malla para desambiguar")] = None,
    texture_index: Annotated[int | None, typer.Option(help="Índice de textura glTF a analizar")] = None,
    uv_set: Annotated[int, typer.Option(help="Conjunto UV (TEXCOORD_n) a usar")] = 0,
    flip_v: Annotated[bool, typer.Option(help="Invierte V para el atlas externo")] = True,
    proximity_factor: Annotated[float, typer.Option(help="Distancia relativa para propuestas 3D")] = 0.08,
) -> None:
    """Agrupa un nodo GLB con UV sin unir físicamente sus componentes de malla."""
    if not model.is_file() or not atlas.is_file():
        raise typer.BadParameter("El GLB o atlas solicitado no existe localmente.")
    if not is_semantic_model_downloaded("qwen3-vl-2b"):
        raise typer.BadParameter("qwen3-vl-2b no está disponible localmente; no se descargará durante run.")
    backend = Qwen3VLSemanticGroupingBackend("qwen3-vl-2b", device, minimum_confidence, minimum_confidence)
    try:
        destination = group_semantic_3d(
            model,
            atlas,
            output,
            backend,
            Semantic3DConfig(minimum_confidence, proximity_factor, flip_v, texture_index, uv_set),
            node_index=node,
            mesh_index=mesh_index,
        )
    except (GltfLoadError, PrimitiveDecodeError, SemanticInferenceError, OSError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error
    finally:
        backend.close()
    console.print(f"[green]Objetos semánticos 3D:[/green] {destination}")


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
    auto_group: Annotated[
        bool | None, typer.Option("--auto-group/--no-auto-group", help="Agrupar piezas semánticamente")
    ] = None,
    semantic_model: Annotated[str | None, typer.Option(help="Modelo semántico local")] = None,
    semantic_device: Annotated[str | None, typer.Option(help="auto, cpu, cuda o mps para el modelo semántico")] = None,
    group_confidence: Annotated[float | None, typer.Option(help="Confianza mínima de agrupación")] = None,
    auto_group_confidence: Annotated[float | None, typer.Option(help="Confianza para aceptación automática")] = None,
    max_pieces_per_sheet: Annotated[int | None, typer.Option(help="Máximo de piezas por hoja semántica")] = None,
    naming_language: Annotated[str | None, typer.Option(help="Idioma de nombres semánticos")] = None,
    keep_semantic_inputs: Annotated[
        bool | None, typer.Option("--keep-semantic-inputs/--discard-semantic-inputs")
    ] = None,
    fail_fast_semantic: Annotated[bool, typer.Option(help="Detenerse al primer error semántico")] = False,
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
                "grouping.enabled": auto_group,
                "grouping.model": semantic_model,
                "grouping.device": semantic_device,
                "grouping.minimum_confidence": group_confidence,
                "grouping.automatic_confidence": auto_group_confidence,
                "grouping.max_pieces_per_sheet": max_pieces_per_sheet,
                "grouping.naming_language": naming_language,
                "grouping.keep_semantic_inputs": keep_semantic_inputs,
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
    try:
        for image_path in images:
            try:
                result = process_image(image_path, output_root, effective_config, sam_engine)
                completed.append(result)
                console.print(f"[green]Procesado:[/green] {image_path} -> {result}")
            except (AtlasSplitterError, OSError, ValueError) as error:
                failures += 1
                console.print(f"[red]Error en {image_path}: {error}[/red]")
                if fail_fast:
                    break
    finally:
        sam_engine.close()
    if effective_config.grouping.enabled and completed:
        semantic_backend = Qwen3VLSemanticGroupingBackend(
            effective_config.grouping.model,
            effective_config.grouping.device,
            effective_config.grouping.minimum_confidence,
            effective_config.grouping.automatic_confidence,
        )
        try:
            for result_directory in completed:
                try:
                    group_extracted_atlas(result_directory, effective_config.grouping, semantic_backend)
                    console.print(f"[green]Agrupado:[/green] {result_directory}")
                except (SemanticInferenceError, SemanticModelUnavailableError, OSError, ValueError) as error:
                    failures += 1
                    console.print(f"[red]Error de agrupación en {result_directory}: {error}[/red]")
                    if fail_fast_semantic:
                        break
        finally:
            semantic_backend.close()
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
    commands = {
        "apply-review", "doctor", "glb", "install", "inspect", "models", "preview", "review", "semantic",
        "semantic-3d", "semantic-models", "run",
    }
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
    arguments = sys.argv[1:]
    if not arguments:
        if not sys.stdin.isatty():
            get_command(app).main(args=["--help"], prog_name="atlas-splitter")
            return
        arguments = interactive_arguments(Path.cwd())
    debug = "--debug" in arguments
    try:
        get_command(app).main(args=translate_simple_args(arguments), prog_name="atlas-splitter", standalone_mode=False)
    except typer.Exit as error:
        raise SystemExit(error.exit_code) from error
    except Exception as error:
        if debug:
            console.print_exception()
        else:
            console.print(f"[red]Error: {error}[/red]\nUsa --debug para ver el traceback.")
        raise SystemExit(1) from error


@app.command()
def install(
    model: Annotated[str | None, typer.Option(help="Checkpoint SAM 2 opcional")] = None,
    environment: Annotated[Path, typer.Option(help="Ruta del virtualenv aislado")] = Path(".atlas-splitter-venv"),
    profile: Annotated[str, typer.Option(help="basic, geometry, semantic o all")] = "basic",
    yes: Annotated[bool, typer.Option("--yes", help="Confirma una descarga de modelo solicitada")] = False,
) -> None:
    """Crea un entorno aislado local; no modifica el Python global."""
    console.print("Creando entorno aislado de atlas-splitter...")
    try:
        target = create_isolated_environment(Path.cwd(), environment, profile)
        if model is not None:
            if not yes and not typer.confirm(
                f"Esto descargará SAM 2 y el checkpoint '{model}' dentro del entorno aislado. ¿Continuar?",
                default=False,
            ):
                raise InstallationError("Descarga de modelo cancelada por la persona usuaria.")
            python = target / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
            checkpoint = install_runtime(model, python)
            console.print(f"[green]Checkpoint disponible:[/green] {checkpoint}")
    except (InstallationError, OSError, ValueError) as error:
        raise typer.BadParameter(str(error), param_hint="--environment") from error
    executable = target / ("Scripts" if sys.platform == "win32" else "bin") / "atlas-splitter"
    console.print(f"[green]Entorno listo:[/green] {target.resolve()}")
    console.print(f"Ejecutable: {executable}")


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


@semantic_models_app.command("list")
def list_semantic_models() -> None:
    """Lista los modelos semánticos locales sin iniciar descargas."""
    table = Table(title="Modelos semánticos")
    table.add_column("Modelo")
    table.add_column("Repositorio")
    table.add_column("Estado")
    for name, spec in SEMANTIC_MODELS.items():
        table.add_row(name, spec.repository_id, "instalado" if is_semantic_model_downloaded(name) else "no descargado")
    console.print(table)


@semantic_models_app.command("download")
def download_registered_semantic_model(
    model: Annotated[str, typer.Argument(help="Nombre del modelo semántico")],
) -> None:
    """Descarga explícitamente un modelo semántico a la caché local."""
    try:
        get_semantic_model(model)
        with console.status(f"Descargando {model}..."):
            destination = download_semantic_model(model)
    except (OSError, RuntimeError, ValueError) as error:
        raise typer.BadParameter(str(error), param_hint="model") from error
    console.print(f"[green]Modelo semántico disponible:[/green] {destination}")


@app.command()
def inspect(
    source: Annotated[Path, typer.Argument(help="Modelo GLB/glTF local o ZIP heredado de atlas-split")],
    format: Annotated[str, typer.Option("--format", help="text o json (sólo para GLB/glTF)")] = "text",
) -> None:
    """Inspecciona un modelo GLB/glTF; los ZIP antiguos conservan su vista heredada."""
    import json
    import zipfile

    if format not in {"text", "json"}:
        raise typer.BadParameter("--format debe ser text o json")
    if source.suffix.lower() in {".glb", ".gltf"}:
        try:
            inspection = inspect_model(load_gltf(source))
        except (GltfLoadError, OSError, ValueError) as error:
            raise typer.BadParameter(str(error), param_hint="source") from error
        if format == "json":
            console.print_json(inspection.model_dump_json(indent=2))
            return
        console.print(f"Archivo: {inspection.file}")
        console.print(f"Nodos: {inspection.nodes}")
        console.print(f"Mallas: {inspection.meshes}")
        console.print(f"Primitivas: {inspection.primitives}")
        console.print(f"Materiales: {inspection.materials}")
        console.print(f"Texturas: {inspection.textures}")
        console.print(f"UV sets disponibles: {', '.join(inspection.uv_sets) or 'ninguno'}")
        console.print(f"Animaciones: {inspection.animations}")
        console.print(f"Compresión Draco: {'sí' if inspection.draco_compression else 'no'}")
        for number, candidate in enumerate(inspection.candidates, start=1):
            console.print(f"\n[{number}] Nodo: {candidate.node_name} ({candidate.node_index})")
            console.print(f"    Malla: {candidate.mesh_index}")
            console.print(f"    Primitivas: {candidate.primitive_count}")
            console.print(f"    Materiales: {', '.join(candidate.material_names) or 'ninguno'}")
            console.print(f"    UV: {', '.join(candidate.uv_sets) or 'ninguno'}")
        return
    if format != "text":
        raise typer.BadParameter("--format json requiere un archivo GLB o glTF", param_hint="source")
    try:
        with zipfile.ZipFile(source) as contents:
            manifests = [name for name in contents.namelist() if name.endswith("manifest.json")]
            if not manifests:
                raise ValueError("El ZIP no contiene manifest.json")
            for name in manifests:
                manifest = json.loads(contents.read(name))
                console.print(f"{name}: {manifest['final_elements']} elementos; fuente {manifest['source_file']}")
    except (OSError, ValueError, zipfile.BadZipFile, KeyError) as error:
        raise typer.BadParameter(str(error), param_hint="source") from error
