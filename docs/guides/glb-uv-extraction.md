# Extracción GLB y UV

## Requisitos

Geometry y un GLB/glTF con coordenadas UV válidas.

```text
atlas-splitter extract modelo.glb --atlas atlas.webp --output resultados
```

La extracción usa las UV del modelo, por eso es más precisa que la segmentación visual. Si hay varios atlas usa `--atlas-dir` o un archivo de asociaciones confirmado.
