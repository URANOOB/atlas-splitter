import importlib.util
from pathlib import Path


def test_blender_addon_can_be_inspected_without_blender() -> None:
    root = Path(__file__).parents[1] / "blender_addon"
    spec = importlib.util.spec_from_file_location(
        "atlas_addon", root / "__init__.py", submodule_search_locations=[str(root)]
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.bl_info["blender"] == (4, 0, 0)
