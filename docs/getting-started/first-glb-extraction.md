# Primer GLB

Si además de la imagen tienes un modelo 3D GLB/glTF que usa ese atlas, puedes extraer las texturas guiándote por la geometría real.

1. Asegúrate de haber instalado los extras de geometría:
   ```text
   atlas-splitter setup geometry
   ```
2. Ejecuta la extracción vinculando el modelo y la imagen:
   ```text
   atlas-splitter extract modelo.glb --atlas textura.png --output resultado_glb
   ```
3. El resultado no solo incluirá las piezas de textura, sino manifiestos que mapean cada imagen extraída a la malla original y a sus coordenadas UV.

Lee la guía de [Extracción GLB y UV](../guides/glb-uv-extraction.md) para más opciones.
