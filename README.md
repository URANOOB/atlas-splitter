# Atlas Splitter

![License](https://img.shields.io/badge/license-MIT-blue) ![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue) ![Status](https://img.shields.io/badge/status-active-success)

Herramienta CLI local para separar regiones visuales de atlas de texturas 2D y recuperar coordenadas UV de archivos GLB/glTF.

![Captura principal](https://raw.githubusercontent.com/URANOOB/atlas-splitter/main/docs/assets/screenshot.webp)

## Flujos de trabajo

| Tengo | Debo usar | Resultado |
| --- | --- | --- |
| Sólo un atlas | `split` | Piezas visuales |
| Atlas y GLB/glTF | `extract` | Regiones por UV |
| Atlas y deseo nombres | `semantic` | Grupos inferidos |
| Resultado a corregir | `review` | Revisión manual |
| Proyecto para Blender | `blender-addon` | Scripts para Blender |

## Instalación rápida

```text
pipx install atlas-splitter
```

Para soporte de geometría (GLB) e inteligencia artificial:
```text
atlas-splitter setup all
```

### Windows portable
Si no puedes instalar Python, descarga el `.zip` ejecutable desde *Releases* y úsalo en cualquier PC sin conexión.

## 3 Comandos básicos

1. **Separar visualmente:**
   ```text
   atlas-splitter split atlas.webp --output resultados
   ```

2. **Extraer usando modelo 3D:**
   ```text
   atlas-splitter extract modelo.glb --atlas atlas.webp --output resultados
   ```

3. **Ver resultados interactivos:**
   ```text
   atlas-splitter preview resultados/atlas
   ```

## Resultado

Al ejecutar cualquiera de los comandos anteriores, Atlas Splitter creará una carpeta con todas las subimágenes cortadas, un archivo manifiesto JSON detallando sus posiciones, y un reporte HTML interactivo para previsualizarlas localmente.

## Blender

Exporta el add-on oficial para importar automáticamente los archivos segmentados y reconstruir tu escena.

```text
atlas-splitter blender-addon export
```

## Privacidad

Todo el procesamiento, incluyendo modelos de IA complejos, se ejecuta de forma **100% local** en tu ordenador. Tus texturas y modelos 3D nunca abandonan tu máquina.

## Limitaciones

- Consumo elevado de memoria RAM para atlas superiores a 8K.
- Soporte para GLB estandarizado sin compresión Draco.
- La segmentación visual depende del canal de transparencia.

## Documentación

[Visita la documentación oficial](https://uranoob.github.io/atlas-splitter/) para guías detalladas, esquemas de JSON, y resolución de problemas comunes.

## Estado
Bajo desarrollo activo. Preparado para producción en flujos de trabajo de modificación de assets.

## Licencia
Distribuido bajo licencia MIT. Ver archivo `LICENSE`.
