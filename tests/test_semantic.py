from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from atlas_splitter.config import AppConfig
from atlas_splitter.io.image_loader import LoadedImage
from atlas_splitter.reporting.annotated_atlas import write_annotated_atlas
from atlas_splitter.reporting.candidate_group_sheet import write_candidate_group_sheet
from atlas_splitter.reporting.group_preview import write_group_preview
from atlas_splitter.reporting.grouping_manifest import write_grouping_manifest
from atlas_splitter.reporting.semantic_contact_sheet import write_semantic_contact_sheet
from atlas_splitter.semantic.fake_backend import FakeSemanticGroupingBackend
from atlas_splitter.semantic.prompt_builder import build_grouping_prompt
from atlas_splitter.semantic.qwen3_vl_engine import Qwen3VLSemanticGroupingBackend
from atlas_splitter.semantic.response_parser import SemanticResponseParseError, parse_response_json
from atlas_splitter.semantic.types import GroupingContext, GroupingResult, PieceReference, SemanticGroup
from atlas_splitter.semantic.validator import SemanticResponseValidationError, validate_groups
from atlas_splitter.semantic_models.manager import (
    download_semantic_model,
    is_semantic_model_downloaded,
    semantic_model_path,
)
from atlas_splitter.semantic_models.registry import get_semantic_model


def _piece(tmp_path: Path, index: int = 1) -> PieceReference:
    png = tmp_path / f"element_{index:03d}.png"
    Image.new("RGBA", (20, 10), (255, 0, 0, 128)).save(png)
    return PieceReference(f"E{index:03d}", index, png, tmp_path / "mask.png", None, (2, 3, 20, 10), 200, "classical")


def test_grouping_config_defaults_to_disabled() -> None:
    assert not AppConfig().grouping.enabled
    assert AppConfig().grouping.max_pieces_per_sheet == 25


def test_domain_models_retain_piece_and_result_data(tmp_path: Path) -> None:
    piece = _piece(tmp_path)
    group = SemanticGroup("house_001", "house", "house", [piece.piece_id], 0.9, "accepted")
    result = GroupingResult([group], [], "fake", "none", 0.01)
    assert result.groups[0].piece_ids == ["E001"]


def test_prompt_is_stable_and_mentions_exact_coverage() -> None:
    prompt = build_grouping_prompt()
    assert prompt == build_grouping_prompt()
    assert "exactly once" in prompt
    assert "Return JSON only" in prompt


def test_parse_clean_and_embedded_json() -> None:
    assert parse_response_json('{"groups": [], "unassigned_piece_ids": ["E001"]}')["groups"] == []
    parsed = parse_response_json('Result follows: {"groups": [], "unassigned_piece_ids": ["E001"]} thanks')
    assert parsed["unassigned_piece_ids"] == ["E001"]


def test_parse_rejects_missing_json() -> None:
    with pytest.raises(SemanticResponseParseError):
        parse_response_json("not structured")


def test_validator_assigns_deterministic_ids_and_statuses() -> None:
    payload: dict[str, object] = {
        "groups": [
            {"name": "house", "piece_ids": ["E001"], "confidence": 0.85},
            {"name": "house", "piece_ids": ["E002"], "confidence": 0.75},
            {"name": "tree", "piece_ids": ["E003"], "confidence": 0.2},
        ],
        "unassigned_piece_ids": ["E004"],
    }
    groups, unassigned = validate_groups(payload, {"E001", "E002", "E003", "E004"}, 0.70, 0.80)
    assert [group.group_id for group in groups] == ["house_001", "house_002", "tree_001"]
    assert [group.status for group in groups] == ["accepted", "uncertain", "rejected"]
    assert unassigned == ["E004", "E003"]


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"groups": [], "unassigned_piece_ids": ["E999"]}, "inexistente"),
        (
            {"groups": [{"name": "house", "piece_ids": ["E001"], "confidence": 0.9}], "unassigned_piece_ids": ["E001"]},
            "duplicado",
        ),
        ({"groups": [], "unassigned_piece_ids": []}, "Faltan"),
        (
            {"groups": [{"name": "house", "piece_ids": ["E001"], "confidence": 2}], "unassigned_piece_ids": []},
            "confianza",
        ),
    ],
)
def test_validator_rejects_invalid_coverage(payload: dict[str, object], message: str) -> None:
    with pytest.raises(SemanticResponseValidationError, match=message):
        validate_groups(payload, {"E001"}, 0.70, 0.80)


def test_fake_backend_is_observable_and_closable(tmp_path: Path) -> None:
    context = GroupingContext([_piece(tmp_path)], tmp_path / "atlas.png", [], build_grouping_prompt())
    expected = GroupingResult([], ["E001"], "fake", "test", 0.0)
    backend = FakeSemanticGroupingBackend(expected)
    assert backend.group(context) is expected
    assert backend.last_context is context
    backend.close()
    assert backend.closed


def test_semantic_visual_inputs_are_written(tmp_path: Path) -> None:
    pieces = [_piece(tmp_path, 1), _piece(tmp_path, 2)]
    sheet = tmp_path / "semantic-sheet.png"
    write_semantic_contact_sheet(sheet, pieces)
    pixels = np.zeros((40, 80, 4), dtype=np.uint8)
    pixels[:, :, 3] = 255
    atlas = tmp_path / "annotated.png"
    write_annotated_atlas(atlas, LoadedImage(Path("atlas.webp"), pixels, "hash"), pieces)
    assert Image.open(sheet).size[0] >= 220
    assert Image.open(atlas).size == (80, 40)


def test_semantic_model_registry_and_local_state(tmp_path: Path) -> None:
    assert get_semantic_model("qwen3-vl-2b").repository_id == "Qwen/Qwen3-VL-2B-Instruct"
    path = semantic_model_path("qwen3-vl-2b", tmp_path)
    assert not is_semantic_model_downloaded("qwen3-vl-2b", tmp_path)
    path.mkdir(parents=True)
    (path / "config.json").write_text("{}", encoding="utf-8")
    assert is_semantic_model_downloaded("qwen3-vl-2b", tmp_path)


def test_explicit_download_uses_hub_snapshot_only_when_called(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, Path]] = []

    def fake_download(*, repo_id: str, local_dir: Path) -> str:
        calls.append((repo_id, local_dir))
        local_dir.mkdir(parents=True)
        (local_dir / "config.json").write_text("{}", encoding="utf-8")
        return str(local_dir)

    import sys
    from types import SimpleNamespace

    monkeypatch.setitem(sys.modules, "huggingface_hub", SimpleNamespace(snapshot_download=fake_download))
    result = download_semantic_model("qwen3-vl-2b", tmp_path)
    assert result == semantic_model_path("qwen3-vl-2b", tmp_path)
    assert calls == [("Qwen/Qwen3-VL-2B-Instruct", result)]


def test_qwen_backend_repairs_once_and_never_loads_implicitly(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    context = GroupingContext([_piece(tmp_path)], tmp_path / "atlas.png", [], build_grouping_prompt())
    backend = Qwen3VLSemanticGroupingBackend()
    responses = iter(["not json", '{"groups": [], "unassigned_piece_ids": ["E001"]}'])
    monkeypatch.setattr(backend, "_generate", lambda *args: next(responses))
    result = backend.group(context)
    assert result.unassigned_piece_ids == ["E001"]
    assert backend._model is None


def test_qwen_backend_falls_back_when_repair_is_invalid(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    context = GroupingContext([_piece(tmp_path)], tmp_path / "atlas.png", [], build_grouping_prompt())
    backend = Qwen3VLSemanticGroupingBackend()
    monkeypatch.setattr(backend, "_generate", lambda *args: "invalid")
    assert backend.group(context).unassigned_piece_ids == ["E001"]


def test_group_preview_and_manifest_are_non_destructive(tmp_path: Path) -> None:
    piece = _piece(tmp_path)
    mask = np.zeros((30, 40), dtype=np.uint8)
    mask[3:13, 2:22] = 255
    Image.fromarray(mask, "L").save(piece.mask_path)
    pixels = np.zeros((30, 40, 4), dtype=np.uint8)
    pixels[:, :, 3] = 255
    image = LoadedImage(Path("atlas.webp"), pixels, "hash")
    preview = tmp_path / "preview.png"
    write_group_preview(preview, image, [piece])
    result = GroupingResult(
        [SemanticGroup("house_001", "house", "house", ["E001"], 0.9, "accepted")], [], "fake", "test", 0.1
    )
    manifest = tmp_path / "grouping_manifest.json"
    write_grouping_manifest(manifest, result, "cpu", {"house_001": {"preview": "group_previews/house_001.png"}}, {})
    assert preview.is_file()
    assert '"group_id": "house_001"' in manifest.read_text(encoding="utf-8")


def test_group_preview_places_a_cropped_mask_using_its_atlas_bounds(tmp_path: Path) -> None:
    mask_path = tmp_path / "cropped-mask.png"
    mask = np.zeros((10, 20), dtype=np.uint8)
    mask[2:8, 4:16] = 255
    Image.fromarray(mask, "L").save(mask_path)
    piece = PieceReference(
        "E001",
        1,
        tmp_path / "element.png",
        mask_path,
        None,
        (2, 3, 20, 10),
        int((mask > 0).sum()),
        "classical",
        mask_bounds=(2, 3, 20, 10),
    )
    pixels = np.zeros((30, 40, 4), dtype=np.uint8)
    pixels[:, :, :3] = 100
    pixels[:, :, 3] = 255
    destination = tmp_path / "cropped-preview.png"
    write_group_preview(destination, LoadedImage(Path("atlas.webp"), pixels, "hash"), [piece])
    preview = np.asarray(Image.open(destination).convert("RGBA"))
    assert preview.shape == (10, 20, 4)
    assert int((preview[:, :, 3] > 0).sum()) == int((mask > 0).sum())


def test_candidate_group_sheet_is_written(tmp_path: Path) -> None:
    candidate = tmp_path / "house_001.png"
    Image.new("RGBA", (20, 20), (255, 0, 0, 255)).save(candidate)
    destination = tmp_path / "candidates.png"
    write_candidate_group_sheet(destination, [("house_001: E001, E002", candidate)])
    assert destination.is_file()
