from pathlib import Path

import numpy as np
from PIL import Image
from psd_tools import PSDImage

from atlas_splitter.io.grouped_psd_writer import write_grouped_psd
from atlas_splitter.io.image_loader import LoadedImage
from atlas_splitter.io.psd_writer import write_element_psd
from atlas_splitter.segmentation.classical import MaskCandidate
from atlas_splitter.semantic.types import PieceReference


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


def test_grouped_psd_has_one_named_layer_per_piece(tmp_path) -> None:
    pixels = np.zeros((20, 20, 4), dtype=np.uint8)
    pixels[2:6, 2:6] = (255, 0, 0, 255)
    pixels[10:15, 12:18] = (0, 255, 0, 255)
    first_mask = np.zeros((20, 20), dtype=np.uint8)
    first_mask[2:6, 2:6] = 255
    second_mask = np.zeros((20, 20), dtype=np.uint8)
    second_mask[10:15, 12:18] = 255
    first_path, second_path = tmp_path / "first.png", tmp_path / "second.png"
    Image.fromarray(first_mask, "L").save(first_path)
    Image.fromarray(second_mask, "L").save(second_path)
    pieces = [
        PieceReference("E001", 1, tmp_path / "one.png", first_path, None, (2, 2, 4, 4), 16, "classical"),
        PieceReference("E002", 2, tmp_path / "two.png", second_path, None, (12, 10, 6, 5), 30, "classical"),
    ]
    destination = tmp_path / "house_001.psd"
    write_grouped_psd(destination, LoadedImage(Path("atlas.webp"), pixels, "a"), pieces)
    document = PSDImage.open(destination)
    assert document.size == (16, 13)
    assert [layer.name for layer in document] == ["E001", "E002"]
