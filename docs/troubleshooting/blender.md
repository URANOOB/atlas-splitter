# Problemas de Blender

## Síntoma

Blender no encuentra el add-on, no carga un manifiesto o no crea colecciones.

## Causa probable

Se eligió una carpeta en vez del ZIP, falta `rebuild_scene.py` o el manifiesto tiene versión desconocida.

## Comprobación

```text
atlas-splitter blender-addon info
atlas-splitter blender-addon export --output Descargas
```

## Solución

En Blender 4.x usa Preferences → Add-ons → Install y selecciona `atlas_splitter_blender.zip`. Actívalo y carga `project.json`, `objects_manifest.json` o `manifest.json`. El panel rechaza JSON corrupto y versiones incompatibles.

## Código y siguiente paso

Mira la consola de Blender para el error completo. Regenera `extract` si falta el script de reconstrucción.
