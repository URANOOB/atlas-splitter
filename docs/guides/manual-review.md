# Revisión manual

Cuando usas la agrupación semántica, o en cualquier momento que generes un archivo de revisión, puedes corregir manualmente los grupos o nombres.

## El archivo `review.json`

Almacena el estado pendiente de tus cambios.

```json
{
  "version": 1,
  "source": "semantic",
  "groups": [
    {
      "name": "walls",
      "piece_ids": ["E001", "E002"],
      "confidence": 0.91,
      "status": "accepted"
    }
  ],
  "unassigned_piece_ids": ["E003"]
}
```

## Cómo modificarlo

* **Renombrar:** Cambia el valor `"name"` a lo que desees.
* **Mover IDs:** Mueve un ID como `"E001"` a otra lista `piece_ids`.
* **Dejar sin asignar:** Mueve el ID a `unassigned_piece_ids`.
* **Evitar duplicados:** Un ID de pieza no puede existir en dos grupos simultáneamente.

## Aplicar revisión

Para previsualizar tu estado actual:
```text
atlas-splitter review resultados/atlas
```

Para aplicar los cambios y regenerar las carpetas de imágenes agrupadas:
```text
atlas-splitter apply-review resultados/atlas/review.json
```
*(Nota: `apply-review` es un comando avanzado para procesar manualmente los archivos de revisión. Los archivos originales en `objects/` siempre se conservan intactos).*
