import json

from PIL import Image

from atlas_splitter.reporting.html_report import generate_html_report


def test_generate_html_report_is_self_contained(tmp_path) -> None:
    atlas = tmp_path / "atlas.png"
    piece = tmp_path / "png" / "element_001.png"
    piece.parent.mkdir()
    Image.new("RGBA", (4, 4), "red").save(atlas)
    Image.new("RGBA", (2, 2), "blue").save(piece)
    (tmp_path / "manifest.json").write_text(
        json.dumps(
            {
                "source_file": str(atlas),
                "elements": [
                    {"name": "element_001", "png": "png/element_001.png", "source": "classical", "confidence": 0.8}
                ],
            }
        ),
        encoding="utf-8",
    )

    report = generate_html_report(tmp_path)

    content = report.read_text(encoding="utf-8")
    assert report == tmp_path / "report" / "index.html"
    assert "data:image/png;base64," in content
    assert "https://" not in content
