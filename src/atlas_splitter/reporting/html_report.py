"""Reporte HTML autocontenido para resultados de segmentación visual."""

from __future__ import annotations

import base64
import html
import json
from pathlib import Path

from atlas_splitter import __version__
from atlas_splitter.io.paths import ProjectPathError, resolve_project_path, resolve_source_image


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
            f"<img alt='{html.escape(name)}' src='{_data_uri(resolve_project_path(destination, png))}'>"
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
        f"<p>Atlas Splitter {html.escape(__version__)} · separación visual aproximada: "
        "revisa y corrige las piezas ambiguas.</p>"
        f"<img alt='Atlas original' src='{_data_uri(resolve_source_image(destination, manifest))}'></header><main>"
        + "".join(sections)
        + "</main></html>"
    )
    report_path = destination / "report" / "index.html"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    return report_path


def generate_semantic_html_report(destination: Path) -> Path:
    """Genera el reporte local de grupos semánticos, sin afirmar geometría."""
    try:
        visual = json.loads((destination / "manifest.json").read_text(encoding="utf-8"))
        semantic = json.loads((destination / "semantic_manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("No se pudieron leer los manifiestos para el reporte semántico.") from error
    if not isinstance(visual, dict) or not isinstance(semantic, dict):
        raise ValueError("Los manifiestos semánticos deben ser objetos JSON.")
    groups = semantic.get("groups")
    if not isinstance(groups, list):
        raise ValueError("semantic_manifest.json no contiene grupos válidos.")
    elements = visual.get("elements")
    if not isinstance(elements, list):
        raise ValueError("manifest.json no contiene piezas válidas.")
    by_id = {f"E{index:03d}": item for index, item in enumerate(elements, start=1) if isinstance(item, dict)}
    rows: list[str] = []
    for group in groups:
        if not isinstance(group, dict):
            continue
        status = str(group.get("status", "unknown"))
        name = html.escape(str(group.get("name", "sin nombre")))
        confidence = group.get("confidence", 0.0)
        try:
            confidence_text = f"{float(confidence):.0%}"
        except (TypeError, ValueError):
            confidence_text = "sin dato"
        preview = group.get("preview")
        image = ""
        if isinstance(preview, str):
            try:
                data_uri = _data_uri(resolve_project_path(destination, preview))
                image = f"<img alt='Vista previa del grupo {name}' src='{data_uri}'>"
            except (OSError, ProjectPathError):
                image = "<p>Vista previa no disponible.</p>"
        pieces = group.get("piece_ids")
        labels = ", ".join(html.escape(str(piece)) for piece in pieces) if isinstance(pieces, list) else ""
        rows.append(
            f"<article><h3>{name}</h3><p>Estado: {html.escape(status)} · Confianza: {confidence_text}</p>"
            f"{image}<p>Piezas: {labels}</p></article>"
        )
    atlas = ""
    try:
        atlas = f"<img alt='Atlas original' src='{_data_uri(resolve_source_image(destination, visual))}'>"
    except (FileNotFoundError, ProjectPathError):
        atlas = "<p>Atlas original no disponible.</p>"
    unassigned = semantic.get("unassigned_piece_ids", [])
    unassigned_text = ", ".join(html.escape(str(piece)) for piece in unassigned) if isinstance(unassigned, list) else ""
    device = html.escape(str(semantic.get("device", "desconocido")))
    model = html.escape(str(semantic.get("model", "desconocido")))
    style = (
        "body{font-family:system-ui;margin:1rem;background:#181818;color:#f5f5f5;line-height:1.5}"
        "main{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:1rem}"
        "article{background:#262626;padding:1rem;border-radius:.5rem}img{max-width:100%;max-height:300px;"
        "background:#333}a{color:#9ed0ff}"
    )
    summary = (
        f"Atlas Splitter {html.escape(__version__)} · piezas: {len(by_id)} · dispositivo: {device} · modelo: {model}"
    )
    report = (
        "<!doctype html><html lang='es'><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>Atlas Splitter: reporte semántico</title><style>{style}</style>"
        f"<header><h1>Reporte semántico</h1><p>{summary}</p>"
        "<p><strong>Advertencia:</strong> nombres y grupos son inferencias visuales. "
        "Sin GLB no hay geometría ni UV exacta; esto no es reconstrucción 3D.</p>"
        f"{atlas}<p><a href='../review.json'>Abrir review.json para revisión manual</a></p></header>"
        "<section><h2>Piezas sin asignar</h2><p>"
        + (unassigned_text or "Ninguna")
        + "</p></section><main>"
        + "".join(rows)
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
