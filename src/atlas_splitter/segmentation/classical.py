"""Segmentación clásica basada en alfa, fondo estimado y componentes."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from atlas_splitter.config import SegmentationConfig
from atlas_splitter.io.image_loader import LoadedImage


@dataclass(frozen=True)
class MaskCandidate:
    """Máscara booleana con metadatos que consumirán las etapas posteriores."""

    mask: np.ndarray
    bbox: tuple[int, int, int, int]
    area: int
    confidence: float
    stability: float
    source: str = "classical"


def _estimate_background(rgb: np.ndarray) -> np.ndarray:
    border = np.concatenate((rgb[0], rgb[-1], rgb[1:-1, 0], rgb[1:-1, -1]))
    return np.median(border, axis=0)  # type: ignore[no-any-return]


def _fill_holes(mask: np.ndarray) -> np.ndarray:
    flood = (mask.astype(np.uint8) * 255).copy()
    padded = np.pad(flood, 1, constant_values=0)
    cv2.floodFill(padded, None, (0, 0), 255)
    exterior = padded[1:-1, 1:-1] == 255
    return np.logical_or(mask, ~exterior)  # type: ignore[no-any-return]


def _foreground_mask(pixels: np.ndarray, threshold: float) -> np.ndarray:
    alpha = pixels[:, :, 3]
    if np.any(alpha < 255):
        return alpha > 0
    rgb = pixels[:, :, :3].astype(np.float32)
    background = _estimate_background(rgb)
    distance = np.linalg.norm(rgb - background, axis=2)
    return distance > threshold  # type: ignore[no-any-return]


def segment_classical(image: LoadedImage, config: SegmentationConfig) -> list[MaskCandidate]:
    """Produce componentes conectados a partir de transparencia o contraste de fondo."""
    foreground = _foreground_mask(image.pixels, config.background_threshold)
    kernel_size = config.morphology_kernel if config.morphology_kernel % 2 else config.morphology_kernel + 1
    kernel = np.ones((kernel_size, kernel_size), dtype=np.uint8)
    cleaned = cv2.morphologyEx(foreground.astype(np.uint8), cv2.MORPH_CLOSE, kernel)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel).astype(bool)
    cleaned = _fill_holes(cleaned)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(cleaned.astype(np.uint8), connectivity=8)
    candidates: list[MaskCandidate] = []
    for label in range(1, count):
        x, y, width, height, area = (int(value) for value in stats[label])
        component = labels == label
        candidates.append(MaskCandidate(component, (x, y, width, height), area, confidence=1.0, stability=1.0))
    return candidates
