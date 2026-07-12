from pathlib import Path

import numpy as np

from atlas_splitter.config import SegmentationConfig
from atlas_splitter.io.image_loader import LoadedImage
from atlas_splitter.segmentation.classical import segment_classical


def _image(pixels: np.ndarray) -> LoadedImage:
    return LoadedImage(path=Path("synthetic.webp"), pixels=pixels, sha256="a" * 64)


def test_transparent_background_finds_separate_components() -> None:
    pixels = np.zeros((40, 50, 4), dtype=np.uint8)
    pixels[3:13, 4:14] = (255, 0, 0, 255)
    pixels[20:35, 30:45] = (0, 255, 0, 255)
    candidates = segment_classical(_image(pixels), SegmentationConfig(min_area=1))
    assert [candidate.area for candidate in candidates] == [100, 225]


def test_solid_background_uses_border_color_and_fills_holes() -> None:
    pixels = np.full((30, 30, 4), (20, 30, 40, 255), dtype=np.uint8)
    pixels[5:25, 5:25, :3] = (220, 40, 50)
    pixels[11:19, 11:19, :3] = (20, 30, 40)
    candidates = segment_classical(_image(pixels), SegmentationConfig(min_area=1, background_threshold=20))
    assert len(candidates) == 1
    assert candidates[0].area == 400
