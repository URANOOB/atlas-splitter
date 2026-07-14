# Coordenadas UV

En los gráficos 3D, una malla (mesh) es sólo forma. Para darle color, necesita saber qué parte de la imagen va en cada triángulo.

**U** y **V** son simplemente X e Y, pero en el espacio 2D de una textura. Representan coordenadas (generalmente de 0.0 a 1.0).

En archivos como GLB, esto suele guardarse en un atributo de geometría llamado `TEXCOORD_0`. Atlas Splitter usa esta información durante el proceso de `extract` para saber exactamente dónde recortar en lugar de adivinar mediante transparencia.
