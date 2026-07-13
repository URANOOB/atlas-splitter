"""Modelos de dominio independientes de la segmentación."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass(frozen=True, slots=True)
class PieceReference:
    """Artefactos y metadatos de una pieza ya extraída."""

    piece_id: str
    element_index: int
    png_path: Path
    mask_path: Path
    psd_path: Path | None
    bbox: tuple[int, int, int, int]
    area: int
    source: str
    mask_bounds: tuple[int, int, int, int] | None = None


@dataclass(frozen=True, slots=True)
class SemanticGroup:
    """Propuesta semántica validada para un conjunto de piezas."""

    group_id: str
    name: str
    slug: str
    piece_ids: list[str]
    confidence: float
    status: Literal["accepted", "uncertain", "rejected"]


@dataclass(frozen=True, slots=True)
class GroupingResult:
    """Resultado completo de un backend de agrupación."""

    groups: list[SemanticGroup]
    unassigned_piece_ids: list[str]
    backend: str
    model: str
    elapsed_seconds: float


@dataclass(frozen=True, slots=True)
class GroupingContext:
    """Entradas visuales y piezas que un backend puede analizar."""

    pieces: list[PieceReference]
    annotated_atlas_path: Path
    contact_sheet_paths: list[Path]
    prompt: str
