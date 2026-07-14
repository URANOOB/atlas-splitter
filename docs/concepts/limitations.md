# Limitaciones vigentes

1. **Memoria RAM:** Procesar un atlas 8K puede consumir gigabytes de RAM debido a cómo las bibliotecas de imágenes cargan matrices sin comprimir.
2. **Modelos unidos por color:** Si no usas GLB y usas `split`, partes de textura que intencionadamente colisionan visualmente no se pueden separar.
3. **Falsos positivos de IA:** La clasificación semántica de texturas esotéricas (ej. texturas de un monstruo espacial alienígena) devolverá etiquetas extrañas, porque la IA fue entrenada principalmente con fotografías de la realidad.
4. **GLB Draco:** La compresión draco destruye la facilidad para leer arrays planos. Debes usar GLB estandarizados.
