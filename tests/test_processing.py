import numpy as np

from atlas_splitter.config import SegmentationConfig
from atlas_splitter.processing.deduplicate import deduplicate_masks
from atlas_splitter.processing.mask_cleanup import cleanup_masks
from atlas_splitter.segmentation.classical import MaskCandidate


def _candidate(mask: np.ndarray, confidence: float = 1.0) -> MaskCandidate:
    height, width = mask.shape
    return MaskCandidate(mask, (0, 0, width, height), int(mask.sum()), confidence, 1.0)


def test_cleanup_removes_small_masks() -> None:
    kept, discarded = cleanup_masks([_candidate(np.ones((2, 2), bool))], SegmentationConfig(min_area=5), 100)
    assert kept == []
    assert discarded == 1


def test_deduplicate_removes_contained_mask() -> None:
    outer = np.ones((10, 10), dtype=bool)
    inner = np.zeros((10, 10), dtype=bool)
    inner[2:8, 2:8] = True
    kept, discarded = deduplicate_masks([_candidate(inner), _candidate(outer)], 0.8)
    assert len(kept) == 1
    assert kept[0].area == 100
    assert discarded == 1
