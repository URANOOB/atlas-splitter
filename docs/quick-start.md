# Inicio rápido

Atlas Splitter procesa los archivos localmente. No sube tu atlas ni descarga modelos durante `run`, `glb` o `semantic-3d`.

```text
atlas-splitter doctor
atlas-splitter atlas.webp resultados
```

También puedes ejecutar `atlas-splitter` sin argumentos: el asistente valida rutas, muestra un resumen y enseña el comando equivalente. Elige **doctor** para revisar el equipo o **modelos locales** para comprobar checkpoints sin descargarlos.

Si cuentas con un modelo, la extracción UV es exacta para la geometría incluida:

```text
atlas-splitter glb modelo.glb --atlas atlas.webp --output resultados --group-by uv-island
```

Abre `resultados/blender/rebuild_scene.py` desde Blender para reconstruir materiales editables.

Consulta [estructura de salida](output-structure.md), [flujo Blender](blender-workflow.md) y [problemas frecuentes](troubleshooting.md).
