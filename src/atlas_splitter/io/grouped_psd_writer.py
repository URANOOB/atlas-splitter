"""PSD no destructivo para grupos de piezas ya extraídas."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image
from psd_tools import PSDImage

from atlas_splitter.io.image_loader import LoadedImage
from atlas_splitter.reporting.group_preview import _add_piece_mask
from atlas_splitter.semantic.types import PieceReference


def write_grouped_psd(destination: Path, image: LoadedImage, pieces: list[PieceReference]) -> None:
    """Escribe una capa transparente por pieza dentro de su bounding box conjunto."""
    if not pieces:
        raise ValueError("Un PSD agrupado requiere al menos una pieza.")
    left = min(piece.bbox[0] for piece in pieces)
    top = min(piece.bbox[1] for piece in pieces)
    right = max(piece.bbox[0] + piece.bbox[2] for piece in pieces)
    bottom = max(piece.bbox[1] + piece.bbox[3] for piece in pieces)
    document = PSDImage.new(mode="RGB", size=(right - left, bottom - top), depth=8)
    for piece in pieces:
        with Image.open(piece.mask_path) as mask_image:
            mask = np.asarray(mask_image.convert("L"), dtype=np.uint8) > 0
        layer = image.pixels[top:bottom, left:right].copy()
        visible = np.zeros(layer.shape[:2], dtype=bool)
        mask_bounds = piece.mask_bounds or (0, 0, image.width, image.height)
        _add_piece_mask(visible, mask, mask_bounds, left, top)
        layer[:, :, 3] = np.where(visible, layer[:, :, 3], 0)
        document.create_pixel_layer(Image.fromarray(layer, "RGBA"), name=piece.piece_id)
    temporary = destination.with_suffix(".psd.tmp")
    document.save(temporary)
    temporary.replace(destination)
