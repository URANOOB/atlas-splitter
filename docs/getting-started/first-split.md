# Primer atlas

## Requisitos

Un archivo WEBP local. No requiere GPU ni modelos.

```text
atlas-splitter split atlas.webp --output resultados
```

El resultado queda en `resultados/atlas`: PNG, máscaras, PSD, `manifest.json`, reporte HTML y `atlas-atlas-splitter.zip`.

Si las piezas son demasiado pequeñas, revisa el atlas o usa el modo avanzado con `--min-area`. Para revisar el resultado: `atlas-splitter preview resultados/atlas`.
