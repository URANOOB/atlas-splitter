# Inicio rápido

Este flujo no necesita GPU, YAML ni modelos. El repositorio incluye un generador de atlas pequeño para comprobar la instalación.

```text
atlas-splitter doctor
python scripts/create_test_atlas.py
atlas-splitter split work/synthetic_atlas.webp --output resultados
atlas-splitter preview resultados/synthetic_atlas
```

Después de `split` encontrarás:

```text
resultados/synthetic_atlas/
├── source/synthetic_atlas.webp
├── manifest.json
├── png/
├── masks/
├── psd/
└── report/index.html
```

El reporte es HTML autocontenido y se puede regenerar. Las piezas son visuales y aproximadas: abre el reporte y comprueba bordes, transparencias y elementos pequeños antes de continuar.
