"""Add-on mínimo de Atlas Splitter para Blender 4.x."""

_PACKAGE_VERSION = "__ATLAS_SPLITTER_VERSION__"


def _version_tuple(value: str) -> tuple[int, int, int]:
    """Convierte la versión del paquete al formato requerido por Blender."""
    if value == "__ATLAS_SPLITTER_VERSION__":
        return (0, 0, 0)
    parts = value.split(".")[:3]
    return tuple(int(part) for part in parts) + (0,) * (3 - len(parts))

bl_info = {
    "name": "Atlas Splitter",
    "author": "Atlas Splitter contributors",
    "version": _version_tuple(_PACKAGE_VERSION),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Atlas Splitter",
    "description": "Carga manifiestos locales de Atlas Splitter",
    "category": "Import-Export",
}

try:
    from .operators import CLASSES as OPERATOR_CLASSES
    from .panels import CLASSES as PANEL_CLASSES
    from .properties import CLASSES as PROPERTY_CLASSES
    from .properties import ATLAS_PG_project
except ImportError:  # Permite inspección y pruebas sin Blender.
    OPERATOR_CLASSES = ()
    PANEL_CLASSES = ()
    PROPERTY_CLASSES = ()
    ATLAS_PG_project = None

CLASSES = (*PROPERTY_CLASSES, *OPERATOR_CLASSES, *PANEL_CLASSES)


def register() -> None:
    import bpy

    assert ATLAS_PG_project is not None
    for item in CLASSES:
        bpy.utils.register_class(item)
    bpy.types.Scene.atlas_splitter_project = bpy.props.PointerProperty(type=ATLAS_PG_project)


def unregister() -> None:
    import bpy

    del bpy.types.Scene.atlas_splitter_project
    for item in reversed(CLASSES):
        bpy.utils.unregister_class(item)
