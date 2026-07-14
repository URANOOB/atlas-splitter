# Instalación en Linux y macOS

Requiere Python 3.11, 3.12 o 3.13 y `python3` disponible en la terminal. Desde el repositorio:

```bash
chmod +x scripts/install.sh
./scripts/install.sh basic
```

Perfiles: `basic` (2D), `geometry` (GLB/UV), `semantic` (modelo local) y `all` (todos los extras). El script crea `.atlas-splitter-venv` dentro del proyecto, ejecuta `doctor` y no descarga checkpoints.

Para usar el entorno manualmente:

```bash
source .atlas-splitter-venv/bin/activate
atlas-splitter doctor
```

Descarga modelos sólo mediante los subcomandos explícitos. En macOS usa `--device cpu` o `--device auto`; CUDA no está disponible.
