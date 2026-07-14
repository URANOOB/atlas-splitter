"""Contratos CPU de la conversión semántica a review.json."""

import json
from pathlib import Path

import pytest

from atlas_splitter.exceptions import InvalidReviewError
from atlas_splitter.review import create_semantic_review_template


def _write_manifests(root: Path, groups: list[dict[str, object]], unassigned: list[str]) -> tuple[Path, Path]:
    visual = root / "manifest.json"
    semantic = root / "semantic_manifest.json"
    visual.write_text(json.dumps({"elements": [{}, {}, {}, {}]}), encoding="utf-8")
    semantic.write_text(json.dumps({"groups": groups, "unassigned_piece_ids": unassigned}), encoding="utf-8")
    return visual, semantic


def test_semantic_review_covers_accepted_uncertain_rejected_and_unassigned(tmp_path: Path) -> None:
    visual, semantic = _write_manifests(
        tmp_path,
        [
            {"name": "Walls!", "piece_ids": ["E001"], "confidence": 0.91, "status": "accepted"},
            {"name": "wall/unsafe", "piece_ids": ["E002"], "confidence": 0.72, "status": "uncertain"},
            {"name": "bad", "piece_ids": ["E003"], "confidence": 0.2, "status": "rejected"},
        ],
        ["E004"],
    )

    review = json.loads(create_semantic_review_template(visual, semantic, tmp_path).read_text(encoding="utf-8"))

    assert review["source"] == "semantic"
    assert review["groups"] == [
        {"name": "walls", "piece_ids": ["E001"], "confidence": 0.91, "status": "accepted"},
        {"name": "wall_unsafe", "piece_ids": ["E002"], "confidence": 0.72, "status": "uncertain"},
    ]
    assert review["unassigned_piece_ids"] == ["E003", "E004"]


@pytest.mark.parametrize(
    ("groups", "unassigned", "message"),
    [
        ([{"name": "a", "piece_ids": ["E001"], "confidence": 1, "status": "accepted"}], ["E001"], "duplicado"),
        ([{"name": "a", "piece_ids": ["E001"], "confidence": 1, "status": "accepted"}], [], "Faltan"),
    ],
)
def test_semantic_review_rejects_duplicate_and_missing_ids(
    tmp_path: Path, groups: list[dict[str, object]], unassigned: list[str], message: str
) -> None:
    visual, semantic = _write_manifests(tmp_path, groups, unassigned)

    with pytest.raises(InvalidReviewError, match=message):
        create_semantic_review_template(visual, semantic, tmp_path)


def test_semantic_review_rejects_corrupt_manifest(tmp_path: Path) -> None:
    visual = tmp_path / "manifest.json"
    semantic = tmp_path / "semantic_manifest.json"
    visual.write_text("{not json", encoding="utf-8")
    semantic.write_text("{}", encoding="utf-8")

    with pytest.raises(InvalidReviewError, match="No se pudieron leer"):
        create_semantic_review_template(visual, semantic, tmp_path)
