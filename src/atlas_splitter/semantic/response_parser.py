"""Extracción tolerante de un único objeto JSON desde una respuesta textual."""

from __future__ import annotations

import json
from typing import Any


class SemanticResponseParseError(ValueError):
    """La respuesta no contiene un objeto JSON válido."""


def parse_response_json(response: str) -> dict[str, Any]:
    """Parsea JSON limpio o el primer objeto equilibrado dentro de texto accidental."""
    candidate = response.strip()
    try:
        value = json.loads(candidate)
    except json.JSONDecodeError:
        start = candidate.find("{")
        if start < 0:
            raise SemanticResponseParseError("La respuesta no contiene JSON.") from None
        depth = 0
        in_string = False
        escaped = False
        for index in range(start, len(candidate)):
            char = candidate[index]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
            elif char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    try:
                        value = json.loads(candidate[start : index + 1])
                    except json.JSONDecodeError as error:
                        raise SemanticResponseParseError("El JSON extraído no es válido.") from error
                    break
        else:
            raise SemanticResponseParseError("El objeto JSON está incompleto.") from None
    if not isinstance(value, dict):
        raise SemanticResponseParseError("La respuesta JSON debe ser un objeto.")
    return value
