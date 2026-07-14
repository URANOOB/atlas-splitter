# Estructura de salida

Cada ejecución crea una carpeta bajo `--output`; no reemplaza una salida existente.

- `masks/`: máscaras PNG de las regiones.
- `materials/<element_id>/`: recortes PNG por mapa de material (`baseColor`, `normal`, etc.).
- `uv_manifest.json`: procedencia UV, nodos, mallas, materiales y archivos exportados.
- `scene_manifest.json`: índice de escena consumible por herramientas locales.
- `blender/rebuild_scene.py`: script generado para Blender.

Con `glb --atlas-dir` también se crea `objects_manifest.json` y una subcarpeta por atlas. Los IDs son deterministas: volver a procesar la misma escena con las mismas opciones conserva las referencias. Si un grupo `node` o `mesh` usa varios materiales, se mantiene una región por material para no mezclar mapas auxiliares.

Los manifiestos son JSON versionado. No los uses para mover archivos manualmente: conserva las rutas relativas y ejecuta los scripts Blender desde la carpeta de resultados.
