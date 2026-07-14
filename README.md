# Atlas Splitter

Separa atlas de texturas localmente para editarlos como piezas 2D o extraer regiones UV exactas desde un GLB/glTF.

![Objetos separados en Blender](docs/assets/semantic-first-house-separated.png)

| Tengo | Debo usar | Precisión |
| --- | --- | --- |
| Atlas solamente | `split` | Aproximada |
| Atlas y GLB/glTF | `extract` | Basada en UV |
| Atlas sin GLB y deseo nombres | `semantic` | Inferencia visual |

## Instalación

```text
pipx install git+https://github.com/URANOOB/atlas-splitter.git
atlas-splitter doctor
```

Las funciones extra se instalan desde cualquier carpeta, previa confirmación. Ningún modelo se descarga durante un procesamiento.

```text
atlas-splitter setup geometry
atlas-splitter setup ai
atlas-splitter setup all
```

## Tres comandos

```text
atlas-splitter split atlas.webp --output resultados
atlas-splitter extract modelo.glb --atlas atlas.webp --output resultados
atlas-splitter semantic atlas.webp --output resultados
```

`split` genera `png/`, `masks/`, `psd/`, `manifest.json`, un reporte HTML y un ZIP. `extract` genera manifiestos UV y scripts de Blender. `semantic` usa Qwen3-VL local sólo si se descargó explícitamente:

```text
atlas-splitter semantic-models download qwen3-vl-2b
```

## Límites

La segmentación visual es una aproximación y los nombres de IA requieren revisión. Sin GLB/glTF no hay geometría ni coordenadas UV, así que no puede reconstruirse fielmente el objeto 3D.

## Documentación

Guías de [instalación](docs/getting-started/installation.md), [primer atlas](docs/getting-started/first-split.md), [extracción GLB](docs/getting-started/first-glb-extraction.md), [Blender](docs/guides/blender.md) y [problemas](docs/troubleshooting/installation.md).

## Estado y licencia

Primera versión pública estable en preparación. Ejecuta `python -m pytest`, `python -m ruff check .`, `python -m mypy` y `python -m build` antes de publicar. Licencia [MIT](LICENSE).
