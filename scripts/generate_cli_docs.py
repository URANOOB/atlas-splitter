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
    
    # Extraer y ordenar parámetros para separar requeridos de opcionales
    args = [p for p in command.params if isinstance(p, click.Argument)]
    opts = [p for p in command.params if isinstance(p, click.Option) and not p.hidden]
    
    # Procesar argumentos (siempre requeridos a menos que tengan default, pero typer no suele)
    for p in args:
        rows.append(f"| `{p.human_readable_name}` | requerido | — | argumento |")
        
    # Procesar opciones
    for p in opts:
        # Extraer opciones primarias y secundarias
        opt_names = sorted(p.opts, key=lambda x: len(x), reverse=True)
        primary = f"`{opt_names[0]}`"
        secondary = f"`{', '.join(opt_names[1:])}`" if len(opt_names) > 1 else "—"
        
        req_str = "requerido" if p.required else "opcional"
        default = str(p.default) if p.default not in (None, (), False, "") else "—"
        
        rows.append(f"| {primary} | {req_str} | `{default}` | {p.help or '—'} |")
        if secondary != "—":
            rows.append(f"| {secondary} | {req_str} | `{default}` | Alias de {primary} |")
            
    return rows


def _render_command(command: click.Command, path: tuple[str, ...]) -> list[str]:
    title = " ".join(("atlas-splitter", *path))
    lines = [f"## `{title}`", "", command.help or "Sin descripción.", "", "```text", _usage(command, path), "```", ""]
    rows = _option_rows(command)
    if rows:
        lines.extend(["| Opción o argumento | Estado | Predeterminado | Descripción |", "| --- | --- | --- | --- |", *rows, ""])
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
    hidden_commands = []
    
    for name, command in commands.items():
        if command.hidden:
            hidden_commands.append((name, command))
            continue
        lines.extend(_render_command(command, (name,)))
        if isinstance(command, click.Group):
            for child_name, child in command.commands.items():
                if child.hidden:
                    hidden_commands.append((f"{name} {child_name}", child))
                    continue
                lines.extend(_render_command(child, (name, child_name)))
                
    if hidden_commands:
        lines.extend([
            "## Alias de compatibilidad (Ocultos)",
            "",
            "Estos comandos existen por razones de compatibilidad con versiones anteriores, pero no deben utilizarse en nuevos flujos de trabajo.",
            ""
        ])
        for name, cmd in hidden_commands:
            lines.extend(_render_command(cmd, tuple(name.split())))

    lines.extend([
        "## Códigos de salida conocidos",
        "",
        "La CLI devuelve los siguientes códigos de salida al sistema operativo:",
        "",
        "* `0`: Éxito.",
        "* `1`: Error genérico o excepción no controlada.",
        "* `2`: Error de sintaxis en los argumentos de la CLI (generado por Click/Typer).",
        "* `E001` - `E100`: Revisa la [referencia de códigos de error](error-codes.md).",
        ""
    ])
            
    return "\\n".join(lines)


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
