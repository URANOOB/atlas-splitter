"""Manifiesto atómico de la agrupación semántica."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atlas_splitter.semantic.types import GroupingResult


def write_grouping_manifest(
    destination: Path,
    result: GroupingResult,
    device: str,
    groups_artifacts: dict[str, dict[str, object]],
    parameters: dict[str, Any],
    errors: list[str] | None = None,
    repaired_responses: int = 0,
) -> None:
    """Publica el informe semántico solo tras escribir su JSON completo."""
    data = {
        "source_manifest": "manifest.json",
        "backend": result.backend,
        "model": result.model,
        "device": device,
        "elapsed_seconds": round(result.elapsed_seconds, 6),
        "repaired_responses": repaired_responses,
        "semantic_errors": errors or [],
        "parameters": parameters,
        "groups": [
            {
                "group_id": group.group_id,
                "name": group.name,
                "slug": group.slug,
                "piece_ids": group.piece_ids,
                "confidence": group.confidence,
                "status": group.status,
                **groups_artifacts.get(group.group_id, {}),
            }
            for group in result.groups
        ],
        "unassigned_piece_ids": result.unassigned_piece_ids,
    }
    temporary = destination.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(destination)
