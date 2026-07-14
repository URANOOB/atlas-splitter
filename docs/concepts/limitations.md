# Límites reales

Un atlas es una imagen; no contiene por sí solo nombre de objeto, malla, UV ni orden de capas. `split` encuentra regiones visibles. Puede unir regiones cercanas, separar detalles de un mismo objeto o ignorar píxeles demasiado pequeños.

`semantic` añade nombres y grupos inferidos por un modelo local. La confianza ayuda a priorizar revisión, pero no prueba que una pieza pertenezca a una pared, personaje u objeto concreto. No crea geometría 3D.

`extract` necesita un GLB/glTF con UV utilizables. Atlas ausente, asociaciones ambiguas, Draco no disponible o extensiones no admitidas pueden impedir la extracción. Conserva siempre el modelo original.

Usa `doctor` antes de procesar, guarda el reporte junto con sus manifiestos y usa `review.json` para cambios humanos. Si necesitas fidelidad 3D, usa `extract`, no `split` ni `semantic`.
