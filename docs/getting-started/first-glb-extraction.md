# Primera extracción GLB

## Requisitos

Un GLB/glTF local y, cuando no esté embebido, su atlas. Instala Geometry una vez.

```text
atlas-splitter setup geometry
atlas-splitter extract modelo.glb --atlas atlas.webp --output resultados
```

Se genera un manifiesto UV y un script para Blender. Si falta Geometry, el comando muestra `atlas-splitter setup geometry`; no descarga nada durante la extracción.
