"""Operadores de lectura local para el add-on."""

import json
from pathlib import Path

try:
    import bpy
except ImportError:
    CLASSES = ()
else:
    class ATLAS_OT_load_project(bpy.types.Operator):
        bl_idname = "atlas_splitter.load_project"
        bl_label = "Cargar proyecto Atlas Splitter"

        filepath: bpy.props.StringProperty(subtype="FILE_PATH")

        def execute(self, context):
            try:
                data = json.loads(Path(self.filepath).read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                self.report({"ERROR"}, f"No se pudo leer el manifiesto: {error}")
                return {"CANCELLED"}
            context.scene["atlas_splitter_project"] = self.filepath
            context.scene["atlas_splitter_atlas_count"] = len(data.get("atlases", []))
            self.report({"INFO"}, "Proyecto Atlas Splitter cargado")
            return {"FINISHED"}

    class ATLAS_OT_create_review_collections(bpy.types.Operator):
        bl_idname = "atlas_splitter.create_review_collections"
        bl_label = "Crear colecciones de revisión"

        def execute(self, context):
            project = context.scene.get("atlas_splitter_project")
            if not project:
                self.report({"ERROR"}, "Carga primero un project.json")
                return {"CANCELLED"}
            groups = Path(project).parent / "groups"
            if not groups.is_dir():
                self.report({"WARNING"}, "No hay grupos de revisión aplicados")
                return {"CANCELLED"}
            root = bpy.data.collections.get("Atlas Splitter")
            if root is None:
                root = bpy.data.collections.new("Atlas Splitter")
                context.scene.collection.children.link(root)
            for group in sorted(path for path in groups.iterdir() if path.is_dir()):
                if root.children.get(group.name) is None:
                    root.children.link(bpy.data.collections.new(group.name))
            self.report({"INFO"}, "Colecciones de revisión creadas")
            return {"FINISHED"}

    CLASSES = (ATLAS_OT_load_project, ATLAS_OT_create_review_collections)
