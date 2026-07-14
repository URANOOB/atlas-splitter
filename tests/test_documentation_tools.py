"""La documentación publicada debe coincidir con la CLI y sus recursos locales."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_documentation_tools_accept_the_repository() -> None:
    for script, arguments in (
        ("scripts/generate_cli_docs.py", ["--check"]),
        ("scripts/validate_doc_examples.py", []),
    ):
        subprocess.run([sys.executable, script, *arguments], cwd=ROOT, check=True)
