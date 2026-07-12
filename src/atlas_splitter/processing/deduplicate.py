"""Supresión determinista de máscaras solapadas o contenidas."""

from __future__ import annotations

import numpy as np

from atlas_splitter.segmentation.classical import MaskCandidate


def _iou(first: np.ndarray, second: np.ndarray) -> float:
    union = np.logical_or(first, second).sum()
    return float(np.logical_and(first, second).sum() / union) if union else 0.0


def deduplicate_masks(candidates: list[MaskCandidate], threshold: float) -> tuple[list[MaskCandidate], int]:
    """Conserva la máscara de mejor calidad cuando hay duplicados o contenidas."""
    ordered = sorted(candidates, key=lambda item: (-item.confidence, -item.stability, -item.area, item.bbox))
    kept: list[MaskCandidate] = []
    discarded = 0
    for candidate in ordered:
        redundant = False
        for existing in kept:
            intersection = np.logical_and(candidate.mask, existing.mask).sum()
            contained = intersection == candidate.area
            if contained or _iou(candidate.mask, existing.mask) >= threshold:
                redundant = True
                break
        if redundant:
            discarded += 1
        else:
            kept.append(candidate)
    return kept, discarded
