# Primer atlas

Usa un archivo WEBP con transparencia cuando sea posible. Las zonas transparentes ayudan a que `split` encuentre piezas separadas.

```text
atlas-splitter split textura.webp --output resultados
atlas-splitter preview resultados/textura
```

La salida contiene el atlas copiado en `source/`, un manifiesto, PNG, máscaras y normalmente PSD y un reporte. No sobrescribe una carpeta de salida existente: cambia `--output` o mueve el resultado anterior.

Las piezas que se tocan pueden quedar unidas. Revisa el reporte y consulta [segmentación visual](../guides/visual-segmentation.md) antes de usar la salida como una clasificación definitiva.
