"""Orquestación no destructiva sobre directorios ya extraídos."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from atlas_splitter.config import GroupingConfig
from atlas_splitter.io.grouped_psd_writer import write_grouped_psd
from atlas_splitter.io.image_loader import load_image
from atlas_splitter.reporting.annotated_atlas import write_annotated_atlas
from atlas_splitter.reporting.candidate_group_sheet import write_candidate_group_sheet
from atlas_splitter.reporting.group_preview import write_group_preview
from atlas_splitter.reporting.grouping_manifest import write_grouping_manifest
from atlas_splitter.reporting.semantic_contact_sheet import write_semantic_contact_sheet
from atlas_splitter.semantic.prompt_builder import build_grouping_prompt
from atlas_splitter.semantic.protocol import SemanticGroupingBackend
from atlas_splitter.semantic.types import GroupingContext, GroupingResult, PieceReference


def _pieces_from_manifest(destination: Path, manifest: dict[str, object]) -> list[PieceReference]:
    raw_elements = manifest.get("elements")
    if not isinstance(raw_elements, list):
        raise ValueError("El manifest.json no contiene elementos válidos.")
    dimensions = manifest.get("dimensions")
    parameters = manifest.get("parameters")
    if not isinstance(dimensions, dict) or not isinstance(parameters, dict):
        raise ValueError("El manifest.json no contiene dimensiones o parámetros válidos.")
    processing = parameters.get("processing")
    if not isinstance(processing, dict):
        raise ValueError("El manifest.json no contiene parámetros de procesado válidos.")
    image_width, image_height = int(dimensions["width"]), int(dimensions["height"])
    cropped = bool(processing.get("crop_elements", False))
    padding = int(processing.get("padding", 0))
    pieces: list[PieceReference] = []
    for index, raw in enumerate(raw_elements, start=1):
        if not isinstance(raw, dict):
            raise ValueError("El manifest.json contiene un elemento inválido.")
        bbox = raw.get("bbox")
        if not isinstance(bbox, dict):
            raise ValueError("El manifest.json contiene un bounding box inválido.")
        name = str(raw["name"])
        x, y, width, height = int(bbox["x"]), int(bbox["y"]), int(bbox["width"]), int(bbox["height"])
        mask_bounds = (0, 0, image_width, image_height)
        if cropped:
            left, top = max(0, x - padding), max(0, y - padding)
            right, bottom = min(image_width, x + width + padding), min(image_height, y + height + padding)
            mask_bounds = (left, top, right - left, bottom - top)
        pieces.append(
            PieceReference(
                piece_id=f"E{index:03d}",
                element_index=index,
                png_path=destination / str(raw["png"]),
                mask_path=destination / str(raw["mask"]),
                psd_path=(destination / str(raw["psd"])) if raw.get("psd") else None,
                bbox=(x, y, width, height),
                area=int(raw["area"]),
                source=str(raw["source"]),
                mask_bounds=mask_bounds,
            )
        )
        if name != f"element_{index:03d}":
            raise ValueError("Los elementos del manifiesto deben conservar orden determinista.")
    return pieces


def group_extracted_atlas(
    destination: Path,
    config: GroupingConfig,
    backend: SemanticGroupingBackend,
) -> GroupingResult:
    """Agrupa una extracción terminada sin alterar sus PNG, máscaras ni PSD individuales."""
    manifest = json.loads((destination / "manifest.json").read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("El manifest.json debe ser un objeto.")
    source = manifest.get("source_file")
    if not isinstance(source, str):
        raise ValueError("El manifest.json no identifica el atlas fuente.")
    image = load_image(Path(source))
    pieces = _pieces_from_manifest(destination, manifest)
    inputs = destination / "semantic_inputs"
    temporary_inputs = not config.keep_semantic_inputs
    if inputs.exists() and temporary_inputs:
        shutil.rmtree(inputs)
    inputs.mkdir(parents=True, exist_ok=True)
    try:
        annotated = inputs / "annotated_atlas.png"
        write_annotated_atlas(annotated, image, pieces)
        groups = []
        unassigned: list[str] = []
        elapsed = 0.0
        repaired_responses = 0
        backend_name: str = "unknown"
        model_name: str = config.model
        page_sheets: list[Path] = []
        for page, offset in enumerate(range(0, len(pieces), config.max_pieces_per_sheet), start=1):
            page_pieces = pieces[offset : offset + config.max_pieces_per_sheet]
            sheet = inputs / f"contact_sheet_{page:03d}.png"
            write_semantic_contact_sheet(sheet, page_pieces)
            page_sheets.append(sheet)
            result = backend.group(GroupingContext(page_pieces, annotated, [sheet], build_grouping_prompt()))
            groups.extend(result.groups)
            unassigned.extend(result.unassigned_piece_ids)
            elapsed += result.elapsed_seconds
            repaired_responses += int(getattr(backend, "last_repaired_responses", 0))
            backend_name, model_name = result.backend, result.model
        if len(page_sheets) > 1 and groups:
            candidate_dir = inputs / "candidate_previews"
            candidate_dir.mkdir(exist_ok=True)
            by_id = {piece.piece_id: piece for piece in pieces}
            candidate_paths: list[tuple[str, Path]] = []
            for group in groups:
                if group.status == "rejected":
                    continue
                preview = candidate_dir / f"{group.group_id}.png"
                write_group_preview(preview, image, [by_id[piece_id] for piece_id in group.piece_ids])
                candidate_paths.append((f"{group.group_id}: {', '.join(group.piece_ids)}", preview))
            if candidate_paths:
                candidate_sheet = inputs / "candidate_groups.png"
                write_candidate_group_sheet(candidate_sheet, candidate_paths)
                final_context = GroupingContext(
                    pieces,
                    annotated,
                    [*page_sheets, candidate_sheet],
                    f"{build_grouping_prompt()}\nCandidate group previews are included for cross-page consolidation.",
                )
                final_result = backend.group(final_context)
                groups, unassigned = final_result.groups, final_result.unassigned_piece_ids
                elapsed += final_result.elapsed_seconds
                repaired_responses += int(getattr(backend, "last_repaired_responses", 0))
                backend_name, model_name = final_result.backend, final_result.model
        result = GroupingResult(groups, unassigned, backend_name, model_name, elapsed)
        artifacts: dict[str, dict[str, object]] = {}
        by_id = {piece.piece_id: piece for piece in pieces}
        for group in result.groups:
            if group.status == "rejected":
                continue
            members = [by_id[piece_id] for piece_id in group.piece_ids]
            grouped_dir, preview_dir = destination / "grouped", destination / "group_previews"
            grouped_dir.mkdir(exist_ok=True)
            preview_dir.mkdir(exist_ok=True)
            psd = grouped_dir / f"{group.group_id}.psd"
            preview = preview_dir / f"{group.group_id}.png"
            write_grouped_psd(psd, image, members)
            write_group_preview(preview, image, members)
            artifacts[group.group_id] = {
                "psd": str(psd.relative_to(destination)),
                "preview": str(preview.relative_to(destination)),
            }
        _organize_semantic_output(destination, result, by_id, artifacts)
        write_grouping_manifest(
            destination / "semantic_manifest.json",
            result,
            getattr(backend, "runtime_device", config.device),
            artifacts,
            config.model_dump(mode="json"),
            repaired_responses=repaired_responses,
        )
        shutil.copy2(destination / "semantic_manifest.json", destination / "grouping_manifest.json")
        return result
    finally:
        if temporary_inputs:
            shutil.rmtree(inputs, ignore_errors=True)


def _organize_semantic_output(
    destination: Path,
    result: GroupingResult,
    pieces: dict[str, PieceReference],
    artifacts: dict[str, dict[str, object]],
) -> None:
    """Copia artefactos a rutas seguras; los PNG y PSD originales nunca se eliminan."""
    for group in result.groups:
        root = destination / ("objects" if group.status == "accepted" else "uncertain") / group.group_id
        root.mkdir(parents=True, exist_ok=True)
        copied: list[str] = []
        for piece_id in group.piece_ids:
            piece = pieces[piece_id]
            target = root / piece.png_path.name
            shutil.copy2(piece.png_path, target)
            copied.append(str(target.relative_to(destination)))
        artifacts[group.group_id]["pieces"] = copied
    unassigned = destination / "unassigned"
    unassigned.mkdir(exist_ok=True)
    for piece_id in result.unassigned_piece_ids:
        piece = pieces[piece_id]
        shutil.copy2(piece.png_path, unassigned / piece.png_path.name)
