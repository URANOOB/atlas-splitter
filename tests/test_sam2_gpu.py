"""Prueba opcional: se activa solo en un entorno SAM 2/CUDA preparado."""

import importlib.util
import os

import pytest

from atlas_splitter.models.manager import is_downloaded
from atlas_splitter.segmentation.sam2_engine import Sam2Engine


def test_sam2_engine_can_close_without_loading_a_model() -> None:
    engine = Sam2Engine("sam2-small")
    assert engine.runtime_device == "cpu"
    engine.close()
    assert engine.runtime_device == "cpu"


@pytest.mark.gpu
def test_sam2_checkpoint_is_usable_on_cuda() -> None:
    """Valida prerrequisitos reales sin descargar nada ni ejecutar una inferencia pesada."""
    if os.environ.get("ATLAS_SPLITTER_GPU_TEST") != "1":
        pytest.skip("Defina ATLAS_SPLITTER_GPU_TEST=1 para activar la prueba GPU")
    if importlib.util.find_spec("torch") is None or importlib.util.find_spec("sam2") is None:
        pytest.skip("PyTorch o SAM 2 no están instalados")
    import torch

    if not torch.cuda.is_available() or not is_downloaded("sam2-small"):
        pytest.skip("CUDA o el checkpoint sam2-small no están disponibles")
    assert Sam2Engine("sam2-small", "cuda").is_available
