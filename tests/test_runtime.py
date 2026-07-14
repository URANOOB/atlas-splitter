from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from atlas_splitter.exceptions import DeviceResolutionError
from atlas_splitter.runtime import resolve_device


def _torch(cuda_available: bool, mps_available: bool = False) -> SimpleNamespace:
    return SimpleNamespace(
        cuda=SimpleNamespace(is_available=lambda: cuda_available),
        backends=SimpleNamespace(mps=SimpleNamespace(is_available=lambda: mps_available)),
    )


def test_resolve_device_auto_uses_cpu_without_cuda(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "torch", _torch(False))
    resolution = resolve_device("auto")
    assert resolution.selected == "cpu"
    assert resolution.fallback_used
    assert resolution.reason == "CUDA y MPS no están disponibles; se usará CPU."


def test_resolve_device_auto_uses_cuda_when_available(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "torch", _torch(True))
    resolution = resolve_device("auto")
    assert resolution.selected == "cuda"
    assert not resolution.fallback_used


def test_resolve_device_cpu_never_requires_torch() -> None:
    resolution = resolve_device("cpu")
    assert resolution.selected == "cpu"
    assert resolution.requested == "cpu"
    assert not resolution.fallback_used


def test_resolve_device_cuda_fails_clearly_without_cuda(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "torch", _torch(False))
    with pytest.raises(DeviceResolutionError, match="CUDA no está disponible"):
        resolve_device("cuda")


def test_resolve_device_auto_uses_mps_after_cuda(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "torch", _torch(False, True))

    resolution = resolve_device("auto")

    assert resolution.selected == "mps"
    assert not resolution.fallback_used
    assert resolution.reason == "CUDA no está disponible; MPS está disponible."


def test_resolve_device_mps_is_explicit_and_fails_when_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "torch", _torch(False, False))

    with pytest.raises(DeviceResolutionError, match="MPS no está disponible"):
        resolve_device("mps")


def test_resolve_device_mps_uses_available_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "torch", _torch(False, True))

    resolution = resolve_device("mps")

    assert resolution.requested == "mps"
    assert resolution.selected == "mps"
    assert not resolution.fallback_used


def test_structured_device_error_has_stable_code_cause_and_solution(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "torch", _torch(False))

    with pytest.raises(DeviceResolutionError) as raised:
        resolve_device("cuda")

    message = str(raised.value)
    assert "AS-MODEL-003" in message
    assert "Causa probable:" in message
    assert "Solucion:" in message
