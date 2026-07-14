"""Revisión manual de piezas visuales sin repetir inferencia."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from atlas_splitter.domain import slugify
from atlas_splitter.exceptions import InvalidReviewError
from atlas_splitter.io.paths import ProjectPathError, resolve_project_path

_GROUP_NAME = re.compile(r"^[a-z0-9][a-z0-9_-]{0,79}$")


def create_review_template(destination: Path) -> Path:
    """Escribe una plantilla editable que cubre todas las piezas como no asignadas."""
    pieces = _pieces(destination)
    review = destination / "review.json"
    if not review.exists():
        data = {"version": 1, "groups": [], "unassigned_piece_ids": list(pieces)}
        review.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return review


def create_semantic_review_template(
    visual_manifest_path: Path, semantic_manifest_path: Path, destination: Path
) -> Path:
    """Convierte una propuesta semántica en una revisión editable completa.

    Esta conversión no toca los manifiestos de entrada. Las propuestas
    rechazadas se dejan sin asignar y las inciertas se conservan con su estado
    para que una persona pueda confirmarlas antes de aplicar la revisión.
    """
    try:
        visual = json.loads(visual_manifest_path.read_text(encoding="utf-8"))
        semantic = json.loads(semantic_manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise InvalidReviewError("No se pudieron leer los manifiestos para la revisión semántica.") from error
    if not isinstance(visual, dict) or not isinstance(visual.get("elements"), list):
        raise InvalidReviewError("El manifiesto visual no contiene elementos válidos.")
    if not isinstance(semantic, dict) or not isinstance(semantic.get("groups"), list):
        raise InvalidReviewError("El manifiesto semántico no contiene grupos válidos.")
    piece_ids = {f"E{index:03d}" for index, _item in enumerate(visual["elements"], start=1)}
    seen: set[str] = set()
    groups: list[dict[str, object]] = []
    unassigned: list[str] = []
    used_names: set[str] = set()
    for raw_group in semantic["groups"]:
        if not isinstance(raw_group, dict):
            raise InvalidReviewError("El manifiesto semántico contiene un grupo inválido.")
        members = raw_group.get("piece_ids")
        status = raw_group.get("status")
        confidence = raw_group.get("confidence")
        if (
            not isinstance(members, list)
            or not all(isinstance(item, str) for item in members)
            or status not in {"accepted", "uncertain", "rejected"}
            or isinstance(confidence, bool)
            or not isinstance(confidence, (int, float))
        ):
            raise InvalidReviewError("El manifiesto semántico contiene datos de grupo inválidos.")
        for piece_id in members:
            if piece_id not in piece_ids or piece_id in seen:
                raise InvalidReviewError(f"ID semántico inexistente o duplicado: {piece_id}")
            seen.add(piece_id)
        if status == "rejected":
            unassigned.extend(members)
            continue
        raw_name = raw_group.get("name")
        base_name = slugify(raw_name if isinstance(raw_name, str) else "grupo", fallback="grupo").replace("-", "_")
        name = base_name
        suffix = 2
        while name in used_names:
            name = f"{base_name}_{suffix}"
            suffix += 1
        used_names.add(name)
        groups.append({"name": name, "piece_ids": members, "confidence": float(confidence), "status": status})
    raw_unassigned = semantic.get("unassigned_piece_ids", [])
    if not isinstance(raw_unassigned, list) or not all(isinstance(item, str) for item in raw_unassigned):
        raise InvalidReviewError("unassigned_piece_ids semántico debe ser una lista de IDs.")
    for piece_id in raw_unassigned:
        if piece_id not in piece_ids or piece_id in seen:
            raise InvalidReviewError(f"ID semántico inexistente o duplicado: {piece_id}")
        seen.add(piece_id)
        unassigned.append(piece_id)
    missing = piece_ids - seen
    if missing:
        raise InvalidReviewError(f"Faltan piezas en el manifiesto semántico: {', '.join(sorted(missing))}")
    review = destination / "review.json"
    review.write_text(
        json.dumps(
            {"version": 1, "source": "semantic", "groups": groups, "unassigned_piece_ids": unassigned},
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return review


def apply_review(review_path: Path) -> Path:
    """Valida y materializa grupos revisados, conservando todos los originales."""
    destination = review_path.parent
    pieces = _pieces(destination)
    try:
        data = json.loads(review_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise InvalidReviewError(f"No se pudo leer review.json: {error}") from error
    if not isinstance(data, dict) or data.get("version") != 1 or not isinstance(data.get("groups"), list):
        raise InvalidReviewError("review.json requiere version: 1 y una lista groups.")
    unassigned = data.get("unassigned_piece_ids", [])
    if not isinstance(unassigned, list) or not all(isinstance(item, str) for item in unassigned):
        raise InvalidReviewError("unassigned_piece_ids debe ser una lista de IDs.")
    seen: set[str] = set()
    for group in data["groups"]:
        name = group.get("name") if isinstance(group, dict) else None
        if not isinstance(name, str) or not _GROUP_NAME.fullmatch(name):
            raise InvalidReviewError("Cada grupo requiere un nombre seguro.")
        identifiers = group.get("piece_ids")
        if not isinstance(identifiers, list) or not all(isinstance(item, str) for item in identifiers):
            raise InvalidReviewError("Cada grupo requiere piece_ids de texto.")
        _validate_ids(identifiers, pieces, seen)
        target = destination / "groups" / name / "pieces"
        target.mkdir(parents=True, exist_ok=True)
        for identifier in identifiers:
            shutil.copy2(pieces[identifier], target / pieces[identifier].name)
    _validate_ids(unassigned, pieces, seen)
    if seen != set(pieces):
        raise InvalidReviewError("La revisión debe cubrir cada pieza exactamente una vez.")
    target = destination / "unassigned"
    target.mkdir(exist_ok=True)
    for identifier in unassigned:
        shutil.copy2(pieces[identifier], target / pieces[identifier].name)
    applied = destination / "review_applied.json"
    applied.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return applied


def _pieces(destination: Path) -> dict[str, Path]:
    try:
        manifest = json.loads((destination / "manifest.json").read_text(encoding="utf-8"))
        elements = manifest["elements"]
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        raise InvalidReviewError("No se encontró un manifest visual válido.") from error
    if not isinstance(elements, list):
        raise InvalidReviewError("El manifest visual no contiene elementos.")
    try:
        return {
            f"E{index:03d}": resolve_project_path(destination, str(item["png"]))
            for index, item in enumerate(elements, start=1)
            if isinstance(item, dict)
        }
    except (KeyError, ProjectPathError) as error:
        raise InvalidReviewError("El manifest visual contiene una ruta de pieza inválida.") from error


def _validate_ids(identifiers: list[str], pieces: dict[str, Path], seen: set[str]) -> None:
    for identifier in identifiers:
        if identifier not in pieces or identifier in seen:
            raise InvalidReviewError(f"ID de pieza inválido o duplicado: {identifier}")
        seen.add(identifier)
