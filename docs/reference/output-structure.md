# Estructura de salida

Los nombres exactos dependen del atlas y de las opciones activadas. No edites rutas internas de un proyecto visual: `source/` y `manifest.json` deben viajar juntos.

## `split`

```text
resultados/atlas/
├── source/atlas.webp       # conservar
├── manifest.json           # generado
├── png/                    # piezas PNG
├── masks/                  # máscaras PNG
├── psd/                    # si include_psd=true
├── contact_sheet.png       # si hay piezas
└── report/index.html       # regenerable con preview
```

El ZIP predeterminado se crea junto al directorio como `atlas-atlas-splitter.zip`. No lo pongas dentro del mismo árbol que vas a comprimir.

## `semantic` y revisión

Además del resultado visual aparecen `semantic_manifest.json`, `grouping_manifest.json`, `review.json`, `grouped/`, `group_previews/`, `objects/`, `uncertain/` y `unassigned/`. `review.json` es editable; `review_applied.json` aparece después de aplicar una revisión y registra lo aplicado.

## `extract` y add-on

Una extracción geométrica puede producir `uv_manifest.json`; con varios atlas también `objects_manifest.json`, `project.json` y `blender/rebuild_scene.py`. El comando `atlas-splitter blender-addon export --output carpeta` crea `atlas_splitter_blender.zip` en esa carpeta.
