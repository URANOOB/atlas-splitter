from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from atlas_splitter.config import GroupingConfig
from atlas_splitter.semantic.fake_backend import FakeSemanticGroupingBackend
from atlas_splitter.semantic.grouping_service import _organize_semantic_output, group_extracted_atlas
from atlas_splitter.semantic.types import GroupingResult, PieceReference, SemanticGroup


def _piece(root: Path, index: int) -> PieceReference:
    path = root / f"element_{index:03d}.png"
    Image.new("RGBA", (2, 2), (index, 0, 0, 255)).save(path)
    return PieceReference(f"E{index:03d}", index, path, root / "mask.png", None, (0, 0, 2, 2), 4, "test")


def test_semantic_output_routes_every_status_once(tmp_path: Path) -> None:
    pieces = {f"E{index:03d}": _piece(tmp_path, index) for index in range(1, 5)}
    result = GroupingResult(
        [
            SemanticGroup("accepted_001", "accepted", "accepted", ["E001"], 0.9, "accepted"),
            SemanticGroup("uncertain_001", "uncertain", "uncertain", ["E002"], 0.75, "uncertain"),
            SemanticGroup("rejected_001", "rejected", "rejected", ["E003"], 0.1, "rejected"),
        ],
        ["E004", "E003"],
        "fake",
        "test",
        0.0,
    )
    artifacts = {"accepted_001": {}, "uncertain_001": {}}

    _organize_semantic_output(tmp_path, result, pieces, artifacts)

    assert (tmp_path / "objects" / "accepted_001" / "element_001.png").is_file()
    assert (tmp_path / "uncertain" / "uncertain_001" / "element_002.png").is_file()
    assert (tmp_path / "unassigned" / "element_003.png").is_file()
    assert (tmp_path / "unassigned" / "element_004.png").is_file()
    routed = (
        list(tmp_path.glob("objects/**/*.png"))
        + list(tmp_path.glob("uncertain/**/*.png"))
        + list(tmp_path.glob("unassigned/*.png"))
    )
    assert sorted(path.name for path in routed) == [f"element_{index:03d}.png" for index in range(1, 5)]
    assert "rejected_001" not in artifacts
    assert pieces["E003"].png_path.is_file()


def test_group_extracted_atlas_preserves_rejected_response_and_routes_every_piece(tmp_path: Path) -> None:
    atlas = tmp_path / "atlas.png"
    Image.new("RGBA", (8, 8), (255, 255, 255, 255)).save(atlas)
    elements: list[dict[str, object]] = []
    for index in range(1, 5):
        png = tmp_path / f"element_{index:03d}.png"
        mask = tmp_path / f"mask_{index:03d}.png"
        Image.new("RGBA", (2, 2), (index, 0, 0, 255)).save(png)
        Image.new("L", (2, 2), 255).save(mask)
        elements.append(
            {
                "name": f"element_{index:03d}",
                "png": png.name,
                "mask": mask.name,
                "bbox": {"x": 0, "y": 0, "width": 2, "height": 2},
                "area": 4,
                "source": "classical",
            }
        )
    (tmp_path / "manifest.json").write_text(
        json.dumps(
            {
                "source_file": str(atlas),
                "dimensions": {"width": 8, "height": 8},
                "parameters": {"processing": {"crop_elements": True, "padding": 0}},
                "elements": elements,
            }
        ),
        encoding="utf-8",
    )
    result = GroupingResult(
        [
            SemanticGroup("accepted_001", "accepted", "accepted", ["E001"], 0.91, "accepted"),
            SemanticGroup("uncertain_001", "uncertain", "uncertain", ["E002"], 0.72, "uncertain"),
            SemanticGroup("rejected_001", "rejected", "rejected", ["E003"], 0.21, "rejected"),
        ],
        ["E004", "E003"],
        "fake",
        "test",
        0.0,
    )

    returned = group_extracted_atlas(tmp_path, GroupingConfig(), FakeSemanticGroupingBackend(result))

    manifest = json.loads((tmp_path / "semantic_manifest.json").read_text(encoding="utf-8"))
    assert returned == result
    assert manifest["groups"][2] == {
        "group_id": "rejected_001",
        "name": "rejected",
        "slug": "rejected",
        "piece_ids": ["E003"],
        "confidence": 0.21,
        "status": "rejected",
    }
    assert sorted(path.name for path in (tmp_path / "unassigned").glob("*.png")) == [
        "element_003.png",
        "element_004.png",
    ]
    routed = [
        *tmp_path.glob("objects/**/*.png"),
        *tmp_path.glob("uncertain/**/*.png"),
        *(tmp_path / "unassigned").glob("*.png"),
    ]
    assert sorted(path.name for path in routed) == [f"element_{index:03d}.png" for index in range(1, 5)]
