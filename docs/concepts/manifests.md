# Manifiestos

Un manifiesto es un JSON que describe una salida sin guardar la imagen dentro del propio JSON. `manifest.json` enumera piezas, máscaras y el atlas copiado en `source/`.

Los manifiestos semánticos registran propuestas; `review.json` es el archivo diseñado para que una persona cambie grupos. Los manifiestos UV y de proyecto conservan evidencia de la asociación con un GLB.

No cambies rutas de PNG o máscaras a mano: pueden dejar de estar confinadas al proyecto. Mueve el directorio completo y usa `preview` para regenerar el reporte.

La [referencia de manifiestos](../reference/manifests.md) detalla quién genera y consume cada archivo.
