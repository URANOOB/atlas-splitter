# Primera extracción GLB

Usa este flujo sólo cuando tengas un GLB o glTF y el atlas que usa. Instala la capacidad de geometría, inspecciona el archivo y después extrae las regiones.

```text
atlas-splitter setup geometry
atlas-splitter inspect modelo.glb
atlas-splitter extract modelo.glb --atlas textura.webp --output resultados
```

El comando no modifica `modelo.glb`. Según el caso crea `uv_manifest.json` y, para asociaciones múltiples, `objects_manifest.json`, `project.json` y scripts de Blender.

Si falta UV o la asociación del atlas es ambigua, revisa la [guía GLB y UV](../guides/glb-uv-extraction.md). No sustituyas un atlas externo sin confirmar que corresponde al material del modelo.
