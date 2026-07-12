from pathlib import Path

import numpy as np
from psd_tools import PSDImage

from atlas_splitter.io.image_loader import LoadedImage
from atlas_splitter.io.psd_writer import write_element_psd
from atlas_splitter.segmentation.classical import MaskCandidate


def test_psd_writer_creates_reopenable_layered_document(tmp_path) -> None:
    pixels = np.zeros((12, 16, 4), dtype=np.uint8)
    pixels[3:9, 4:12] = (220, 20, 40, 255)
    mask = pixels[:, :, 3] > 0
    candidate = MaskCandidate(mask, (4, 3, 8, 6), int(mask.sum()), 1.0, 1.0)
    destination = tmp_path / "element_001.psd"
    write_element_psd(destination, LoadedImage(Path("atlas.webp"), pixels, "a"), candidate, False, 0)
    document = PSDImage.open(destination)
    assert document.size == (16, 12)
    assert [layer.name for layer in document] == [
        "Background reference",
        "Original crop",
        "Mask",
        "Element",
    ]
    assert not document[0].visible


def test_psd_writer_crops_document_with_padding(tmp_path) -> None:
    pixels = np.zeros((20, 20, 4), dtype=np.uint8)
    pixels[5:10, 5:10] = (10, 100, 200, 255)
    mask = pixels[:, :, 3] > 0
    candidate = MaskCandidate(mask, (5, 5, 5, 5), int(mask.sum()), 1.0, 1.0)
    destination = tmp_path / "element_001.psd"
    write_element_psd(destination, LoadedImage(Path("atlas.webp"), pixels, "a"), candidate, True, 2)
    assert PSDImage.open(destination).size == (9, 9)
