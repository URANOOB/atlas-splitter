# Coordenadas UV

Las coordenadas UV dicen dónde cae cada vértice de una malla sobre una textura. U y V son posiciones horizontales y verticales normalizadas, no píxeles absolutos.

Un GLB puede tener varios conjuntos, como `TEXCOORD_0`. También puede tener materiales y texturas distintas por malla. `inspect` muestra información útil antes de extraer.

`extract` usa esas coordenadas para recortar regiones relacionadas con la geometría. La precisión depende de UV, materiales y asociaciones presentes en el archivo; no altera el GLB original.

Lee la [guía GLB y UV](../guides/glb-uv-extraction.md) antes de usar bindings o `flip-v`.
