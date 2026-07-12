"""Creación de PSD con capas de píxeles compatibles con Photoshop."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image
from psd_tools import PSDImage

from atlas_splitter.io.image_loader import LoadedImage
from atlas_splitter.segmentation.classical import MaskCandidate


def write_element_psd(
    destination: Path,
    image: LoadedImage,
    candidate: MaskCandidate,
    crop: bool,
    padding: int,
) -> None:
    """Escribe un PSD con Element, Original crop, Mask y Background reference.

    ``psd-tools`` crea capas de píxeles y máscaras alfa, no capas artísticas
    originales. El documento se abre con un tamaño completo o recortado según
    la opción elegida.
    """
    x, y, width, height = candidate.bbox
    left, top, right, bottom = 0, 0, image.width, image.height
    if crop:
        left, top = max(0, x - padding), max(0, y - padding)
        right, bottom = (
            min(image.width, x + width + padding),
            min(image.height, y + height + padding),
        )
    original = image.pixels[top:bottom, left:right]
    mask = candidate.mask[top:bottom, left:right]
    element = original.copy()
    element[:, :, 3] = np.where(mask, element[:, :, 3], 0)
    document = PSDImage.new(mode="RGB", size=(right - left, bottom - top), depth=8)
    background = document.create_pixel_layer(Image.fromarray(original, "RGBA"), name="Background reference")
    background.visible = False
    document.create_pixel_layer(Image.fromarray(original, "RGBA"), name="Original crop")
    mask_image = Image.fromarray((mask * 255).astype(np.uint8), "L").convert("RGBA")
    document.create_pixel_layer(mask_image, name="Mask")
    document.create_pixel_layer(Image.fromarray(element, "RGBA"), name="Element")
    temporary = destination.with_suffix(".psd.tmp")
    document.save(temporary)
    temporary.replace(destination)
