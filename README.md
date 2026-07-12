# atlas-splitter

Convierte un atlas WEBP plano en elementos reutilizables: PNG, máscara, PSD,
manifiesto, hoja de contacto y ZIP. Todo se procesa localmente.

## Para qué sirve

Cuando solo existe un atlas final y se perdió el PSD original, `atlas-splitter`
lo **despedaza en capas nuevas** para facilitar su reutilización. No recupera las
capas artísticas originales: infiere regiones desde los píxeles visibles. Revisa
siempre la hoja de contacto antes de reutilizar los resultados.

## Instalación fácil

En Windows se recomienda WSL 2 con Ubuntu y Python 3.11 o superior.

```bash
# Instala el proyecto una vez
pip install -e .

# Instala PyTorch CUDA, SAM 2 y el checkpoint pequeño
atlas-splitter install
```

El comando `install` necesita Git y conexión a Internet solo la primera vez.
Descarga todo en el equipo; los atlas nunca se suben a ningún servicio.

Después, comprueba el entorno:

```bash
atlas-splitter doctor
```

## Uso más simple

```bash
# Guarda automáticamente en outputs/
atlas-splitter atlas.webp

# Elige una carpeta de salida
atlas-splitter atlas.webp mis-resultados
```

También se aceptan los comandos avanzados:

```bash
atlas-splitter run ./input --recursive --output outputs --zip resultados.zip
atlas-splitter doctor
atlas-splitter models list
atlas-splitter models download sam2-small
atlas-splitter inspect resultados.zip
```

## Calibrar bordes

Si SAM 2 recorta demasiado un elemento, añade píxeles al borde:

```bash
atlas-splitter atlas.webp outputs --calibration-pixels 4
```

Para usar parámetros avanzados, conserva el subcomando `run`:

```bash
atlas-splitter run atlas.webp --output outputs --calibration-pixels 4 --crop-elements
```

| Píxeles | Uso |
| --- | --- |
| `0` | No expande la máscara. |
| `2` | Corrección ligera. |
| `4` | Valor predeterminado. |
| `5-8` | Úsalo solo si aún falta borde; revisa que no incluya fondo. |

La configuración YAML equivalente es:

```yaml
segmentation:
  sam2_edge_padding: 4
```

## Archivos generados

```text
outputs/
  nombre_del_atlas/
    png/element_001.png
    masks/element_001.png
    psd/element_001.psd
    contact_sheet.png
    manifest.json
```

Cada PSD incluye `Element`, `Original crop`, `Mask` y `Background reference`
(oculta). Son capas nuevas de píxeles, no el PSD artístico original.

## Limitaciones

- Un objeto puede dividirse en varias regiones.
- SAM 2 puede crear máscaras imperfectas o duplicadas.
- Los resultados dependen de transparencia, contraste y composición del atlas.
- Revisa `contact_sheet.png` y `manifest.json` antes de usar resultados en
  producción.

## Desarrollo

```bash
python -m pytest
python -m ruff check .
python -m mypy
```
