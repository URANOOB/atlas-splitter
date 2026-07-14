# Flujo con Blender

1. Ejecuta `atlas-splitter glb modelo.glb --atlas-dir atlases --output resultados`.
2. Abre Blender, cambia a **Scripting** y abre `resultados/blender/rebuild_scene.py`.
3. Ejecuta el script. Blender importa el modelo local y crea objetos/materiales editables.
4. Guarda un `.blend` nuevo antes de cambios destructivos.

El script no modifica el GLB original. Los resultados UV conservan la procedencia de nodo, malla, primitiva, material y conjunto UV. El flujo `semantic-3d` crea padres semánticos y mantiene los componentes como mallas separadas; no hace `Join`.

Si Blender no encuentra una imagen, verifica que no hayas movido la carpeta de salida y vuelve a generar el script. En Windows, ejecuta el script con una versión de Blender instalada localmente y accesible en `PATH` si quieres que `doctor` la detecte.
