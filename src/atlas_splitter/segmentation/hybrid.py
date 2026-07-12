"""Combinación conservadora de candidatos clásicos y SAM 2."""

from __future__ import annotations

import numpy as np

from atlas_splitter.config import SegmentationConfig
from atlas_splitter.io.image_loader import LoadedImage
from atlas_splitter.segmentation.classical import MaskCandidate, segment_classical
from atlas_splitter.segmentation.sam2_engine import MaskGenerator


def _iou(first: np.ndarray, second: np.ndarray) -> float:
    union = np.logical_or(first, second).sum()
    return float(np.logical_and(first, second).sum() / union) if union else 0.0


def merge_masks(classical: list[MaskCandidate], sam2: list[MaskCandidate]) -> list[MaskCandidate]:
    """Conserva componentes clásicos limpios e incorpora SAM 2 para regiones nuevas."""
    merged = list(classical)
    for candidate in sam2:
        if all(_iou(candidate.mask, existing.mask) < 0.80 for existing in classical):
            merged.append(candidate)
    return merged


def segment_hybrid(
    image: LoadedImage, config: SegmentationConfig, sam_engine: MaskGenerator | None = None
) -> list[MaskCandidate]:
    """Segmenta con técnicas clásicas y refina solo cuando SAM 2 está disponible."""
    classical = segment_classical(image, config)
    if sam_engine is None:
        return classical
    return merge_masks(classical, sam_engine.generate(image))
