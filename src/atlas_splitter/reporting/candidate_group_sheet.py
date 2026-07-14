"""Hoja de candidatos para la consolidación semántica entre páginas."""

from __future__ import annotations

from math import ceil, sqrt
from pathlib import Path

from PIL import Image, ImageDraw


def write_candidate_group_sheet(destination: Path, candidates: list[tuple[str, Path]], tile_size: int = 220) -> None:
    """Compone vistas previas de candidatos y sus IDs de piezas en una hoja estable."""
    if not candidates:
        return
    columns = max(1, ceil(sqrt(len(candidates))))
    rows = ceil(len(candidates) / columns)
    label_height, margin = 42, 12
    sheet = Image.new("RGBA", (columns * tile_size, rows * (tile_size + label_height)), (52, 52, 52, 255))
    draw = ImageDraw.Draw(sheet)
    for index, (label, path) in enumerate(candidates):
        with Image.open(path) as source:
            thumbnail = source.convert("RGBA")
        thumbnail.thumbnail((tile_size - 2 * margin, tile_size - 2 * margin))
        column, row = index % columns, index // columns
        left = column * tile_size + (tile_size - thumbnail.width) // 2
        top = row * (tile_size + label_height) + (tile_size - thumbnail.height) // 2
        sheet.alpha_composite(thumbnail, (left, top))
        draw.text((column * tile_size + margin, row * (tile_size + label_height) + tile_size + 4), label, fill="white")
    temporary = destination.with_suffix(".png.tmp")
    sheet.save(temporary, format="PNG")
    temporary.replace(destination)
