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
    
    # Excepciones justificadas
    min_lines = 10
    exceptions = ["index.md", "cli.md"]
    
    for document in DOCS.rglob("*.md"):
        text = document.read_text(encoding="utf-8")
        
        # Validar TODOs y placeholders
        if re.search(r"\bTODO\b|próximamente|placeholder", text, re.IGNORECASE):
            problems.append(f"Texto provisional en {document}")
            
        # Validar longitud mínima
        lines = len(text.strip().splitlines())
        if lines < min_lines and document.name not in exceptions:
            problems.append(f"Página con contenido insuficiente ({lines} líneas): {document}")
            
        # Validar bloques de código vacíos
        if "```text\n```" in text or "```json\n```" in text or "```\n```" in text:
            problems.append(f"Bloque de código vacío en {document}")
            
        # Validar enlaces e imágenes
        for target in LINK.findall(text):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            
            target_path = target.split('#')[0]
            if not target_path:
                continue
                
            resolved_path = (document.parent / target_path).resolve()
            if not resolved_path.exists():
                problems.append(f"Enlace roto o recurso inexistente en {document}: {target}")
                
        # Validar JSON
        for block in JSON_BLOCK.findall(text):
            block = block.strip()
            if not block:
                continue
            try:
                data = json.loads(block)
                # Validar manifiestos si parece uno
                if isinstance(data, dict):
                    if "pieces" in data and "version" not in data:
                        problems.append(f"Esquema inválido en ejemplo JSON de {document}")
            except json.JSONDecodeError as error:
                problems.append(f"JSON inválido en {document}: {error.msg}")
                
    if problems:
        print("\n".join(problems))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
