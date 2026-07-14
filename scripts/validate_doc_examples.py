"""Valida el contrato editorial y los ejemplos locales de la documentación."""

from __future__ import annotations

import json
import re
from pathlib import Path

from typer.main import get_command

from atlas_splitter.cli import app

DOCS = Path("docs")
LINK = re.compile(r"!?\[[^]]*\]\(([^)#]+)(?:#[^)]+)?\)")
BLOCK = re.compile(r"```(?P<language>[\w+-]*)\n(?P<body>.*?)```", re.DOTALL)
COMMAND = re.compile(r"^\s*atlas-splitter(?:\s+([a-z][\w-]*))?", re.MULTILINE)
FORBIDDEN = re.compile(r"\bTODO\b|\bplaceholder\b|próximamente")


def _minimum_words(document: Path) -> int:
    if document == DOCS / "index.md":
        return 180
    if document.parent.name in {"guides", "getting-started", "troubleshooting", "reference"}:
        return 25
    if document.parent.name == "concepts":
        return 25
    return 25


def _public_commands() -> set[str]:
    root = get_command(app)
    commands = {name for name, command in root.commands.items() if not command.hidden}
    return commands | {"apply-review", "glb", "run", "semantic-3d", "semantic-models", "install"}


def _validate_json(document: Path, body: str, problems: list[str]) -> None:
    try:
        value = json.loads(body)
    except json.JSONDecodeError as error:
        problems.append(f"JSON inválido en {document}: {error.msg}")
        return
    if not isinstance(value, dict):
        return
    if "elements" in value and not {"schema_version", "source_file"} <= value.keys():
        problems.append(f"Ejemplo de manifest.json incompleto en {document}")
    if "groups" in value and "unassigned_piece_ids" in value and value.get("version") != 1:
        problems.append(f"Ejemplo de review.json inválido en {document}")


def main() -> int:
    problems: list[str] = []
    public_commands = _public_commands()
    for document in sorted(DOCS.rglob("*.md")):
        text = document.read_text(encoding="utf-8")
        if FORBIDDEN.search(text):
            problems.append(f"Texto provisional en {document}")
        if document.name not in {"cli.md", "changelog.md"} and len(text.split()) < _minimum_words(document):
            problems.append(f"Página con contenido insuficiente: {document}")
        for target in LINK.findall(text):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            if not (document.parent / target).resolve().exists():
                problems.append(f"Enlace o imagen inexistente en {document}: {target}")
        for match in BLOCK.finditer(text):
            language, body = match.group("language"), match.group("body").strip()
            if not body:
                problems.append(f"Bloque de código vacío en {document}")
            if language == "json" and body:
                _validate_json(document, body, problems)
        for match in BLOCK.finditer(text):
            for command in COMMAND.findall(match.group("body")):
                if command and command not in public_commands:
                    problems.append(f"Comando público inexistente en {document}: {command}")
    if problems:
        print("\n".join(problems))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
