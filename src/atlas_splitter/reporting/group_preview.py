"""Vistas previas PNG de grupos semánticos."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from atlas_splitter.io.image_loader import LoadedImage
from atlas_splitter.semantic.types import PieceReference


def _add_piece_mask(
    union: np.ndarray,
    mask: np.ndarray,
    mask_bounds: tuple[int, int, int, int],
    left: int,
    top: int,
) -> None:
    """Añade una máscara local o completa a una unión expresada en coordenadas del atlas."""
    mask_left, mask_top, mask_width, mask_height = mask_bounds
    if mask.shape != (mask_height, mask_width):
        raise ValueError("Las dimensiones de la máscara no coinciden con sus coordenadas registradas.")
    right, bottom = left + union.shape[1], top + union.shape[0]
    overlap_left, overlap_top = max(left, mask_left), max(top, mask_top)
    overlap_right, overlap_bottom = min(right, mask_left + mask_width), min(bottom, mask_top + mask_height)
    if overlap_left >= overlap_right or overlap_top >= overlap_bottom:
        return
    union[overlap_top - top : overlap_bottom - top, overlap_left - left : overlap_right - left] |= mask[
        overlap_top - mask_top : overlap_bottom - mask_top, overlap_left - mask_left : overlap_right - mask_left
    ]


def write_group_preview(destination: Path, image: LoadedImage, pieces: list[PieceReference]) -> None:
    """Compone las piezas conservando su posición relativa dentro del atlas."""
    left = min(piece.bbox[0] for piece in pieces)
    top = min(piece.bbox[1] for piece in pieces)
    right = max(piece.bbox[0] + piece.bbox[2] for piece in pieces)
    bottom = max(piece.bbox[1] + piece.bbox[3] for piece in pieces)
    preview = image.pixels[top:bottom, left:right].copy()
    union = np.zeros(preview.shape[:2], dtype=bool)
    for piece in pieces:
        with Image.open(piece.mask_path) as mask_image:
            mask = np.asarray(mask_image.convert("L"), dtype=np.uint8) > 0
        mask_bounds = piece.mask_bounds or (0, 0, image.width, image.height)
        _add_piece_mask(union, mask, mask_bounds, left, top)
    preview[:, :, 3] = np.where(union, preview[:, :, 3], 0)
    temporary = destination.with_suffix(".png.tmp")
    Image.fromarray(preview, "RGBA").save(temporary, format="PNG")
    temporary.replace(destination)
