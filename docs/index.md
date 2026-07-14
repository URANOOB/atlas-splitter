# Atlas Splitter

Convierte un atlas de texturas en piezas editables sin enviar archivos a Internet.

![Objetos separados en Blender](assets/semantic-first-house-separated.png)

Elige un flujo:

| Tienes | Comando | Precisión |
| --- | --- | --- |
| Sólo un atlas | `atlas-splitter split atlas.webp` | Aproximada |
| Atlas y GLB/glTF | `atlas-splitter extract modelo.glb --atlas atlas.webp` | Basada en UV |
| Atlas y nombres deseados | `atlas-splitter semantic atlas.webp` | Inferencia visual |

Empieza con [instalación](getting-started/installation.md). La segmentación 2D no reconstruye geometría; la extracción UV sí conserva las regiones declaradas por el modelo.
