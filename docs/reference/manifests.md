# Referencia de manifiestos

## `manifest.json`
* **Generado por:** `split`, `semantic`
* **Consumido por:** `preview`, visor HTML
* **Versión:** 1
* **Campos principales:** `source_image`, `pieces` (lista de objetos con `id`, `bbox`, `path`)
* **Editable:** No recomendado.
* **Ejemplo:**
```json
{
  "version": 1,
  "source_image": "../atlas.png",
  "pieces": [
    {
      "id": "obj_0000",
      "bbox": [0, 0, 100, 100],
      "path": "objects/obj_0000.png"
    }
  ]
}
```

## `semantic_manifest.json`
* **Generado por:** `semantic`
* **Consumido por:** `group`, visores avanzados
* **Versión:** 1
* **Campos principales:** `groups` (nombres y lista de IDs de piezas asignadas).
* **Editable:** Usa `review.json` mejor.
* **Ejemplo:**
```json
{
  "version": 1,
  "groups": {
    "walls": ["obj_0000"]
  }
}
```

## `grouping_manifest.json`
* **Generado por:** `group-3d`, `group`
* **Consumido por:** `blender-addon`
* **Versión:** 1
* **Editable:** No recomendado.

## `review.json`
* **Generado por:** `semantic`, o comandos de revisión.
* **Consumido por:** `apply-review`
* **Versión:** 1
* **Editable:** Sí.
* **Ejemplo:**
```json
{
  "version": 1,
  "source": "semantic",
  "groups": [
    {
      "name": "walls",
      "piece_ids": ["E001"],
      "confidence": 0.9,
      "status": "accepted"
    }
  ],
  "unassigned_piece_ids": []
}
```

## `review_applied.json`
* **Generado por:** `apply-review`
* Copia del `review.json` una vez sus efectos ya alteraron la carpeta `grouped/`.

## `uv_manifest.json`
* **Generado por:** `extract`
* **Consumido por:** Scripts de reconstrucción.
* Contiene arrays mapeando vértices y UVs.

## `objects_manifest.json`
* **Generado por:** `extract`
* Mapea mallas del GLB a las imágenes `obj_XXX.png`.

## `project.json`
* **Generado por:** `extract`
* **Consumido por:** `blender-addon`
* Punto de entrada principal que enlaza los demás manifiestos.
* **Ejemplo:**
```json
{
  "version": 1,
  "type": "geometry",
  "manifests": {
    "uv": "uv_manifest.json",
    "objects": "objects_manifest.json"
  }
}
```
