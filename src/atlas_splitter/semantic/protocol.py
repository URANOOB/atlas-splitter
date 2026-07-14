"""Contrato extensible para backends de agrupación."""

from __future__ import annotations

from typing import Protocol

from atlas_splitter.semantic.types import GroupingContext, GroupingResult


class SemanticGroupingBackend(Protocol):
    """Motor local que propone asociaciones entre piezas extraídas."""

    def group(self, context: GroupingContext) -> GroupingResult:
        """Agrupa las piezas presentes en el contexto."""

    def close(self) -> None:
        """Libera los recursos retenidos por el backend."""
