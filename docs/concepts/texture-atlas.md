# Atlas de textura

Un atlas junta muchas imágenes pequeñas dentro de una imagen grande. Un videojuego o modelo puede usar una sola imagen para reducir cambios de material. El atlas no dice dónde empieza un objeto: sólo contiene píxeles.

Usa `split` cuando sólo tienes la imagen y deseas piezas editables. Obtendrás una aproximación basada en transparencia, fondo y regiones de color. Usa `semantic` cuando además deseas una propuesta de grupos locales.

Si también tienes GLB/glTF, usa `extract`. El modelo trae las coordenadas UV que señalan qué zona del atlas usa cada cara. Ese flujo conserva evidencia geométrica y es el único adecuado para reconstrucción asistida.
