"""Add-on mínimo de Atlas Splitter para Blender 4.x."""

bl_info = {
    "name": "Atlas Splitter",
    "author": "Atlas Splitter contributors",
    "version": (0, 1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Atlas Splitter",
    "description": "Carga manifiestos locales de Atlas Splitter",
    "category": "Import-Export",
}

try:
    from .operators import CLASSES as OPERATOR_CLASSES
    from .panels import CLASSES as PANEL_CLASSES
except ImportError:  # Permite inspección y pruebas sin Blender.
    OPERATOR_CLASSES = ()
    PANEL_CLASSES = ()

CLASSES = (*OPERATOR_CLASSES, *PANEL_CLASSES)


def register() -> None:
    import bpy

    for item in CLASSES:
        bpy.utils.register_class(item)


def unregister() -> None:
    import bpy

    for item in reversed(CLASSES):
        bpy.utils.unregister_class(item)
