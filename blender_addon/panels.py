"""Panel lateral del add-on."""

try:
    import bpy
except ImportError:
    CLASSES = ()
else:
    class ATLAS_PT_panel(bpy.types.Panel):
        bl_label = "Atlas Splitter"
        bl_idname = "ATLAS_PT_panel"
        bl_space_type = "VIEW_3D"
        bl_region_type = "UI"
        bl_category = "Atlas"

        def draw(self, context):
            layout = self.layout
            layout.operator("atlas_splitter.load_project", icon="FILE_FOLDER")
            path = context.scene.get("atlas_splitter_project")
            if path:
                layout.label(text=path)
                layout.label(text=f"Atlas: {context.scene.get('atlas_splitter_atlas_count', 0)}")

    CLASSES = (ATLAS_PT_panel,)
