"""Generación atómica del manifiesto JSON."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from atlas_splitter.config import AppConfig
from atlas_splitter.io.image_loader import LoadedImage
from atlas_splitter.segmentation.classical import MaskCandidate


def write_manifest(
    destination: Path,
    image: LoadedImage,
    config: AppConfig,
    candidates_initial: int,
    discarded: int,
    elements: list[MaskCandidate],
    elapsed_seconds: float,
) -> None:
    """Escribe metadatos reproducibles y asociaciones de cada elemento."""
    data = {
        "source_file": str(image.path.resolve()),
        "sha256": image.sha256,
        "dimensions": {"width": image.width, "height": image.height, "channels": 4},
        "processed_at": datetime.now(UTC).isoformat(),
        "device": "cpu",
        "model": config.model,
        "parameters": config.model_dump(mode="json"),
        "elapsed_seconds": round(elapsed_seconds, 6),
        "initial_masks": candidates_initial,
        "discarded_masks": discarded,
        "final_elements": len(elements),
        "elements": [
            {
                "name": f"element_{index:03d}",
                "bbox": {
                    "x": item.bbox[0],
                    "y": item.bbox[1],
                    "width": item.bbox[2],
                    "height": item.bbox[3],
                },
                "area": item.area,
                "confidence": item.confidence,
                "stability": item.stability,
                "source": item.source,
                "png": f"png/element_{index:03d}.png",
                "mask": f"masks/element_{index:03d}.png",
                "psd": f"psd/element_{index:03d}.psd" if config.output.include_psd else None,
            }
            for index, item in enumerate(elements, start=1)
        ],
    }
    temporary = destination.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(destination)
