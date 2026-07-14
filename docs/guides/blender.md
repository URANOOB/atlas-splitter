# Blender

El add-on funciona con Blender 4.x y sólo carga manifiestos locales. Exporta el ZIP desde la misma versión de Atlas Splitter que creó el proyecto.

```text
atlas-splitter blender-addon export --output Descargas
```

En Blender abre **Edit > Preferences > Add-ons > Install…**, elige `atlas_splitter_blender.zip` y activa **Atlas Splitter**. En la Vista 3D pulsa **N** y abre la pestaña **Atlas**; allí aparecen los botones *Cargar proyecto*, *Crear colecciones* y *Reconstruir objetos*.

*Cargar proyecto* acepta `project.json`, `objects_manifest.json` o `manifest.json`. Para una extracción con geometría, `project.json` es el punto de entrada más completo. *Crear colecciones* necesita una revisión aplicada que haya creado `groups/`. *Reconstruir objetos* ejecuta el script generado `blender/rebuild_scene.py` cuando existe.

No hay capturas verificadas del panel en este repositorio. Para evitar documentar una interfaz inventada, esta guía describe únicamente los controles implementados; consulta la consola de Blender para mensajes de error. Para desinstalarlo, desactívalo o elimínalo desde Preferences.

El add-on no descarga modelos ni envía archivos. Conserva los manifiestos y los directorios referenciados juntos al mover un proyecto.
