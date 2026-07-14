# Limitaciones

Un atlas 8K puede requerir mucha memoria porque la imagen se descomprime antes de analizarse. Cierra otras aplicaciones o trabaja con una copia reducida si el sistema se queda sin memoria.

`split` no sabe qué hay detrás de una pieza superpuesta ni separa automáticamente regiones que se tocan. Un fondo opaco, detalles pequeños y colores similares pueden producir resultados incompletos.

Los nombres y grupos de `semantic` son inferencias locales. Una confianza alta no garantiza que el nombre sea correcto. Revisa `review.json` antes de organizar archivos.

`extract` necesita UV válidas en el modelo. Draco, buffers externos ausentes o asociaciones ambiguas requieren diagnóstico y, en algunos casos, una confirmación manual.

Atlas Splitter no promete reconstruir una escena 3D ni reparar automáticamente datos de entrada dañados.
