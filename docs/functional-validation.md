# Validación funcional final

Fecha: 2026-07-13.

Se inspeccionaron las asociaciones material/imágenes declaradas localmente antes
de invocar `atlas-splitter glb` con una textura externa:

| GLB | Imágenes declaradas | Comparación RGBA con `Samples/day/*.webp` |
| --- | --- | --- |
| `GLB/gobos.glb` | imagen 0, 4096×4096 | ninguna coincidencia |
| `GLB/Hitboxes.glb` | ninguna | no aplicable |
| `GLB/Room.glb` | ninguna | no aplicable |

La comparación usa las dimensiones y el hash SHA-256 de los píxeles RGBA, no
el nombre de archivo. Por ello no hay una pareja GLB + textura de
`Samples/day` que pueda asociarse de forma fiable. No se ejecutó la exportación
funcional solicitada ni se fabricaron salidas; el comando rechazaría esa
asociación externa con un diagnóstico específico.
