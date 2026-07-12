import pytest

from atlas_splitter.models.manager import checkpoint_path, is_downloaded
from atlas_splitter.models.registry import get_model


def test_registry_resolves_small_model() -> None:
    spec = get_model("sam2-small")
    assert spec.checkpoint_filename == "sam2.1_hiera_small.pt"


def test_checkpoint_state_is_local_and_explicit(tmp_path) -> None:
    path = checkpoint_path("sam2-tiny", tmp_path)
    assert not is_downloaded("sam2-tiny", tmp_path)
    path.write_bytes(b"checkpoint")
    assert is_downloaded("sam2-tiny", tmp_path)


def test_unknown_model_is_rejected() -> None:
    with pytest.raises(ValueError, match="no admitido"):
        get_model("sam2-large")
