"""Contrato para segmentación SAM2 guiada, separado del modo automático."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np

from atlas_splitter.io.image_loader import LoadedImage


@dataclass(frozen=True, slots=True)
class SegmentationPrompt:
    """Una caja opcional y puntos positivos/negativos en píxeles del atlas."""

    box: tuple[float, float, float, float] | None = None
    positive_points: tuple[tuple[float, float], ...] = ()
    negative_points: tuple[tuple[float, float], ...] = ()

    def point_arrays(self) -> tuple[np.ndarray, np.ndarray]:
        points = [*self.positive_points, *self.negative_points]
        labels = [1] * len(self.positive_points) + [0] * len(self.negative_points)
        return np.asarray(points, dtype=np.float32).reshape(-1, 2), np.asarray(labels, dtype=np.int32)


class PromptedMaskGenerator(Protocol):
    """Backend intercambiable que convierte prompts visuales en una máscara precisa."""

    def predict(self, image: LoadedImage, prompt: SegmentationPrompt) -> np.ndarray:
        """Devuelve una máscara booleana del tamaño íntegro del atlas."""


class FakePromptedMaskGenerator:
    """Backend determinista para pruebas; nunca carga SAM2 ni usa GPU."""

    def __init__(self, mask: np.ndarray) -> None:
        self.mask = np.asarray(mask, dtype=bool)
        self.last_prompt: SegmentationPrompt | None = None

    def predict(self, image: LoadedImage, prompt: SegmentationPrompt) -> np.ndarray:
        if self.mask.shape != (image.height, image.width):
            raise ValueError("La máscara falsa no coincide con el atlas")
        self.last_prompt = prompt
        return self.mask.copy()
