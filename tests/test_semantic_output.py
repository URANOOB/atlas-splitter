from __future__ import annotations

from pathlib import Path

from PIL import Image

from atlas_splitter.semantic.grouping_service import _organize_semantic_output
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
    routed = list(tmp_path.glob("objects/**/*.png")) + list(tmp_path.glob("uncertain/**/*.png")) + list(tmp_path.glob("unassigned/*.png"))
    assert sorted(path.name for path in routed) == [f"element_{index:03d}.png" for index in range(1, 5)]
    assert "rejected_001" not in artifacts
    assert pieces["E003"].png_path.is_file()
