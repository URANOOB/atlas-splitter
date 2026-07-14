# Estructura de salida

## `split`
```text
resultados/
├── manifest.json        (Generado)
├── report/              (Temporales/Regenerables)
│   └── index.html
└── objects/             (Permanentes)
    ├── obj_000.png
    └── obj_001.png
```

## `semantic`
Añade a lo anterior:
```text
├── semantic_manifest.json (Generado)
├── review.json            (Editable)
└── grouped/               (Generados/Regenerables)
    ├── walls/
    │   └── obj_000.png
    └── uncertain/
```

## `extract`
```text
resultados/
├── uv_manifest.json       (Generado)
├── objects_manifest.json  (Generado)
├── project.json           (Raíz de Blender, Permanente)
└── blender/               (Generado)
    └── rebuild_scene.py
```

## Revisión aplicada
Si ejecutas `apply-review`, aparecerá:
```text
├── review_applied.json    (Registro, no editable)
```
Y la carpeta `grouped/` será regenerada con tus cambios manuales.

## Add-on exportado
Al usar `blender-addon export --output .` obtienes:
```text
└── atlas_splitter_blender.zip
```
