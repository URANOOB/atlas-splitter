"""Escritura del índice global de una extracción geométrica multiatlas."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from atlas_splitter import __version__
from atlas_splitter.domain import ProjectAtlas, ProjectManifest, slugify, write_versioned_manifest
from atlas_splitter.geometry.object_grouping import ExportedAtlas


def write_project_manifest(destination: Path, source_model: Path, atlases: list[ExportedAtlas]) -> ProjectManifest:
    """Publica ``project.json`` tras terminar todas las exportaciones de atlas."""
    records = [
        ProjectAtlas(
            atlas_id=slugify(atlas.atlas_path.stem, fallback="atlas"),
            source_file=str(atlas.atlas_path.resolve()),
            output_directory=str(atlas.output_directory.relative_to(destination.parent).as_posix()),
            association_method=atlas.association_method,
            confidence=atlas.association_confidence,
            manual_confirmation=atlas.manual_confirmation,
            texture_slot=atlas.texture_slot,
            element_ids=[element.element_id for element in atlas.manifest.elements],
        )
        for atlas in atlases
    ]
    manifest = ProjectManifest(
        tool_version=__version__,
        created_at=datetime.now(UTC).isoformat(),
        source_files=[str(source_model.resolve()), *[item.source_file for item in records]],
        warnings=["Las asociaciones de atlas conservan su método y confianza; no se infirieron asociaciones ambiguas."],
        atlases=records,
    )
    write_versioned_manifest(destination, manifest)
    return manifest
