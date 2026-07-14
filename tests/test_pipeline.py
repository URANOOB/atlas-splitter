import json

from PIL import Image

from atlas_splitter.config import AppConfig
from atlas_splitter.io.image_loader import ImageLoadError, discover_images, load_image
from atlas_splitter.pipeline import process_image


def test_pipeline_writes_png_masks_and_manifest(tmp_path) -> None:
    image_path = tmp_path / "atlas.webp"
    image = Image.new("RGBA", (40, 30), (0, 0, 0, 0))
    image.paste((255, 0, 0, 255), (2, 2, 14, 14))
    image.paste((0, 255, 0, 255), (22, 10, 36, 24))
    image.save(image_path, "WEBP", lossless=True)
    config = AppConfig.model_validate({"segmentation": {"min_area": 20}})
    destination = process_image(image_path, tmp_path / "results", config)
    manifest = json.loads((destination / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "1.0"
    assert manifest["capabilities"]["reconstruction_quality"] == "approximate_2d_only"
    assert manifest["final_elements"] == 2
    assert (destination / "png" / "element_001.png").is_file()
    assert (destination / "masks" / "element_002.png").is_file()
    assert (destination / "psd" / "element_001.psd").is_file()
    assert (destination / "contact_sheet.png").is_file()


def test_discovery_ignores_non_webp_and_loader_rejects_corruption(tmp_path) -> None:
    (tmp_path / "notes.txt").write_text("not an image", encoding="utf-8")
    broken = tmp_path / "broken.webp"
    broken.write_bytes(b"bad")
    assert discover_images(tmp_path) == [broken]
    try:
        load_image(broken)
    except ImageLoadError:
        pass
    else:
        raise AssertionError("Se esperaba ImageLoadError")
