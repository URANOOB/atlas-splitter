"""Genera la referencia CLI desde los comandos Click reales."""

from __future__ import annotations

import argparse
from pathlib import Path

import click
from typer.main import get_command

from atlas_splitter.cli import app

DESTINATION = Path("docs/reference/cli.md")


def _usage(command: click.Command, path: tuple[str, ...]) -> str:
    context = click.Context(command, info_name="atlas-splitter")
    usage = command.get_usage(context).removeprefix("Usage: ").strip()
    suffix = usage.removeprefix("atlas-splitter").strip()
    return " ".join(("atlas-splitter", *path, suffix))


def _option_rows(command: click.Command) -> list[str]:
    rows: list[str] = []
    for parameter in command.params:
        if isinstance(parameter, click.Option) and not parameter.hidden:
            names = ", ".join(parameter.opts)
            default = str(parameter.default) if parameter.default not in (None, (), False) else "—"
            rows.append(f"| `{names}` | `{default}` | {parameter.help or '—'} |")
        elif isinstance(parameter, click.Argument):
            rows.append(f"| `{parameter.human_readable_name}` | requerido | argumento |")
    return rows


def _render_command(command: click.Command, path: tuple[str, ...]) -> list[str]:
    title = " ".join(("atlas-splitter", *path))
    lines = [f"## `{title}`", "", command.help or "Sin descripción.", "", "```text", _usage(command, path), "```", ""]
    rows = _option_rows(command)
    if rows:
        lines.extend(["| Opción o argumento | Predeterminado | Descripción |", "| --- | --- | --- |", *rows, ""])
    return lines


def render() -> str:
    root = get_command(app)
    lines = [
        "# Referencia CLI",
        "",
        "Este archivo se genera con `python scripts/generate_cli_docs.py`. No edites esta lista a mano.",
        "",
        "La CLI no descarga modelos durante `split`, `semantic`, `extract` ni la generación de documentación.",
        "",
    ]
    commands = getattr(root, "commands", {})
    for name, command in commands.items():
        if command.hidden:
            continue
        lines.extend(_render_command(command, (name,)))
        if isinstance(command, click.Group):
            for child_name, child in command.commands.items():
                if not child.hidden:
                    lines.extend(_render_command(child, (name, child_name)))
    lines.extend(
        [
            "## Alias de compatibilidad",
            "",
            "`run`, `glb`, `install`, `semantic-3d` y `semantic-models` son alias ocultos y deprecados. "
            "Usa `split`, `extract`, `setup`, `group-3d` y `models`.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Falla si el archivo no coincide con la CLI")
    arguments = parser.parse_args()
    content = render()
    if arguments.check:
        if not DESTINATION.is_file() or DESTINATION.read_text(encoding="utf-8") != content:
            print("docs/reference/cli.md no coincide con la CLI. Ejecuta python scripts/generate_cli_docs.py")
            return 1
        return 0
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    DESTINATION.write_text(content, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
