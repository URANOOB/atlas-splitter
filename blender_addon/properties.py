"""Propiedades persistentes del proyecto Atlas Splitter cargado."""

try:
    import bpy
except ImportError:
    CLASSES = ()
else:

    class ATLAS_PG_project(bpy.types.PropertyGroup):
        manifest_path: bpy.props.StringProperty(name="Proyecto", subtype="FILE_PATH")
        atlas_count: bpy.props.IntProperty(name="Atlas", min=0)

    CLASSES = (ATLAS_PG_project,)
