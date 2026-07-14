"""Revisión manual de piezas visuales sin repetir inferencia."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from atlas_splitter.exceptions import InvalidReviewError

_GROUP_NAME = re.compile(r"^[a-z0-9][a-z0-9_-]{0,79}$")


def create_review_template(destination: Path) -> Path:
    """Escribe una plantilla editable que cubre todas las piezas como no asignadas."""
    pieces = _pieces(destination)
    review = destination / "review.json"
    if not review.exists():
        data = {"version": 1, "groups": [], "unassigned_piece_ids": list(pieces)}
        review.write_text(json.dumps(data, indent=2), encoding="utf-8")
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
    return {
        f"E{index:03d}": destination / str(item["png"])
        for index, item in enumerate(elements, start=1)
        if isinstance(item, dict)
    }


def _validate_ids(identifiers: list[str], pieces: dict[str, Path], seen: set[str]) -> None:
    for identifier in identifiers:
        if identifier not in pieces or identifier in seen:
            raise InvalidReviewError(f"ID de pieza inválido o duplicado: {identifier}")
        seen.add(identifier)
