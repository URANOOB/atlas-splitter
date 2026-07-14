# Extracción GLB y UV

Cuando tienes la geometría 3D, puedes hacer recortes precisos basados en los mapas UV en lugar de adivinar mediante píxeles transparentes.

## Conceptos clave
* **GLB/glTF:** Formatos de modelos 3D que contienen la malla.
* **Materiales y Texturas:** Definen el aspecto de la malla.
* **Atlas:** Imagen grande que contiene las texturas de todos los objetos.
* **Coordenadas UV:** Sistema (`TEXCOORD_0`) que dice qué parte de la imagen 2D va en qué parte del modelo 3D.
* **Múltiples atlas / Atlas externos / Embebidos:** Un GLB puede tener la imagen dentro del archivo (embebido) o apuntar a un archivo externo.
* **Asociaciones ambiguas:** A veces varias mallas comparten UV. `extract` lo detecta.
* **flip-v:** A veces las coordenadas Y (o V) están invertidas.
* **Draco:** Compresión de geometría. Debes descomprimir tu GLB si usas compresión Draco, pues `atlas-splitter` requiere acceso a las UV en crudo.

## Comandos

Primero, inspecciona tu modelo para asegurarte de que contiene texturas válidas:
```text
atlas-splitter inspect modelo.glb
```

Luego, extrae las regiones basándote en la imagen y el archivo 3D:
```text
atlas-splitter extract modelo.glb --atlas atlas.webp --output resultados
```

*Nota: `extract` no modifica tu GLB original.*

## Salida real

En tu carpeta `resultados` verás:
```text
uv_manifest.json
objects_manifest.json
project.json
blender/rebuild_scene.py
```
Estos archivos mantienen la relación matemática entre las imágenes cortadas y la malla 3D.
