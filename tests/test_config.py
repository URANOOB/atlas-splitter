import pytest
from pydantic import ValidationError

from atlas_splitter.config import AppConfig, apply_cli_overrides, load_config, write_default_config


def test_default_config_has_expected_values() -> None:
    config = load_config()
    assert config.device == "cuda"
    assert config.grouping.device == "cuda"
    assert config.segmentation.min_area == 400
    assert config.gltf.group_by == "uv-island"
    assert config.semantic.enabled is False


def test_rejects_out_of_range_confidence() -> None:
    with pytest.raises(ValidationError):
        AppConfig.model_validate({"segmentation": {"confidence": 1.1}})


def test_cli_values_override_config() -> None:
    config = apply_cli_overrides(load_config(), {"device": "cpu", "segmentation.min_area": 12})
    assert config.device == "cpu"
    assert config.segmentation.min_area == 12


def test_grouping_rejects_inverted_confidence_thresholds() -> None:
    with pytest.raises(ValidationError):
        AppConfig.model_validate({"grouping": {"minimum_confidence": 0.9, "automatic_confidence": 0.8}})


def test_writes_default_yaml_without_overwriting_user_file(tmp_path) -> None:
    config = write_default_config(tmp_path / "atlas-splitter.yaml")
    assert load_config(config).processing.padding == 16
    config.write_text("device: cpu\n", encoding="utf-8")
    assert write_default_config(config).read_text(encoding="utf-8") == "device: cpu\n"
