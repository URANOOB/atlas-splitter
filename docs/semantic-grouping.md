# Agrupación semántica

La agrupación semántica es opcional y siempre local. SAM 2 propone regiones 2D; Qwen3-VL local puede asignar nombres o agrupar propuestas cuando el modelo ya está instalado. `run` y `semantic-3d` nunca descargan modelos.

`semantic-3d` usa primero componentes exactos por conectividad y proximidad geométrica. La etiqueta es una inferencia semántica y el manifiesto distingue ambas evidencias. Usa `--minimum-confidence` para conservar propuestas inciertas y `--proximity-factor` para controlar las sugerencias 3D.

Para instalar modelos usa explícitamente `atlas-splitter models download ...` o `atlas-splitter semantic-models download qwen3-vl-2b`. Revisa con `doctor` qué capacidades están disponibles.
