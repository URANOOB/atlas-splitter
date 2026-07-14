import json

import pytest
from PIL import Image

from atlas_splitter.exceptions import InvalidReviewError
from atlas_splitter.review import apply_review, create_review_template


def _output(tmp_path) -> None:
    (tmp_path / "png").mkdir()
    elements = []
    for index in range(1, 3):
        name = f"element_{index:03d}.png"
        Image.new("RGBA", (2, 2), (index, 0, 0, 255)).save(tmp_path / "png" / name)
        elements.append({"png": f"png/{name}"})
    (tmp_path / "manifest.json").write_text(json.dumps({"elements": elements}), encoding="utf-8")


def test_review_template_and_apply_preserve_every_piece_once(tmp_path) -> None:
    _output(tmp_path)
    review = create_review_template(tmp_path)
    review.write_text(
        json.dumps(
            {"version": 1, "groups": [{"name": "walls", "piece_ids": ["E001"]}], "unassigned_piece_ids": ["E002"]}
        ),
        encoding="utf-8",
    )

    applied = apply_review(review)

    assert applied.is_file()
    assert (tmp_path / "groups" / "walls" / "pieces" / "element_001.png").is_file()
    assert (tmp_path / "unassigned" / "element_002.png").is_file()
    assert (tmp_path / "png" / "element_001.png").is_file()


def test_review_rejects_duplicate_or_missing_pieces(tmp_path) -> None:
    _output(tmp_path)
    review = tmp_path / "review.json"
    review.write_text(
        json.dumps(
            {"version": 1, "groups": [{"name": "walls", "piece_ids": ["E001"]}], "unassigned_piece_ids": ["E001"]}
        ),
        encoding="utf-8",
    )

    with pytest.raises(InvalidReviewError, match="duplicado"):
        apply_review(review)
