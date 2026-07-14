# Instalación

## Requisitos

Usa Python 3.11, 3.12 o 3.13 en Windows, macOS o Linux. La instalación base necesita espacio para Python y sus dependencias; los componentes de IA añaden descargas locales. Una GPU es opcional: CUDA sirve en equipos NVIDIA y MPS en equipos Apple compatibles. Internet sólo se necesita para instalar paquetes o descargar modelos de forma explícita.

## Pipx

`pipx` instala el comando en un entorno aislado. Tras `pipx ensurepath`, cierra y abre la terminal.

```powershell
python -m pip install --user pipx
python -m pipx ensurepath
pipx install atlas-splitter
```

En CMD usa los mismos comandos `python -m`. En Linux instala `pipx` con el gestor de paquetes de tu distribución o `python -m pip install --user pipx`; en macOS puedes usar `brew install pipx`. Después ejecuta `pipx ensurepath`.

## Wheel y desarrollo

```text
pipx install atlas_splitter-0.2.0-py3-none-any.whl
git clone https://github.com/URANOOB/atlas-splitter.git
cd atlas-splitter
python -m venv .venv
```

Activa `.venv` según tu shell y ejecuta `python -m pip install -e ".[dev,geometry,docs]"` para desarrollo.

## Componentes, actualización y comprobación

`atlas-splitter setup geometry` instala dependencias GLB/glTF. `setup ai` instala dependencias de IA, no modelos. `setup all` instala ambos grupos. Actualiza con `pipx upgrade atlas-splitter` y elimina el comando con `pipx uninstall atlas-splitter`; los modelos descargados permanecen en la caché local.

```text
atlas-splitter --version
atlas-splitter doctor
```
