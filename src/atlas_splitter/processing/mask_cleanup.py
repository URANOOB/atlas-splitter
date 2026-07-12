"""Filtrado de máscaras clásicas mediante reglas configurables."""

from __future__ import annotations

from atlas_splitter.config import SegmentationConfig
from atlas_splitter.segmentation.classical import MaskCandidate


def cleanup_masks(
    candidates: list[MaskCandidate], config: SegmentationConfig, image_area: int
) -> tuple[list[MaskCandidate], int]:
    """Descarta máscaras por área, confianza, estabilidad o cobertura de fondo."""
    cleaned: list[MaskCandidate] = []
    discarded = 0
    for candidate in candidates:
        ratio = candidate.area / image_area
        if (
            candidate.area < config.min_area
            or ratio > config.max_area_ratio
            or candidate.confidence < config.confidence
            or candidate.stability < config.stability
        ):
            discarded += 1
        else:
            cleaned.append(candidate)
    return cleaned, discarded
