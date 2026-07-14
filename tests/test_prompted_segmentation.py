"""Pruebas CPU para el contrato de prompts guiados."""

import numpy as np

from atlas_splitter.io.image_loader import LoadedImage
from atlas_splitter.segmentation.prompted import FakePromptedMaskGenerator, SegmentationPrompt


def test_prompted_backend_receives_box_and_positive_negative_points(tmp_path) -> None:
    image = LoadedImage(tmp_path / "atlas.webp", np.zeros((4, 5, 4), dtype=np.uint8), "hash")
    prompt = SegmentationPrompt((0, 0, 4, 3), ((1, 1),), ((2, 2),))
    backend = FakePromptedMaskGenerator(np.ones((4, 5), dtype=bool))
    assert backend.predict(image, prompt).shape == (4, 5)
    assert backend.last_prompt == prompt
    assert prompt.point_arrays()[1].tolist() == [1, 0]
