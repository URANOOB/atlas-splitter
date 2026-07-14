"""Contratos estrictos para respuestas Qwen por candidato, sin efectos laterales."""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

_CANDIDATE_ID = re.compile(r"^element_[a-zA-Z0-9_-]{1,120}$")


class CandidateSemanticAssessment(BaseModel):
    """Clasificación semántica de una región previamente segmentada."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    candidate_id: str
    label: str = Field(min_length=1, max_length=80)
    category: str = Field(min_length=1, max_length=80)
    object_group: str = Field(min_length=1, max_length=80)
    part_role: str = Field(min_length=1, max_length=80)
    orientation: str = Field(min_length=1, max_length=40)
    confidence: float = Field(ge=0.0, le=1.0)
    related_candidates: list[str] = Field(default_factory=list, max_length=100)
    discard: bool
    reason: str = Field(default="", max_length=500)

    @field_validator("candidate_id", "related_candidates", mode="after")
    @classmethod
    def _validate_candidate_id(cls, value: str | list[str]) -> str | list[str]:
        values = [value] if isinstance(value, str) else value
        if not all(_CANDIDATE_ID.fullmatch(item) for item in values):
            raise ValueError("candidate IDs must use the stable element_<id> format")
        return value


class SemanticAnalysisResponse(BaseModel):
    """Respuesta completa, validada antes de convertir texto en rutas o grupos."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    candidates: list[CandidateSemanticAssessment] = Field(default_factory=list)

    @field_validator("candidates")
    @classmethod
    def _unique_candidates(cls, value: list[CandidateSemanticAssessment]) -> list[CandidateSemanticAssessment]:
        identifiers = [candidate.candidate_id for candidate in value]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("candidate_id values must be unique")
        return value
