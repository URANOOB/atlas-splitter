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
