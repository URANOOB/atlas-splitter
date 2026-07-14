# Instalación

## Requisitos

Python 3.11 a 3.13 y `pipx` son suficientes para el flujo básico.

```text
pipx install git+https://github.com/URANOOB/atlas-splitter.git
atlas-splitter doctor
```

Añade sólo lo que vayas a usar. Cada orden confirma antes de descargar dependencias; ninguna descarga modelos.

```text
atlas-splitter setup geometry
atlas-splitter setup ai
atlas-splitter setup all
```

Si `doctor` indica un componente opcional ausente, ejecuta el `setup` indicado. Los modelos se descargan únicamente con `atlas-splitter models download` o `atlas-splitter semantic-models download`.
