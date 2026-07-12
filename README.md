# atlas-splitter

`atlas-splitter` transforma un atlas WEBP plano en elementos reutilizables.
Detecta regiones visuales, las separa con transparencia y genera PNG, máscaras,
PSD, un manifiesto, una hoja de contacto y un ZIP.

## Por qué existe

Muchos recursos solo conservan un atlas final y no el PSD original. Esta
herramienta sirve para **despedazar ese atlas en capas nuevas y reutilizables**.
No recupera las capas artísticas originales: infiere elementos desde los píxeles
visibles. Por eso conviene revisar siempre la hoja de contacto final.

Todo se procesa localmente: ni atlas ni resultados salen del equipo.

## Requisitos

- Windows 10/11 con WSL 2 y Ubuntu 24.04 recomendado.
- Python 3.11 o posterior.
- Para usar SAM 2 con GPU: NVIDIA/CUDA y PyTorch compatible.
- Git, `pip`, Pillow, OpenCV, `psd-tools`, PyTorch, SAM 2 y sus pesos.

## Instalación rápida

En Ubuntu/WSL:

```bash
mkdir -p ~/venvs ~/src
python3 -m venv ~/venvs/atlas-splitter
source ~/venvs/atlas-splitter/bin/activate
python -m pip install --upgrade pip

pip install torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cu121
git clone https://github.com/facebookresearch/sam2.git ~/src/sam2
SAM2_BUILD_CUDA=0 pip install -e ~/src/sam2

cd /ruta/al/atlas-splitter
pip install -e ".[dev]"
atlas-split models download sam2-small
atlas-split doctor
```

`SAM2_BUILD_CUDA=0` evita compilar una extensión opcional de SAM 2; PyTorch
sigue usando CUDA para inferencia. `atlas-split doctor` confirma Python, GPU,
WEBP, OpenCV, checkpoint, PSD y ZIP.

## Uso básico

```bash
# Un atlas
atlas-split run atlas.webp --output resultados --zip resultados.zip

# Una carpeta
atlas-split run ./input --recursive --output resultados

# Usar CPU en vez de GPU
atlas-split run atlas.webp --device cpu

# Crear PSD/PNG recortados al elemento
atlas-split run atlas.webp --crop-elements --padding 16
```

El programa no sobrescribe carpetas de resultados ni ZIP existentes. Usa una
carpeta de salida nueva para cada intento.

## Calibración de bordes

SAM 2 puede recortar un poco de más o de menos en los bordes. Ajusta el margen
con `--calibration-pixels`:

```bash
atlas-split run atlas.webp --calibration-pixels 4 --crop-elements
```

| Valor | Cuándo usarlo |
| --- | --- |
| `0` | La máscara queda exacta, sin expansión. |
| `2` | Corrección ligera. |
| `4` | Valor predeterminado; útil si SAM 2 corta el borde. |
| `5-8` | Solo si todavía faltan píxeles; revisa que no incluya fondo. |

También puede guardarse en YAML:

```yaml
segmentation:
  sam2_edge_padding: 4
```

Los argumentos CLI tienen prioridad sobre el YAML.

## Archivos generados

```text
resultados/
  nombre_del_atlas/
    png/element_001.png
    masks/element_001.png
    psd/element_001.psd
    contact_sheet.png
    manifest.json
```

Cada PSD incluye `Element`, `Original crop`, `Mask` y `Background reference`
(oculta). Son capas nuevas de píxeles; no contienen texto, efectos ni la
estructura del PSD original.

## Comandos útiles

```bash
atlas-split doctor
atlas-split models list
atlas-split models download sam2-small
atlas-split inspect resultados.zip
```

## Limitaciones

- Un objeto puede dividirse en varias regiones.
- SAM 2 puede crear máscaras duplicadas o imperfectas.
- Los resultados dependen del contraste, alfa y composición del atlas.
- Revise `contact_sheet.png` y el `manifest.json` antes de reutilizar los
  elementos en producción.

## Desarrollo

```bash
python -m pytest
python -m ruff check .
python -m mypy
ATLAS_SPLITTER_GPU_TEST=1 python -m pytest tests/test_sam2_gpu.py
```
