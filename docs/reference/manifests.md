# Referencia de manifiestos

Los manifiestos son JSON locales. Conserva sus rutas relativas y trata los recibidos de terceros como datos no confiables. Los esquemas de `schemas/` describen los contratos de los manifiestos versionados.

| Archivo | Genera | Consume | ¿Editable? |
| --- | --- | --- | --- |
| `manifest.json` | `split` | `preview`, `group`, reporte | No, salvo migración consciente. |
| `semantic_manifest.json` y `grouping_manifest.json` | `semantic` o `group` | reporte y revisión | No recomendado. |
| `review.json` | `review` o flujo semántico | `apply-review` | Sí. |
| `review_applied.json` | `apply-review` | auditoría | No. |
| `uv_manifest.json` | `extract` | scripts Blender | No. |
| `objects_manifest.json`, `project.json` | extracción multiatlas | add-on Blender | No recomendado. |

## Manifest visual

`manifest.json` usa `schema_version`, `tool_version`, `source_file`, `source_file_portable`, dimensiones, parámetros y `elements`. Cada elemento contiene nombre, cuadro `bbox`, área, confianza, origen y rutas relativas `png`, `mask` y opcionalmente `psd`.

```json
{"schema_version":"1.0","source_file":"source/atlas.webp","source_file_portable":true,"elements":[{"name":"element_001","png":"png/element_001.png","mask":"masks/element_001.png"}]}
```

## Revisión manual

```json
{"version":1,"source":"semantic","groups":[{"name":"walls","piece_ids":["E001","E002"],"confidence":0.91,"status":"accepted"}],"unassigned_piece_ids":["E003"]}
```

Incluye cada ID exactamente una vez. Los manifiestos geométricos versionados usan `schema_version: "1.0"`; `project.json` añade versión de herramienta, fecha, archivos fuente y una lista de atlas con el método y confianza de asociación.
