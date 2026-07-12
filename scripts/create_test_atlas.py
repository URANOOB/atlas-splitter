"""Genera atlas WEBP sintéticos para pruebas manuales locales."""

from pathlib import Path

from PIL import Image, ImageDraw


def create_atlas(destination: Path) -> None:
    """Crea un atlas con transparencia, objetos, huecos e islas pequeñas."""
    image = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((80, 80, 340, 340), fill=(220, 60, 50, 255))
    draw.ellipse((460, 120, 760, 420), fill=(40, 130, 230, 255))
    draw.ellipse((550, 210, 670, 330), fill=(0, 0, 0, 0))
    draw.polygon(((150, 600), (450, 850), (70, 880)), fill=(90, 200, 110, 255))
    draw.rectangle((900, 920, 906, 926), fill=(255, 255, 255, 255))
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination, "WEBP", lossless=False, quality=92)


if __name__ == "__main__":
    create_atlas(Path("work/synthetic_atlas.webp"))
