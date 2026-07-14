# Extracción GLB y UV

Un GLB o glTF puede indicar qué parte del atlas usa cada cara mediante coordenadas UV. UV no es una imagen: es un mapa de posiciones sobre la textura. `TEXCOORD_0` es el primer conjunto de esas posiciones.

```text
atlas-splitter inspect modelo.glb
atlas-splitter extract modelo.glb --atlas atlas.webp --output resultados
```

`extract` lee el modelo y no lo modifica. Puede usar una textura embebida, un atlas externo con `--atlas`, un directorio asociado por nodos con `--atlas-dir` o asociaciones confirmadas con `--bindings`; usa sólo una de esas opciones a la vez. Si el atlas se ve invertido, revisa `--flip-v`. Si hay Draco, instala y comprueba el decodificador local antes de repetir la extracción.

El resultado sencillo incluye `uv_manifest.json`. Una extracción con varios atlas puede añadir `objects_manifest.json`, `project.json` y `blender/rebuild_scene.py`. Las asociaciones ambiguas se registran con método y confianza; no las trates como una certeza automática.
