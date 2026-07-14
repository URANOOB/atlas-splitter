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

## Alias de compatibilidad

`run`, `glb`, `install`, `semantic-3d` y `semantic-models` son alias ocultos y deprecados. Usa `split`, `extract`, `setup`, `group-3d` y `models`.
