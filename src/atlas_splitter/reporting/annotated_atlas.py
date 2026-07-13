"""Representación anotada del atlas para contexto semántico."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from atlas_splitter.io.image_loader import LoadedImage
from atlas_splitter.semantic.types import PieceReference


def write_annotated_atlas(
    destination: Path, image: LoadedImage, pieces: list[PieceReference], max_dimension: int = 1600
) -> None:
    """Dibuja cajas y IDs sobre una copia proporcional del atlas original."""
    canvas = Image.fromarray(image.pixels, "RGBA")
    scale = min(1.0, max_dimension / max(canvas.size))
    if scale < 1:
        canvas = canvas.resize((round(canvas.width * scale), round(canvas.height * scale)), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(canvas)
    palette = [(255, 89, 94), (255, 202, 58), (138, 201, 38), (25, 130, 196), (106, 76, 147)]
    for index, piece in enumerate(pieces):
        x, y, width, height = piece.bbox
        box = tuple(round(value * scale) for value in (x, y, x + width, y + height))
        color = palette[index % len(palette)]
        draw.rectangle(box, outline=color, width=max(1, round(2 * scale)))
        draw.text((box[0] + 2, box[1] + 2), piece.piece_id, fill=color, stroke_width=1, stroke_fill="black")
    temporary = destination.with_suffix(".png.tmp")
    canvas.save(temporary, format="PNG")
    temporary.replace(destination)
