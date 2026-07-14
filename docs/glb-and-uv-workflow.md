# Flujo GLB y UV

Usa este modo cuando el GLB/glTF contiene el atlas en un material y coordenadas `TEXCOORD_n`.

`--group-by uv-island` separa islas conectadas por una arista UV. Triángulos que sólo se tocan en un punto no se unen. Los modos `node`, `mesh` y `primitive` conservan sus identificadores de procedencia en el manifiesto.

La asociación de un atlas externo se verifica contra la textura declarada por el material. Para un GLB sin materiales usa `--allow-unbound-atlas`: esa decisión queda marcada como manual en el manifiesto.

Para confirmar asociaciones complejas usa un YAML local:

```yaml
atlas_bindings:
  - atlas: day/house.webp
    nodes: [12]
    uv_set: 0
    flip_v: true
```

Ejecuta `atlas-splitter glb modelo.glb --bindings bindings.yaml --output resultados`. Un binding YAML es una confirmación manual explícita. Cuando la asociación automática es ambigua, Atlas Splitter no adivina: informa las alternativas y pide este archivo. El manifiesto conserva método, confianza, material, textura, UV y confirmación.
