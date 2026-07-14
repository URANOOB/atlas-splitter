# Agrupación semántica

`semantic` separa el atlas y usa Qwen3-VL local para proponer nombres y grupos. Es una ayuda de clasificación, no una afirmación sobre la geometría ni una reconstrucción del objeto.

```text
atlas-splitter setup ai
atlas-splitter models download qwen3-vl-2b
atlas-splitter semantic atlas.webp --output resultados
```

La descarga es explícita. El modelo puede trabajar en CPU, CUDA o MPS según el equipo, pero CPU suele ser más lenta. Las propuestas se clasifican como aceptadas, inciertas o rechazadas según su confianza; revísalas antes de usarlas.

El resultado añade `semantic_manifest.json`, `review.json`, `grouped/`, `objects/`, `uncertain/`, `unassigned/` y un reporte. `group` aplica la misma etapa a una extracción visual existente. Conserva los PNG y máscaras originales: las salidas semánticas no los sustituyen.
