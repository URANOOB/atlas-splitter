"""Decisiones de dispositivo compartidas por los backends locales opcionales."""

from __future__ import annotations

import importlib
import logging
from dataclasses import dataclass
from typing import Literal, cast

from atlas_splitter.exceptions import DeviceResolutionError

LOGGER = logging.getLogger(__name__)
RequestedDevice = Literal["auto", "cpu", "cuda", "mps"]
SelectedDevice = Literal["cpu", "cuda", "mps"]


@dataclass(frozen=True, slots=True)
class DeviceResolution:
    """Resultado auditable de convertir una preferencia en un dispositivo real."""

    requested: RequestedDevice
    selected: SelectedDevice
    fallback_used: bool
    reason: str


def resolve_device(requested_device: str) -> DeviceResolution:
    """Resuelve ``auto`` sin entregar nunca ese valor a PyTorch o a un modelo.

    La detección sólo consulta capacidades locales: no inicia descargas ni cambia
    el entorno. Las solicitudes explícitas de CUDA o MPS fallan si no están
    disponibles; sólo ``auto`` puede degradarse a CPU.
    """
    if requested_device not in {"auto", "cpu", "cuda", "mps"}:
        raise DeviceResolutionError(f"Dispositivo no compatible: {requested_device}. Use auto, cpu, cuda o mps.")
    requested = cast(RequestedDevice, requested_device)
    if requested == "cpu":
        return _report(DeviceResolution(requested, "cpu", False, "CPU fue solicitada explícitamente."))

    torch = _load_torch()
    cuda_available = _cuda_available(torch)
    mps_available = _mps_available(torch)
    if requested == "cuda":
        if not cuda_available:
            raise DeviceResolutionError(
                "Dispositivo solicitado: cuda. CUDA no está disponible; instale una versión de PyTorch con CUDA "
                "o use --device cpu/auto."
            )
        return _report(DeviceResolution(requested, "cuda", False, "CUDA está disponible."))
    if requested == "mps":
        if not mps_available:
            raise DeviceResolutionError(
                "Dispositivo solicitado: mps. MPS no está disponible; use --device cpu/auto o una instalación "
                "de PyTorch con soporte MPS."
            )
        return _report(DeviceResolution(requested, "mps", False, "MPS está disponible."))
    if cuda_available:
        return _report(DeviceResolution(requested, "cuda", False, "CUDA está disponible."))
    if mps_available:
        return _report(DeviceResolution(requested, "mps", False, "CUDA no está disponible; MPS está disponible."))
    return _report(DeviceResolution(requested, "cpu", True, "CUDA y MPS no están disponibles; se usará CPU."))


def _load_torch() -> object | None:
    try:
        return importlib.import_module("torch")
    except ImportError:
        return None


def _cuda_available(torch: object | None) -> bool:
    cuda = getattr(torch, "cuda", None)
    is_available = getattr(cuda, "is_available", None)
    return bool(is_available()) if callable(is_available) else False


def _mps_available(torch: object | None) -> bool:
    backends = getattr(torch, "backends", None)
    mps = getattr(backends, "mps", None)
    is_available = getattr(mps, "is_available", None)
    return bool(is_available()) if callable(is_available) else False


def _report(resolution: DeviceResolution) -> DeviceResolution:
    LOGGER.info(
        "Dispositivo solicitado: %s; dispositivo seleccionado: %s. Motivo: %s",
        resolution.requested,
        resolution.selected,
        resolution.reason,
    )
    return resolution
