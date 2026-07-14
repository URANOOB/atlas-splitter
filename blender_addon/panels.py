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
            layout.operator("atlas_splitter.create_review_collections", icon="OUTLINER_COLLECTION")
            layout.operator("atlas_splitter.rebuild_objects", icon="FILE_REFRESH")
            project = context.scene.atlas_splitter_project
            path = project.manifest_path
            if path:
                layout.label(text=path)
                layout.label(text=f"Atlas: {project.atlas_count}")

    CLASSES = (ATLAS_PT_panel,)
