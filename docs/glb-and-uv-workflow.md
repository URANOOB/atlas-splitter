# Flujo GLB y UV

Usa este modo cuando el GLB/glTF contiene el atlas en un material y coordenadas `TEXCOORD_n`.

`--group-by uv-island` separa islas conectadas por una arista UV. Triángulos que sólo se tocan en un punto no se unen. Los modos `node`, `mesh` y `primitive` conservan sus identificadores de procedencia en el manifiesto.

La asociación de un atlas externo se verifica contra la textura declarada por el material. Para un GLB sin materiales usa `--allow-unbound-atlas`: esa decisión queda marcada como manual en el manifiesto.

Inspecciona primero un modelo sin modificarlo:

```text
atlas-splitter inspect modelo.glb
atlas-splitter inspect modelo.gltf --format json
```

Con `--atlas-dir`, Atlas Splitter compara primero el contenido RGBA normalizado y las dimensiones con las imágenes declaradas por los materiales. Como último recurso usa nombres normalizados (por ejemplo, elimina sufijos `_day`, `_diffuse` o `_basecolor`) y lo registra con confianza menor. Las texturas normales no se tratan como color base salvo que elijas explícitamente `--texture-slot normal`.

Para confirmar asociaciones complejas usa un YAML local versionado:

```yaml
version: 1

atlas_bindings:
  - atlas: day/house.webp
    nodes: [12]
    texture_slot: baseColor
    uv_set: 0
    flip_v: true
```

Ejecuta `atlas-splitter glb modelo.glb --bindings bindings.yaml --output resultados`. Un binding YAML es una confirmación manual explícita. Cuando la asociación automática es ambigua, Atlas Splitter no adivina: informa las alternativas y pide este archivo. Las ejecuciones con varios atlas escriben también `project.json`, que enlaza cada carpeta de atlas con su evidencia y sus elementos exportados.
