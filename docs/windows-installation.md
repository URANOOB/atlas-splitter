# Instalación en Windows

Requiere Python 3.11, 3.12 o 3.13 instalado y disponible mediante `python`.

En PowerShell, desde el repositorio:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\install.ps1 -Features geometry
```

Para el flujo visual con modelos locales instala los extras, pero los modelos se mantienen bajo tu control:

```powershell
.\scripts\install.ps1 -Features all
.\.atlas-splitter-venv\Scripts\atlas-splitter.exe models list
.\.atlas-splitter-venv\Scripts\atlas-splitter.exe semantic-models list
```

Los comandos `download` son explícitos. `run`, `glb` y `semantic-3d` no descargan modelos.
