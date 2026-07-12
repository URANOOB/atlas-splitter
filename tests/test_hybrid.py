from pathlib import Path

import numpy as np

from atlas_splitter.config import SegmentationConfig
from atlas_splitter.io.image_loader import LoadedImage
from atlas_splitter.segmentation.classical import MaskCandidate
from atlas_splitter.segmentation.hybrid import merge_masks, segment_hybrid


def _candidate(mask: np.ndarray, source: str) -> MaskCandidate:
    return MaskCandidate(mask, (0, 0, mask.shape[1], mask.shape[0]), int(mask.sum()), 0.95, 0.95, source)


def test_hybrid_preserves_clean_classical_and_adds_new_sam_mask() -> None:
    classical = _candidate(np.pad(np.ones((2, 2), bool), ((0, 4), (0, 4))), "classical")
    sam = _candidate(np.pad(np.ones((2, 2), bool), ((4, 0), (4, 0))), "sam2")
    merged = merge_masks([classical], [sam])
    assert [item.source for item in merged] == ["classical", "sam2"]


def test_hybrid_without_backend_uses_classical() -> None:
    pixels = np.zeros((10, 10, 4), dtype=np.uint8)
    pixels[2:8, 2:8] = (255, 0, 0, 255)
    image = LoadedImage(Path("atlas.webp"), pixels, "x")
    candidates = segment_hybrid(image, SegmentationConfig(min_area=1))
    assert len(candidates) == 1
    assert candidates[0].source == "classical"
