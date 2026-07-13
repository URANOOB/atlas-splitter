from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from atlas_splitter.config import AppConfig
from atlas_splitter.io.image_loader import LoadedImage
from atlas_splitter.reporting.annotated_atlas import write_annotated_atlas
from atlas_splitter.reporting.semantic_contact_sheet import write_semantic_contact_sheet
from atlas_splitter.semantic.fake_backend import FakeSemanticGroupingBackend
from atlas_splitter.semantic.prompt_builder import build_grouping_prompt
from atlas_splitter.semantic.response_parser import SemanticResponseParseError, parse_response_json
from atlas_splitter.semantic.types import GroupingContext, GroupingResult, PieceReference, SemanticGroup
from atlas_splitter.semantic.validator import SemanticResponseValidationError, validate_groups


def _piece(tmp_path: Path, index: int = 1) -> PieceReference:
    png = tmp_path / f"element_{index:03d}.png"
    Image.new("RGBA", (20, 10), (255, 0, 0, 128)).save(png)
    return PieceReference(f"E{index:03d}", index, png, tmp_path / "mask.png", None, (2, 3, 20, 10), 200, "classical")


def test_grouping_defaults_and_domain_models(tmp_path: Path) -> None:
    piece = _piece(tmp_path)
    group = SemanticGroup("house_001", "house", "house", [piece.piece_id], 0.9, "accepted")
    result = GroupingResult([group], [], "fake", "none", 0.01)
    assert not AppConfig().grouping.enabled
    assert result.groups[0].piece_ids == ["E001"]


def test_prompt_and_parser_are_stable() -> None:
    prompt = build_grouping_prompt()
    assert prompt == build_grouping_prompt()
    assert "exactly once" in prompt
    assert parse_response_json('Prefix {"groups": [], "unassigned_piece_ids": ["E001"]} suffix')["groups"] == []
    with pytest.raises(SemanticResponseParseError):
        parse_response_json("not structured")


def test_validator_assigns_deterministic_statuses_and_rejects_bad_coverage() -> None:
    payload: dict[str, object] = {
        "groups": [
            {"name": "house", "piece_ids": ["E001"], "confidence": 0.85},
            {"name": "house", "piece_ids": ["E002"], "confidence": 0.2},
        ],
        "unassigned_piece_ids": ["E003"],
    }
    groups, unassigned = validate_groups(payload, {"E001", "E002", "E003"}, 0.70, 0.80)
    assert [group.group_id for group in groups] == ["house_001", "house_002"]
    assert [group.status for group in groups] == ["accepted", "rejected"]
    assert unassigned == ["E003", "E002"]
    with pytest.raises(SemanticResponseValidationError, match="inexistente"):
        validate_groups({"groups": [], "unassigned_piece_ids": ["E999"]}, {"E001"}, 0.70, 0.80)


def test_fake_backend_and_semantic_visuals(tmp_path: Path) -> None:
    pieces = [_piece(tmp_path, 1), _piece(tmp_path, 2)]
    context = GroupingContext(pieces, tmp_path / "atlas.png", [], build_grouping_prompt())
    backend = FakeSemanticGroupingBackend(GroupingResult([], ["E001", "E002"], "fake", "test", 0.0))
    assert backend.group(context).unassigned_piece_ids == ["E001", "E002"]
    backend.close()
    assert backend.closed

    sheet = tmp_path / "semantic-sheet.png"
    write_semantic_contact_sheet(sheet, pieces)
    pixels = np.zeros((40, 80, 4), dtype=np.uint8)
    pixels[:, :, 3] = 255
    annotated = tmp_path / "annotated.png"
    write_annotated_atlas(annotated, LoadedImage(Path("atlas.webp"), pixels, "hash"), pieces)
    assert Image.open(sheet).size[0] >= 220
    assert Image.open(annotated).size == (80, 40)
