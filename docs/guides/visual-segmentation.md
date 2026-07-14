# Segmentación visual

La segmentación visual procesa una imagen sin ninguna información 3D extra. Su propósito es recortar formas independientes.

## Qué analiza
Busca "islas" de píxeles no transparentes. Todo lo que esté conectado por píxeles visibles se considera una sola pieza.

* **Transparencia:** Es el delimitador principal. Atlas Splitter detecta el canal alfa y divide donde el alfa es 0.
* **Fondos:** Si tu imagen no tiene transparencia, la herramienta asume que es una sola pieza sólida. En esos casos, fallará en dividirla a menos que uses una herramienta externa primero para quitar el fondo.
* **Regiones conectadas:** Píxeles diagonales se consideran conectados por defecto.
* **Máscaras y recorte:** Las piezas finales se recortan para eliminar el espacio vacío a su alrededor.
* **Padding:** Se añade un relleno transparente de seguridad alrededor del recorte.
* **Área mínima:** Si una pieza generada tiene menos de 4 píxeles cuadrados, se ignora como "ruido".
* **Deduplicación:** Las piezas idénticas a nivel de píxel se agrupan.
* **SAM 2:** Opcionalmente, se puede utilizar el modelo SAM 2 para mejorar la separación.
* **PSD:** Puede procesar capas individuales.

## Ejemplos

Comando principal:
```text
atlas-splitter split atlas.webp
```

Comando avanzado especificando área mínima de 10 píxeles:
```text
atlas-splitter split atlas.webp --min-area 10
```

## Errores comunes y situaciones donde fallará
1. **Piezas del mismo color unidas:** Si dos piezas se tocan aunque sea por 1 píxel no transparente, serán exportadas como una sola imagen.
2. **Fondos complejos:** Si la imagen tiene un fondo negro o blanco en lugar de alfa, no se podrá separar.
3. **Objetos superpuestos:** No puede reconstruir información que está oculta detrás de otra pieza.
4. **Detalles muy pequeños:** Si el área mínima es mayor que la pieza, ésta se descartará.
5. **Ausencia de transparencia:** Todo el archivo será 1 sola pieza.
