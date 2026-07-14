"""Chequeos locales baratos para documentación, enlaces y bloques JSON."""

from __future__ import annotations

import json
import re
from pathlib import Path

DOCS = Path("docs")
LINK = re.compile(r"\[[^]]+\]\(([^)#]+)(?:#[^)]+)?\)")
JSON_BLOCK = re.compile(r"```json\s*\n(.*?)```", re.DOTALL)


def main() -> int:
    problems: list[str] = []
    for document in DOCS.rglob("*.md"):
        text = document.read_text(encoding="utf-8")
        if re.search(r"\bTODO\b|próximamente|placeholder", text, re.IGNORECASE):
            problems.append(f"Texto provisional: {document}")
        if len(text.strip().splitlines()) < 4:
            problems.append(f"Página casi vacía: {document}")
        for target in LINK.findall(text):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            if not (document.parent / target).resolve().is_file():
                problems.append(f"Enlace interno inexistente en {document}: {target}")
        for block in JSON_BLOCK.findall(text):
            try:
                json.loads(block)
            except json.JSONDecodeError as error:
                problems.append(f"JSON inválido en {document}: {error.msg}")
    if problems:
        print("\n".join(problems))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
