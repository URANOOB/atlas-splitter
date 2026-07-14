# Revisión manual

`atlas-splitter review resultados/atlas` crea `review.json` si todavía no existe. Edita sólo ese archivo para decidir qué piezas pertenecen a cada grupo.

```json
{"version":1,"source":"semantic","groups":[{"name":"walls","piece_ids":["E001","E002"],"confidence":0.91,"status":"accepted"}],"unassigned_piece_ids":["E003"]}
```

Los nombres usan letras minúsculas, números, guiones o guiones bajos. Mueve un ID entre `groups` y `unassigned_piece_ids` para reclasificarlo. Cada ID debe aparecer exactamente una vez; no dupliques ni elimines piezas. La confianza y el estado son útiles para registrar la decisión, no para ejecutar una inferencia nueva.

```text
atlas-splitter apply-review resultados/atlas/review.json
```

`apply-review` continúa oculto como herramienta avanzada de compatibilidad. Copia las piezas a `groups/` o `unassigned/`, conserva los PNG y máscaras originales y escribe `review_applied.json`.
