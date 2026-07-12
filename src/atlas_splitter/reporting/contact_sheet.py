"""Hoja de contacto PNG para inspección visual rápida."""

from __future__ import annotations

from math import ceil, sqrt
from pathlib import Path

from PIL import Image, ImageDraw


def write_contact_sheet(destination: Path, element_paths: list[Path], tile_size: int = 160) -> None:
    """Compone miniaturas sobre tablero y etiqueta cada elemento."""
    if not element_paths:
        return
    columns = max(1, ceil(sqrt(len(element_paths))))
    rows = ceil(len(element_paths) / columns)
    sheet = Image.new("RGBA", (columns * tile_size, rows * (tile_size + 24)), (40, 40, 40, 255))
    draw = ImageDraw.Draw(sheet)
    for index, path in enumerate(element_paths):
        with Image.open(path) as item:
            thumbnail = item.convert("RGBA")
            thumbnail.thumbnail((tile_size - 12, tile_size - 12))
        column, row = index % columns, index // columns
        x = column * tile_size + (tile_size - thumbnail.width) // 2
        y = row * (tile_size + 24) + (tile_size - thumbnail.height) // 2
        sheet.alpha_composite(thumbnail, (x, y))
        draw.text(
            (column * tile_size + 6, row * (tile_size + 24) + tile_size + 4),
            path.stem,
            fill="white",
        )
    temporary = destination.with_suffix(".png.tmp")
    sheet.save(temporary, format="PNG")
    temporary.replace(destination)
