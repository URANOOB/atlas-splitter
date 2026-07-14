"""Hoja de contacto específica para la entrada semántica."""

from __future__ import annotations

from math import ceil, sqrt
from pathlib import Path

from PIL import Image, ImageDraw

from atlas_splitter.semantic.types import PieceReference


def write_semantic_contact_sheet(destination: Path, pieces: list[PieceReference], tile_size: int = 220) -> None:
    """Escribe una cuadrícula con alfa sobre tablero neutro y etiquetas grandes."""
    if not pieces:
        return
    columns = max(1, ceil(sqrt(len(pieces))))
    rows = ceil(len(pieces) / columns)
    label_height, margin = 34, 12
    sheet = Image.new("RGBA", (columns * tile_size, rows * (tile_size + label_height)), (52, 52, 52, 255))
    draw = ImageDraw.Draw(sheet)
    for index, piece in enumerate(pieces):
        with Image.open(piece.png_path) as source:
            item = source.convert("RGBA")
        board = Image.new("RGBA", (tile_size - 2 * margin, tile_size - 2 * margin), (110, 110, 110, 255))
        for y in range(0, board.height, 16):
            for x in range(0, board.width, 16):
                if (x // 16 + y // 16) % 2:
                    ImageDraw.Draw(board).rectangle((x, y, x + 15, y + 15), fill=(140, 140, 140, 255))
        item.thumbnail(board.size)
        board.alpha_composite(item, ((board.width - item.width) // 2, (board.height - item.height) // 2))
        column, row = index % columns, index // columns
        left, top = column * tile_size + margin, row * (tile_size + label_height) + margin
        sheet.alpha_composite(board, (left, top))
        draw.text(
            (column * tile_size + margin, row * (tile_size + label_height) + tile_size + 5),
            piece.piece_id,
            fill="white",
        )
    temporary = destination.with_suffix(".png.tmp")
    sheet.save(temporary, format="PNG")
    temporary.replace(destination)
