from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from atlas_splitter.exceptions import DeviceResolutionError
from atlas_splitter.runtime import resolve_device


def _torch(cuda_available: bool) -> SimpleNamespace:
    return SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: cuda_available))


def test_resolve_device_auto_uses_cpu_without_cuda(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "torch", _torch(False))
    assert resolve_device("auto") == "cpu"


def test_resolve_device_auto_uses_cuda_when_available(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "torch", _torch(True))
    assert resolve_device("auto") == "cuda"


def test_resolve_device_cpu_never_requires_torch() -> None:
    assert resolve_device("cpu") == "cpu"


def test_resolve_device_cuda_fails_clearly_without_cuda(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "torch", _torch(False))
    with pytest.raises(DeviceResolutionError, match="CUDA no está disponible"):
        resolve_device("cuda")
