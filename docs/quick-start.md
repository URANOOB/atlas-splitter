# Inicio rápido

Atlas Splitter procesa los archivos localmente. No sube tu atlas ni descarga modelos durante `run` o `glb`.

```text
atlas-splitter doctor
atlas-splitter atlas.webp resultados
```

Si cuentas con un modelo, la extracción UV es exacta para la geometría incluida:

```text
atlas-splitter glb modelo.glb --atlas atlas.webp --output resultados --group-by uv-island
```

Abre `resultados/blender/rebuild_scene.py` desde Blender para reconstruir materiales editables.
