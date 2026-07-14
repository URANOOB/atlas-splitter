# Segmentación visual

`split` observa los píxeles de un atlas WEBP; no conoce el modelo 3D. Busca regiones visibles, crea una máscara para cada una y exporta PNG y PSD según la configuración. Es una separación aproximada, no una reconstrucción 3D.

![Atlas real empleado como ejemplo](../assets/first-house-day-atlas.webp)

```text
atlas-splitter split atlas.webp --output resultados
```

La transparencia ayuda: las zonas con alfa cero separan piezas. Un fondo opaco, dos piezas que se tocan, objetos superpuestos o detalles más pequeños que `min_area` pueden producir una sola pieza o descartar ruido. Las máscaras conservan la forma detectada; el recorte y `padding` dejan un margen alrededor del cuadro.

Para ajustar área mínima, deduplicación, recorte o PSD, crea YAML con `atlas-splitter config init atlas-splitter.yml` y usa el flujo avanzado de compatibilidad sólo si necesitas opciones no expuestas por `split`. SAM 2 es opcional y nunca se descarga durante una ejecución.

Comprueba `manifest.json`, abre `report/index.html` o ejecuta `atlas-splitter preview resultados/atlas`. Si las piezas son ambiguas, corrígelas en un editor o usa [revisión manual](manual-review.md); no asumas que una máscara es exacta.
