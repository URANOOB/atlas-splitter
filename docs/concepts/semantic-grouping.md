# Agrupación semántica

La agrupación semántica pide a un modelo local que compare piezas visuales y proponga grupos. Puede sugerir que dos regiones parecen paredes, madera o accesorios, pero no observa el modelo 3D salvo en el flujo `group-3d`.

Cada grupo tiene confianza y estado: aceptado, incierto o rechazado. El estado ayuda a decidir qué revisar; no certifica la identidad del objeto.

Los resultados se guardan aparte de las piezas originales. Edita `review.json` para aceptar, renombrar o separar propuestas antes de copiar grupos.

La [guía semántica](../guides/semantic-grouping.md) explica instalación local y archivos de salida.
