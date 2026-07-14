# Referencia CLI

Este archivo se genera con `python scripts/generate_cli_docs.py`. No edites esta lista a mano.

La CLI no descarga modelos durante `split`, `semantic`, `extract` ni la generación de documentación.

## `atlas-splitter doctor`

Comprueba los requisitos locales sin descargar ni modificar nada.

```text
atlas-splitter doctor [OPTIONS]
```

## `atlas-splitter setup`

Comprueba el entorno o instala una capacidad opcional.

```text
atlas-splitter setup [OPTIONS] [COMPONENT]
```

## `atlas-splitter extract`

Atajo sencillo para extraer regiones UV exactas de un modelo.

```text
atlas-splitter extract [OPTIONS] MODEL
```

## `atlas-splitter preview`

Regenera el reporte HTML local de una extracción visual ya terminada.

```text
atlas-splitter preview [OPTIONS] OUTPUT
```

## `atlas-splitter review`

Crea la plantilla review.json sin ejecutar inferencia otra vez.

```text
atlas-splitter review [OPTIONS] OUTPUT
```

## `atlas-splitter group`

Agrupa una extracción existente con el modelo local, sin reprocesar el atlas.

```text
atlas-splitter group [OPTIONS] OUTPUT
```

## `atlas-splitter semantic`

Separa visualmente un atlas y agrupa sus piezas con IA local.

```text
atlas-splitter semantic [OPTIONS] ATLAS
```

## `atlas-splitter group-3d`

Agrupa un nodo GLB con UV sin unir físicamente sus componentes de malla.

```text
atlas-splitter group-3d [OPTIONS] MODEL ATLAS
```

## `atlas-splitter split`

Atajo sencillo para separar visualmente un atlas sin geometría.

```text
atlas-splitter split [OPTIONS] ATLAS
```

## `atlas-splitter inspect`

Inspecciona un modelo GLB/glTF; los ZIP antiguos conservan su vista heredada.

```text
atlas-splitter inspect [OPTIONS] SOURCE
```

## `atlas-splitter models`

Gestiona checkpoints de SAM 2.

```text
atlas-splitter models [OPTIONS] COMMAND [ARGS]...
```

## `atlas-splitter blender-addon`

Exporta el add-on portable para Blender.

```text
atlas-splitter blender-addon [OPTIONS] COMMAND [ARGS]...
```

## `atlas-splitter config`

Crea, valida y muestra configuración YAML.

```text
atlas-splitter config [OPTIONS] COMMAND [ARGS]...
```

## Alias de compatibilidad (Ocultos)

Estos comandos existen por compatibilidad con versiones anteriores; no los uses en flujos nuevos.

## `atlas-splitter glb`

Exporta regiones UV y materiales de un GLB/glTF enteramente local.

```text
atlas-splitter glb [OPTIONS] MODEL
```

## `atlas-splitter apply-review`

Aplica grupos manuales sin modificar los PNG ni las máscaras originales.

```text
atlas-splitter apply-review [OPTIONS] REVIEW_FILE
```

## `atlas-splitter semantic-3d`

Alias temporal deprecado de ``group-3d``.

```text
atlas-splitter semantic-3d [OPTIONS] MODEL ATLAS
```

## `atlas-splitter run`

Procesa WEBP locales mediante segmentación clásica.

```text
atlas-splitter run [OPTIONS] SOURCE
```

## `atlas-splitter install`

Alias temporal deprecado de ``setup``.

```text
atlas-splitter install [OPTIONS] [COMPONENT]
```

## `atlas-splitter semantic-models`

Gestiona modelos semánticos locales.

```text
atlas-splitter semantic-models [OPTIONS] COMMAND [ARGS]...
```

## Códigos de salida conocidos

La CLI devuelve los siguientes códigos de salida al sistema operativo:

* `0`: Éxito.
* `1`: Error genérico o excepción no controlada.
* `2`: Error de sintaxis en los argumentos de la CLI (generado por Click/Typer).
* Códigos `AS-*`: Revisa la [referencia de códigos de error](error-codes.md).
