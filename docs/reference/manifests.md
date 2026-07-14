# Manifiestos

Los manifiestos son JSON locales. No edites `manifest.json` ni `semantic_manifest.json` mientras una ejecución está activa. Las rutas de piezas son relativas al directorio de resultado y no pueden usar rutas absolutas ni `..`.

| Archivo | Productor | Consumidor | Uso |
| --- | --- | --- | --- |
| `manifest.json` | `split` | reporte, `review`, `semantic` | piezas visuales aproximadas |
| `semantic_manifest.json` | `semantic` o `group` | reporte y revisión | grupos inferidos y confianza |
| `review.json` | `review` o `semantic` | `apply-review` | cambios humanos editables |
| `review_applied.json` | `apply-review` | auditoría | revisión materializada |
| `uv_manifest.json` | `extract` | Blender | regiones obtenidas por UV |
| `objects_manifest.json` | `extract` | Blender | objetos y partes UV |
| `project.json` | `extract` | Blender | proyecto multi-atlas |

Los manifiestos geométricos usan `schema_version: "1.0"`. `manifest.json` visual también declara `tool_version` y capacidades: una salida visual tiene `geometry_available: false`; no sirve para reconstruir una malla.

`review.json` conserva `version: 1`, `groups` y `unassigned_piece_ids`. Cada `piece_id` debe salir exactamente una vez. `accepted` e `uncertain` quedan en grupos; piezas rechazadas quedan sin asignar.

Los esquemas JSON de referencia viven en `schemas/`. Cuando subas una versión de esquema, conserva lectores de la anterior o añade una migración explícita.
