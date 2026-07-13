"""Validación y normalización de propuestas de agrupación."""

from __future__ import annotations

import re
from typing import Literal

from atlas_splitter.semantic.types import SemanticGroup

_SLUG_RE = re.compile(r"^[a-z][a-z0-9_]*$")


class SemanticResponseValidationError(ValueError):
    """La propuesta semántica no cumple el contrato de piezas."""


def validate_groups(
    payload: dict[str, object],
    piece_ids: set[str],
    minimum_confidence: float,
    automatic_confidence: float,
) -> tuple[list[SemanticGroup], list[str]]:
    """Valida cobertura exacta y asigna estados y IDs estables a cada grupo."""
    raw_groups = payload.get("groups")
    unassigned = payload.get("unassigned_piece_ids")
    if not isinstance(raw_groups, list) or not isinstance(unassigned, list):
        raise SemanticResponseValidationError("Se requieren listas groups y unassigned_piece_ids.")
    seen: set[str] = set()
    raw_validated: list[tuple[str, list[str], float]] = []
    for item in raw_groups:
        if not isinstance(item, dict):
            raise SemanticResponseValidationError("Cada grupo debe ser un objeto.")
        name, members, confidence = item.get("name"), item.get("piece_ids"), item.get("confidence")
        if not isinstance(name, str) or not name or not _SLUG_RE.fullmatch(name):
            raise SemanticResponseValidationError("El nombre debe ser snake_case no vacío.")
        if not isinstance(members, list) or not members or not all(isinstance(member, str) for member in members):
            raise SemanticResponseValidationError("Un grupo debe incluir piece_ids no vacíos.")
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            raise SemanticResponseValidationError("La confianza debe estar entre 0 y 1.")
        for member in members:
            if member not in piece_ids:
                raise SemanticResponseValidationError(f"ID inexistente: {member}")
            if member in seen:
                raise SemanticResponseValidationError(f"ID duplicado: {member}")
            seen.add(member)
        raw_validated.append((name, members, float(confidence)))
    if not all(isinstance(member, str) for member in unassigned):
        raise SemanticResponseValidationError("Los IDs no asignados deben ser texto.")
    for member in unassigned:
        if member not in piece_ids:
            raise SemanticResponseValidationError(f"ID inexistente: {member}")
        if member in seen:
            raise SemanticResponseValidationError(f"ID duplicado: {member}")
        seen.add(member)
    missing = piece_ids - seen
    if missing:
        raise SemanticResponseValidationError(f"Faltan IDs: {', '.join(sorted(missing))}")
    counters: dict[str, int] = {}
    groups: list[SemanticGroup] = []
    rejected_ids: list[str] = []
    for name, members, confidence in raw_validated:
        counters[name] = counters.get(name, 0) + 1
        group_id = f"{name}_{counters[name]:03d}"
        status: Literal["accepted", "uncertain", "rejected"]
        if confidence >= automatic_confidence:
            status = "accepted"
        elif confidence >= minimum_confidence:
            status = "uncertain"
        else:
            status = "rejected"
            rejected_ids.extend(members)
        groups.append(SemanticGroup(group_id, name, name, members, confidence, status))
    return groups, [*unassigned, *rejected_ids]
