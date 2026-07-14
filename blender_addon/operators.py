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

    CLASSES = (ATLAS_OT_load_project,)
