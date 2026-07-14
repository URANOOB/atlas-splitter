# Segmentación visual vs Geometría

La decisión de qué comando usar se basa puramente en la información que tienes.

**Segmentación Visual (`split`):**
Solo mira colores y transparencia.
Si dos partes del dibujo se tocan, las considera una sola pieza.
*Precisión:* Aproximada y ruidosa.

**Extracción por Geometría (`extract`):**
Lee las matemáticas del archivo 3D.
Incluso si dos partes del dibujo se tocan en el atlas, si el modelo 3D usa coordenadas separadas, las separará perfectamente.
*Precisión:* Exacta, dictada por los datos del modelo.
