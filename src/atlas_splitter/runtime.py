"""Decisiones de runtime compartidas por los backends locales opcionales."""

from __future__ import annotations

import importlib
import logging
from typing import Literal

from atlas_splitter.exceptions import DeviceResolutionError

LOGGER = logging.getLogger(__name__)
Device = Literal["auto", "cpu", "cuda"]


def resolve_device(requested_device: str) -> str:
    """Resuelve ``auto`` sin pasar nunca ese valor a PyTorch o a un modelo.

    CUDA es una petición explícita: si no está disponible se informa el problema
    en lugar de ejecutar silenciosamente un resultado potencialmente muy lento en
    CPU. ``auto`` sí puede degradarse a CPU de forma segura.
    """
    if requested_device not in {"auto", "cpu", "cuda"}:
        raise DeviceResolutionError(f"Dispositivo no compatible: {requested_device}. Use auto, cpu o cuda.")
    if requested_device == "cpu":
        LOGGER.info("Dispositivo solicitado: cpu; dispositivo seleccionado: cpu.")
        return "cpu"
    try:
        torch = importlib.import_module("torch")
        cuda_available = bool(torch.cuda.is_available())
    except ImportError:
        cuda_available = False
    if requested_device == "cuda":
        if not cuda_available:
            raise DeviceResolutionError(
                "Dispositivo solicitado: cuda. CUDA no está disponible; instale una versión de PyTorch con CUDA "
                "o use --device cpu/auto."
            )
        LOGGER.info("Dispositivo solicitado: cuda; dispositivo seleccionado: cuda.")
        return "cuda"
    if cuda_available:
        LOGGER.info("Dispositivo solicitado: auto; dispositivo seleccionado: cuda.")
        return "cuda"
    LOGGER.info("Dispositivo solicitado: auto; dispositivo seleccionado: cpu. CUDA no está disponible; se usará CPU.")
    return "cpu"
