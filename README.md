# atlas-splitter

CLI local y multiplataforma para convertir atlas de texturas en artefactos editables. Funciona en PowerShell, CMD, bash y terminales de macOS/Linux. Los archivos de entrada se procesan localmente.

## Inicio sencillo

Después de instalar, ejecuta simplemente:

```text
atlas-splitter
```

El asistente pregunta si tienes un GLB/glTF o sólo atlas WEBP, pide las rutas de entrada y salida, y crea `atlas-splitter.yaml` editable para el modo sin geometría.

## Dos modos

| Dispones de | Qué elige el asistente | Resultado |
| --- | --- | --- |
| Sólo atlas WEBP | Segmentación 2D | PNG, máscaras, PSD, manifiesto, contact sheet y ZIP. Ajusta `processing.padding` o `--calibration-pixels` para recuperar bordes. |
| GLB/glTF y atlas | Extracción guiada por UV | Máscaras UV exactas, recortes de material, manifiestos y scripts Blender con geometría editable. |

El modo GLB avisa si detecta `KHR_draco_mesh_compression`. Draco puede ser necesario para recuperar POSITION y UV; el proyecto usa únicamente el decodificador local de `draco/gltf` y nunca lo descarga durante una ejecución.

Para First House existe además la prueba semántica 3D:

```text
atlas-splitter semantic-3d GLB/Room.glb Samples/day/first-house_day.webp --output outputs
```

Agrupa primero por conectividad y proximidad 3D; Qwen3-VL local sólo etiqueta las propuestas resultantes. No hace Join de las mallas.

## Configuración

El asistente crea un YAML inicial. Ejemplo para ajustar bordes en atlas sin GLB:

```yaml
device: cuda
processing:
  padding: 4
segmentation:
  sam2_edge_padding: 4
```

CUDA es el valor predeterminado cuando está disponible. Usa `--device cpu` si necesitas forzarlo.

## Comandos directos

```text
atlas-splitter atlas.webp resultados
atlas-splitter run ./atlases --recursive --output resultados --calibration-pixels 4
atlas-splitter glb modelo.glb --atlas-dir ./atlases --allow-unbound-atlas --output resultados
atlas-splitter doctor
atlas-splitter models list
atlas-splitter semantic-models list
```

## Instalación aislada

La forma recomendada crea el entorno y dependencias sin tocar el Python global:

```text
atlas-splitter install
```

También puede hacerse manualmente:

```text
python -m venv .atlas-splitter-venv
```

Actívalo y luego instala los extras necesarios desde el directorio del repositorio:

```powershell
.\.atlas-splitter-venv\Scripts\Activate.ps1
pip install -e ".[vision,semantic,geometry]"
```

```bash
source .atlas-splitter-venv/bin/activate
pip install -e ".[vision,semantic,geometry]"
```

En macOS/Linux y Windows se usa el mismo ejecutable: `atlas-splitter`. Añade `atlas-splitter install --model sam2-small` sólo si deseas preparar también el runtime SAM 2 y su checkpoint.

## Herramientas empleadas

- Python 3.11+ y Typer/Rich para la CLI.
- NumPy, OpenCV y Pillow para máscaras, recortes y contact sheets.
- PSD Tools para PSD editables.
- PyTorch, SAM 2 y CUDA opcional para segmentación.
- Transformers, Accelerate y Qwen3-VL local para etiquetas semánticas.
- pygltflib y el decodificador Draco local para GLB/glTF, UV y mallas.
- Blender (`bpy`, sólo dentro del script generado) para reconstrucción editable.
- Pydantic y YAML para configuración y manifiestos versionados.

## Verificación

```text
python -m pytest
python -m ruff check .
python -m mypy
```
