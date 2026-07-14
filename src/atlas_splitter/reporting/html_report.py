"""Reporte HTML autocontenido para resultados de segmentación visual."""

from __future__ import annotations

import base64
import html
import json
from pathlib import Path


def generate_html_report(destination: Path) -> Path:
    """Genera un informe local sin recursos remotos a partir de ``manifest.json``."""
    manifest_path = destination / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or not isinstance(manifest.get("elements"), list):
        raise ValueError("El manifest.json no contiene elementos válidos para el reporte.")
    source_file = manifest.get("source_file")
    if not isinstance(source_file, str):
        raise ValueError("El manifest.json no identifica el atlas fuente.")
    sections: list[str] = []
    for element in manifest["elements"]:
        if not isinstance(element, dict):
            continue
        name, png = element.get("name"), element.get("png")
        if not isinstance(name, str) or not isinstance(png, str):
            continue
        source = html.escape(str(element.get("source", "unknown")))
        sections.append(
            "<article>"
            f"<h3>{html.escape(name)}</h3>"
            f"<img alt='{html.escape(name)}' src='{_data_uri(destination / png)}'>"
            f"<p>Método: segmentación visual aproximada · Origen: {source}</p>"
            f"<p>Confianza: {float(element.get('confidence', 0.0)):.0%}</p>"
            "</article>"
        )
    report = (
        "<!doctype html><html lang='es'><meta charset='utf-8'><title>Atlas Splitter report</title>"
        "<style>body{font-family:system-ui;margin:2rem;background:#181818;color:#eee}img{max-width:220px;"
        "max-height:220px;background:#333}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));"
        "gap:1rem}article{padding:1rem;background:#262626;border-radius:.5rem}"
        "header img{max-width:100%;max-height:420px}"
        "</style><header><h1>Atlas Splitter</h1>"
        "<p>Separación visual aproximada: revisa y corrige las piezas ambiguas.</p>"
        f"<img alt='Atlas original' src='{_data_uri(Path(source_file))}'></header><main>"
        + "".join(sections)
        + "</main></html>"
    )
    report_path = destination / "report" / "index.html"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    return report_path


def _data_uri(path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".")
    media_type = "image/jpeg" if suffix in {"jpg", "jpeg"} else f"image/{suffix}"
    return f"data:{media_type};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"
