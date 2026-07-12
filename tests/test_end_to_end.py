import json

from PIL import Image, ImageDraw

from atlas_splitter.config import AppConfig
from atlas_splitter.io.zip_writer import write_zip
from atlas_splitter.pipeline import process_image


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
