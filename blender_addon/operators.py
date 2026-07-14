"""Operadores locales del add-on para Blender 4.x."""

from pathlib import Path

try:
    import bpy
    from bpy_extras.io_utils import ImportHelper
except ImportError:
    CLASSES = ()
else:
    from .manifest import collection_name, load_manifest

    class ATLAS_OT_load_project(bpy.types.Operator, ImportHelper):
        bl_idname = "atlas_splitter.load_project"
        bl_label = "Cargar proyecto"
        filename_ext = ".json"
        filter_glob: bpy.props.StringProperty(
            default="project.json;manifest.json;objects_manifest.json", options={"HIDDEN"}
        )

        def execute(self, context):
            try:
                path, data = load_manifest(self.filepath)
            except ValueError as error:
                self.report({"ERROR"}, str(error))
                return {"CANCELLED"}
            project = context.scene.atlas_splitter_project
            project.manifest_path = str(path)
            project.atlas_count = len(data.get("atlases", data.get("objects", data.get("elements", []))))
            self.report({"INFO"}, "Proyecto Atlas Splitter cargado")
            return {"FINISHED"}

    class ATLAS_OT_create_review_collections(bpy.types.Operator):
        bl_idname = "atlas_splitter.create_review_collections"
        bl_label = "Crear colecciones"

        def execute(self, context):
            project = context.scene.atlas_splitter_project.manifest_path
            if not project:
                self.report({"ERROR"}, "Carga primero un manifiesto Atlas Splitter")
                return {"CANCELLED"}
            groups = Path(project).parent / "groups"
            if not groups.is_dir():
                self.report({"WARNING"}, "No hay grupos de revisión aplicados")
                return {"CANCELLED"}
            root = bpy.data.collections.get("Atlas Splitter")
            if root is None:
                root = bpy.data.collections.new("Atlas Splitter")
                context.scene.collection.children.link(root)
            existing = {item.name for item in root.children}
            for group in sorted(path for path in groups.iterdir() if path.is_dir()):
                name = collection_name(group.name)
                if name in existing:
                    continue
                root.children.link(bpy.data.collections.new(name))
                existing.add(name)
            self.report({"INFO"}, "Colecciones de revisión creadas")
            return {"FINISHED"}

    class ATLAS_OT_rebuild_objects(bpy.types.Operator):
        bl_idname = "atlas_splitter.rebuild_objects"
        bl_label = "Reconstruir objetos"

        def execute(self, context):
            project = context.scene.atlas_splitter_project.manifest_path
            if not project:
                self.report({"ERROR"}, "Carga primero un manifiesto Atlas Splitter")
                return {"CANCELLED"}
            root = Path(project).parent
            candidates = [root / "blender" / "rebuild_scene.py", root / "rebuild_scene.py"]
            script = next((item for item in candidates if item.is_file()), None)
            if script is None:
                self.report({"ERROR"}, "No se encontró un script de reconstrucción generado.")
                return {"CANCELLED"}
            try:
                bpy.ops.script.python_file_run(filepath=str(script))
            except RuntimeError as error:
                self.report({"ERROR"}, f"No se pudo reconstruir: {error}")
                return {"CANCELLED"}
            self.report({"INFO"}, "Reconstrucción terminada")
            return {"FINISHED"}

    CLASSES = (ATLAS_OT_load_project, ATLAS_OT_create_review_collections, ATLAS_OT_rebuild_objects)
