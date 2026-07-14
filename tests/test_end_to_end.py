import json

from PIL import Image, ImageDraw

from atlas_splitter.config import AppConfig
from atlas_splitter.io.zip_writer import write_zip
from atlas_splitter.pipeline import process_image
from atlas_splitter.semantic.fake_backend import FakeSemanticGroupingBackend
from atlas_splitter.semantic.grouping_service import group_extracted_atlas
from atlas_splitter.semantic.types import GroupingResult, SemanticGroup


def test_lossy_webp_end_to_end_creates_all_artifacts(tmp_path) -> None:
    source = tmp_path / "lossy.webp"
    image = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((40, 40, 220, 220), fill=(230, 50, 20, 255))
    draw.ellipse((290, 260, 470, 440), fill=(20, 120, 230, 255))
    image.save(source, "WEBP", lossless=False, quality=85)
    config = AppConfig.model_validate({"segmentation": {"min_area": 100}})
    result = process_image(source, tmp_path / "results", config)
    manifest = json.loads((result / "manifest.json").read_text(encoding="utf-8"))
    archive = tmp_path / "results.zip"
    write_zip(archive, [result])
    assert manifest["final_elements"] >= 2
    assert (result / "contact_sheet.png").is_file()
    assert (result / "psd" / "element_001.psd").is_file()
    assert archive.is_file()


def test_extracted_atlas_groups_with_a_deterministic_fake_backend(tmp_path) -> None:
    source = tmp_path / "atlas.webp"
    image = Image.new("RGBA", (48, 24), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((2, 2, 18, 20), fill=(255, 0, 0, 255))
    draw.rectangle((29, 2, 45, 20), fill=(0, 255, 0, 255))
    image.save(source, "WEBP", lossless=True)
    config = AppConfig.model_validate(
        {"segmentation": {"min_area": 20}, "grouping": {"enabled": True, "device": "cpu"}}
    )
    destination = process_image(source, tmp_path / "results", config)
    backend = FakeSemanticGroupingBackend(
        GroupingResult(
            [SemanticGroup("objects_001", "objects", "objects", ["E001", "E002"], 0.9, "accepted")],
            [],
            "fake",
            "deterministic",
            0.0,
        )
    )

    result = group_extracted_atlas(destination, config.grouping, backend)

    manifest = json.loads((destination / "semantic_manifest.json").read_text(encoding="utf-8"))
    assert result.groups[0].group_id == "objects_001"
    assert manifest["backend"] == "fake"
    assert (destination / "objects" / "objects_001" / "element_001.png").is_file()
    assert (destination / "grouped" / "objects_001.psd").is_file()
    assert not (destination / "semantic_inputs").exists()
