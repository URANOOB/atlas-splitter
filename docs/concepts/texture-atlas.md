# Atlas de texturas

Un atlas es una sola imagen que contiene muchas zonas de textura. Un juego o modelo puede usarlo para reducir archivos y cambios de material.

Las zonas no siempre son objetos completos: una misma pared puede usar varias partes y una zona puede incluir píxeles transparentes. Por eso una pieza visual no equivale necesariamente a una malla 3D.

`split` trabaja sobre atlas WEBP locales. Conserva el archivo original y revisa transparencia, bordes y escala antes de procesarlo.

Si tienes el GLB o glTF correspondiente, usa [UV](uv-coordinates.md) para una extracción basada en datos del modelo.
