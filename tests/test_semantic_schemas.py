"""Pruebas CPU del contrato estructurado para respuestas Qwen."""

import pytest
from pydantic import ValidationError

from atlas_splitter.semantic.prompt_builder import build_candidate_analysis_prompt
from atlas_splitter.semantic.schemas import SemanticAnalysisResponse


def test_candidate_schema_accepts_strict_valid_response() -> None:
    response = SemanticAnalysisResponse.model_validate({"candidates": [_valid_candidate()]})
    assert response.candidates[0].label == "roof"


def test_candidate_schema_rejects_unsafe_or_duplicate_identifiers() -> None:
    payload = {"candidates": [_valid_candidate(candidate_id="../unsafe")]}
    with pytest.raises(ValidationError):
        SemanticAnalysisResponse.model_validate(payload)


def test_candidate_prompt_forbids_side_effects() -> None:
    prompt = build_candidate_analysis_prompt()
    assert "never write files" in prompt
    assert "Return JSON only" in prompt


def _valid_candidate(**overrides: object) -> dict[str, object]:
    candidate: dict[str, object] = {
        "candidate_id": "element_001",
        "label": "roof",
        "category": "architecture",
        "object_group": "house_001",
        "part_role": "roof",
        "orientation": "front",
        "confidence": 0.91,
        "related_candidates": [],
        "discard": False,
        "reason": "tiles",
    }
    candidate.update(overrides)
    return candidate
