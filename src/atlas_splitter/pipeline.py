"""Pipeline clásico de una imagen, procesada localmente y archivo por archivo."""

from __future__ import annotations

import shutil
from pathlib import Path
from time import perf_counter

import numpy as np
from PIL import Image

from atlas_splitter.config import AppConfig
from atlas_splitter.io.image_loader import LoadedImage, load_image
from atlas_splitter.io.psd_writer import write_element_psd
from atlas_splitter.processing.deduplicate import deduplicate_masks
from atlas_splitter.processing.mask_cleanup import cleanup_masks
from atlas_splitter.reporting.contact_sheet import write_contact_sheet
from atlas_splitter.reporting.html_report import generate_html_report
from atlas_splitter.reporting.manifest import write_manifest
from atlas_splitter.segmentation.classical import MaskCandidate
from atlas_splitter.segmentation.hybrid import segment_hybrid
from atlas_splitter.segmentation.sam2_engine import MaskGenerator


def _safe_name(path: Path) -> str:
    return "".join(character if character.isalnum() or character in "-_" else "_" for character in path.stem)


def _copy_source_image(source: Path, destination: Path) -> str:
    """Copia el atlas a una ruta segura que viaja con el resultado."""
    suffix = source.suffix.lower()
    if not suffix or suffix == ".":
        raise ValueError("El atlas fuente debe conservar una extensión válida.")
    name = f"{_safe_name(source) or 'atlas'}{suffix}"
    relative = Path("source") / name
    target = destination / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return relative.as_posix()


def _ordered(candidates: list[MaskCandidate]) -> list[MaskCandidate]:
    return sorted(candidates, key=lambda item: (item.bbox[1], item.bbox[0], -item.area))


def _write_elements(
    destination: Path, image: LoadedImage, elements: list[MaskCandidate], config: AppConfig
) -> list[Path]:
    """Escribe los artefactos por elemento y devuelve los PNG para la vista previa."""
    png_dir, mask_dir, psd_dir = destination / "png", destination / "masks", destination / "psd"
    if config.output.include_png:
        png_dir.mkdir(parents=True)
    if config.output.include_masks:
        mask_dir.mkdir(parents=True)
    if config.output.include_psd:
        psd_dir.mkdir(parents=True)
    png_paths: list[Path] = []
    for index, candidate in enumerate(elements, start=1):
        element = image.pixels.copy()
        element[:, :, 3] = np.where(candidate.mask, element[:, :, 3], 0)
        mask = (candidate.mask * 255).astype(np.uint8)
        if config.processing.crop_elements:
            x, y, width, height = candidate.bbox
            left, top = max(0, x - config.processing.padding), max(0, y - config.processing.padding)
            right, bottom = (
                min(image.width, x + width + config.processing.padding),
                min(image.height, y + height + config.processing.padding),
            )
            element, mask = element[top:bottom, left:right], mask[top:bottom, left:right]
        name = f"element_{index:03d}.png"
        if config.output.include_png:
            png_path = png_dir / name
            Image.fromarray(element, "RGBA").save(png_path)
            png_paths.append(png_path)
        if config.output.include_masks:
            Image.fromarray(mask, "L").save(mask_dir / name)
        if config.output.include_psd:
            write_element_psd(
                psd_dir / name.replace(".png", ".psd"),
                image,
                candidate,
                config.processing.crop_elements,
                config.processing.padding,
            )
    return png_paths


def process_image(path: Path, output_root: Path, config: AppConfig, sam_engine: MaskGenerator | None = None) -> Path:
    """Procesa un atlas sin sobrescribir resultados preexistentes."""
    started = perf_counter()
    image = load_image(path)
    destination = output_root / _safe_name(path)
    if destination.exists():
        raise FileExistsError(f"El resultado ya existe y no se sobrescribirá: {destination}")
    candidates = segment_hybrid(image, config.segmentation, sam_engine)
    kept, discarded = cleanup_masks(candidates, config.segmentation, image.width * image.height)
    elements, duplicate_count = deduplicate_masks(kept, config.segmentation.duplicate_iou)
    elements = _ordered(elements)
    destination.mkdir(parents=True)
    try:
        source_file = _copy_source_image(path, destination)
        png_paths = _write_elements(destination, image, elements, config)
        if config.output.create_contact_sheet and png_paths:
            write_contact_sheet(destination / "contact_sheet.png", png_paths)
        write_manifest(
            destination / "manifest.json",
            image,
            config,
            len(candidates),
            discarded + duplicate_count,
            elements,
            perf_counter() - started,
            source_file,
            getattr(sam_engine, "runtime_device", "cpu"),
        )
        generate_html_report(destination)
    except (Exception, KeyboardInterrupt):
        for item in sorted(destination.rglob("*"), reverse=True):
            if item.is_file():
                item.unlink()
            else:
                item.rmdir()
        destination.rmdir()
        raise
    return destination
