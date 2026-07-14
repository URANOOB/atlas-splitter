# Estructura de salida

`split atlas.webp --output resultados` crea un directorio por atlas. Los PNG, máscaras y PSD son resultados base; puedes copiarlos, pero no cambies rutas dentro de `manifest.json`.

```text
resultados/
└── atlas/
    ├── manifest.json
    ├── report/index.html
    ├── png/
    ├── masks/
    ├── psd/
    └── atlas-atlas-splitter.zip
```

`semantic` agrega `semantic_manifest.json`, `review.json`, `grouped/`, `group_previews/`, `objects/`, `uncertain/` y `unassigned/`. Los nombres de grupo son inferencias; abre el reporte y corrige `review.json` antes de ejecutar `apply-review`.

`extract` agrega `uv_manifest.json`, `objects_manifest.json`, `project.json` y `blender/rebuild_scene.py`. Esas salidas proceden de geometría y UV, no de una inferencia visual.

El ZIP se publica al final. Puede vivir dentro o fuera de resultados, pero nunca contiene el propio archivo ZIP ni enlaces simbólicos que salgan del proyecto.
