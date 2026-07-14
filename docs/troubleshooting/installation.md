# Problemas de instalación

## Síntoma

`atlas-splitter` no se reconoce, o `doctor` muestra una dependencia opcional ausente.

## Causa probable

El entorno de `pipx` o virtualenv no está en PATH, o aún no instalaste Geometry/AI.

## Comprobación

```text
atlas-splitter doctor --format json
python --version
```

## Solución

Reabre la terminal después de instalar con pipx. Para una capacidad opcional usa `atlas-splitter setup geometry` o `atlas-splitter setup ai`; confirma la descarga. No se descargan modelos en ese paso.

## Código y siguiente paso

Los errores de instalación muestran un comando `setup` recomendado. Si persiste, crea un virtualenv limpio e instala el wheel generado.
