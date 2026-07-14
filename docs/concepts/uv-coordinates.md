# Coordenadas UV

UV es un mapa entre vértices de una malla 3D y píxeles de una textura. U y V normalmente están entre 0 y 1: U va de izquierda a derecha, V va de abajo arriba en glTF.

`extract` rasteriza esas coordenadas para obtener regiones reales del atlas. El resultado puede usar repetición, espejo, transformaciones de textura o varios materiales; por eso se debe inspeccionar el GLB antes de editar.

Una imagen sin GLB no permite recuperar UV. `split` y `semantic` son útiles para edición 2D, pero no pueden inventar caras ni una malla exacta.
