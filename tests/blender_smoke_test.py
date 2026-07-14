"""Smoke test opcional: ejecutar con ``blender --background --python``."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import bpy
except ImportError:
    import pytest

    pytest.skip("Blender no está disponible en PATH", allow_module_level=True)

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))
import blender_addon  # noqa: E402

blender_addon.register()
assert hasattr(bpy.types.Scene, "atlas_splitter_project")
blender_addon.unregister()
print("Atlas Splitter Blender add-on smoke test: OK")
