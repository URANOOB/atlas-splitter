import pytest
from pydantic import ValidationError

from atlas_splitter.config import AppConfig, apply_cli_overrides, load_config


def test_default_config_has_expected_values() -> None:
    config = load_config()
    assert config.device == "auto"
    assert config.segmentation.min_area == 400


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
