"""Adaptador opcional de SAM 2, con importación y carga diferidas."""

from __future__ import annotations

import gc
import importlib.util
from contextlib import nullcontext
from typing import Protocol

import cv2
import numpy as np

from atlas_splitter.exceptions import Sam2InferenceError
from atlas_splitter.io.image_loader import LoadedImage
from atlas_splitter.models.manager import checkpoint_path, is_downloaded
from atlas_splitter.models.registry import get_model
from atlas_splitter.runtime import resolve_device
from atlas_splitter.segmentation.classical import MaskCandidate


class MaskGenerator(Protocol):
    """Contrato mínimo para SAM 2 y para los backends falsos de pruebas."""

    def generate(self, image: LoadedImage) -> list[MaskCandidate]:
        """Genera candidatos de máscara para una imagen."""


class Sam2Engine:
    """Carga SAM 2 una única vez por instancia y solo cuando hay un checkpoint local."""

    def __init__(
        self,
        model_name: str,
        device: str = "auto",
        points_per_side: int = 16,
        points_per_batch: int = 16,
        edge_padding: int = 2,
    ) -> None:
        self.model_name = model_name
        self.device = device
        self.points_per_side = points_per_side
        self.points_per_batch = points_per_batch
        self.edge_padding = edge_padding
        self._generator: object | None = None
        self._runtime_device = "cpu"

    @property
    def is_available(self) -> bool:
        """Indica si SAM 2 y su checkpoint local existen; nunca descarga nada."""
        return importlib.util.find_spec("sam2") is not None and is_downloaded(self.model_name)

    @property
    def runtime_device(self) -> str:
        """Dispositivo realmente usado por el generador, no el solicitado."""
        return self._runtime_device

    def _load_generator(self) -> object:
        if self._generator is not None:
            return self._generator
        from sam2.automatic_mask_generator import (  # type: ignore[import-not-found]
            SAM2AutomaticMaskGenerator,
        )
        from sam2.build_sam import build_sam2  # type: ignore[import-not-found]

        spec = get_model(self.model_name)
        selected_device = resolve_device(self.device)
        model = build_sam2(spec.config_name, str(checkpoint_path(self.model_name)), device=selected_device)
        self._runtime_device = selected_device
        self._generator = SAM2AutomaticMaskGenerator(
            model,
            points_per_side=self.points_per_side,
            points_per_batch=self.points_per_batch,
        )
        return self._generator

    def generate(self, image: LoadedImage) -> list[MaskCandidate]:
        """Ejecuta inferencia sin gradientes y transforma la respuesta de SAM 2."""
        if not self.is_available:
            return []
        import torch

        generator = self._load_generator()
        autocast_context = (
            torch.autocast("cuda", dtype=torch.bfloat16) if self._runtime_device == "cuda" else nullcontext()
        )
        try:
            with torch.inference_mode(), autocast_context:
                results = generator.generate(image.pixels[:, :, :3])  # type: ignore[attr-defined]
        except torch.OutOfMemoryError as error:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            message = (
                "SAM 2 agotó la memoria CUDA. Reduzca sam2_points_per_batch en el YAML o procese con --device cpu."
            )
            raise Sam2InferenceError(message) from error
        candidates: list[MaskCandidate] = []
        for result in results:
            mask = np.asarray(result["segmentation"], dtype=bool)
            if self.edge_padding:
                size = self.edge_padding * 2 + 1
                kernel = np.ones((size, size), dtype=np.uint8)
                mask = cv2.dilate(mask.astype(np.uint8), kernel).astype(bool)
                if np.any(image.pixels[:, :, 3] < 255):
                    mask &= image.pixels[:, :, 3] > 0
            rows, columns = np.where(mask)
            if not len(rows):
                continue
            x, y = int(columns.min()), int(rows.min())
            width, height = int(columns.max() - x + 1), int(rows.max() - y + 1)
            candidates.append(
                MaskCandidate(
                    mask=mask,
                    bbox=(x, y, width, height),
                    area=int(mask.sum()),
                    confidence=float(result.get("predicted_iou", 0.0)),
                    stability=float(result.get("stability_score", 0.0)),
                    source="sam2",
                )
            )
        return candidates

    def close(self) -> None:
        """Libera SAM 2 y caché CUDA; es seguro si nunca se cargó."""
        self._generator = None
        try:
            import torch
        except ImportError:
            return
        if torch.cuda.is_available():
            gc.collect()
            torch.cuda.empty_cache()
