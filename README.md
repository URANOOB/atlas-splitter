# Atlas Splitter

![Licencia MIT](https://img.shields.io/badge/licencia-MIT-blue) ![Python 3.11–3.13](https://img.shields.io/badge/Python-3.11--3.13-blue)

CLI local para separar atlas de texturas y extraer regiones UV de GLB/glTF.

![Atlas real de ejemplo](docs/assets/first-house-day-atlas.webp)

| Tengo | Uso | Resultado |
| --- | --- | --- |
| Sólo un atlas | `split` | Piezas visuales aproximadas |
| Atlas y GLB/glTF | `extract` | Regiones guiadas por UV |
| Atlas y deseo nombres | `semantic` | Grupos inferidos localmente |

## Instalación rápida

```text
pipx install atlas-splitter
atlas-splitter doctor
```

## Tres comandos

```text
atlas-splitter split atlas.webp --output resultados
atlas-splitter extract modelo.glb --atlas atlas.webp --output resultados
atlas-splitter blender-addon export --output Descargas
```

`split` genera PNG, máscaras, PSD opcionales y un reporte. `extract` no modifica el GLB. La versión portable para Windows se distribuye como ZIP en Releases.

Todo el procesamiento ocurre localmente. Los modelos opcionales se descargan sólo con una orden explícita. La segmentación visual y los nombres semánticos son aproximaciones: revisa las piezas antes de usarlas.

La documentación completa está en [docs/](docs/index.md). Consulta [licencia](LICENSE) y [seguridad](SECURITY.md).
