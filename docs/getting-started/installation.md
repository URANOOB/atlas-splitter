# Instalación

Atlas Splitter se instala mejor usando `pipx` para mantener sus dependencias aisladas.

## Requisitos

* **Python:** 3.11 a 3.13.
* **Sistemas operativos:** Windows 10+, macOS 13+, Linux (Ubuntu 22.04+).
* **Espacio en disco:** 500 MB mínimos. Si usas IA, 5-10 GB adicionales para modelos.
* **GPU (Opcional):** Tarjeta gráfica compatible con CUDA (NVIDIA) o MPS (Apple Silicon) para acelerar operaciones de IA.
* **Internet:** Sólo para la instalación y descarga de modelos (opcional).

## Pipx

Si no tienes `pipx`, instálalo primero.

### Windows PowerShell

Abre PowerShell y ejecuta:
```powershell
pip install pipx
pipx ensurepath
```
Cierra y vuelve a abrir PowerShell, luego:
```text
pipx install atlas-splitter
```

### Windows CMD

Ejecuta en Símbolo del sistema:
```cmd
pip install pipx
python -m pipx ensurepath
```
Reinicia la consola e instala:
```text
pipx install atlas-splitter
```

### Linux

```bash
sudo apt update
sudo apt install pipx
pipx ensurepath
```
Reinicia la terminal e instala:
```text
pipx install atlas-splitter
```

### macOS

```bash
brew install pipx
pipx ensurepath
```
Reinicia la terminal e instala:
```text
pipx install atlas-splitter
```

## Wheel

Si tienes un archivo release descargado, puedes instalarlo directamente:
```text
pipx install atlas_splitter-0.2.0-py3-none-any.whl
```

## Desarrollo

Para contribuir o instalar desde el código fuente:
```text
git clone https://github.com/URANOOB/atlas-splitter.git
cd atlas-splitter
python -m venv .venv
# Activar entorno
pip install -e ".[dev,geometry,docs]"
```

## Componentes opcionales

Instala soporte para geometría 3D y GLB:
```text
atlas-splitter setup geometry
```

Instala soporte para segmentación semántica e IA (PyTorch, Transformers):
```text
atlas-splitter setup ai
```

Instala todo:
```text
atlas-splitter setup all
```

## Actualización y eliminación

Para actualizar:
```text
pipx upgrade atlas-splitter
```

Para desinstalar:
```text
pipx uninstall atlas-splitter
```
*Nota: La desinstalación no elimina los modelos de IA descargados en caché.*

## Verificación

Asegúrate de que todo está correcto:
```text
atlas-splitter --version
atlas-splitter doctor
```
