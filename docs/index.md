# Atlas Splitter

Atlas Splitter es una herramienta CLI para separar regiones visuales de atlas de texturas 2D y, de forma opcional, recuperar asociaciones 3D usando archivos GLB/glTF.

## ¿Qué problema resuelve?

Cuando tienes un atlas de texturas, a menudo necesitas separar las piezas individuales para usarlas por separado. Hacer esto a mano en un editor de imágenes es lento y propenso a errores, especialmente si las piezas tienen transparencias complejas o necesitas mantener su relación con un modelo 3D. Atlas Splitter automatiza este proceso de forma local.

![Captura principal](https://raw.githubusercontent.com/URANOOB/atlas-splitter/main/docs/assets/screenshot.webp)

## Selector de flujo

| Tengo | Debo usar | Resultado |
| --- | --- | --- |
| Sólo un atlas | `split` | Piezas visuales aproximadas |
| Atlas y GLB/glTF | `extract` | Regiones basadas en UV |
| Atlas y deseo nombres | `semantic` | Grupos inferidos |
| Resultado que deseo corregir | `review` | Revisión manual |
| Proyecto para Blender | `blender-addon` | Add-on y scripts de reconstrucción |

## Instalación mínima

```text
pipx install atlas-splitter
```
Si deseas características avanzadas como IA o geometría 3D:
```text
atlas-splitter setup all
```

## Primer comando

Para separar un atlas visualmente:
```text
atlas-splitter split atlas.webp --output resultados
```

## Procesamiento local y privacidad

Atlas Splitter procesa todas las imágenes y modelos **localmente** en tu máquina. Tus datos no se envían a la nube para su procesamiento. Las únicas conexiones a Internet se realizan durante la instalación inicial para descargar modelos de IA públicos (si se solicitan).

## Plataformas compatibles

- Windows 10/11
- macOS 13+ (Apple Silicon y procesadores Intel)
- Linux (Ubuntu 22.04+)

## Limitaciones

- La segmentación visual asume que el fondo es transparente.
- Los modelos de IA no siempre son 100% precisos en la clasificación semántica.
- Los atlas muy grandes pueden consumir mucha RAM.

[Inicio rápido](getting-started/quickstart.md) | [Windows Portable](getting-started/windows-portable.md) | [Blender](guides/blender.md)
