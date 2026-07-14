# Problemas de GLB y UV

## Síntoma

`extract` no encuentra atlas, UV o no puede abrir un GLB.

## Causa probable

Falta el extra Geometry, el atlas no está asociado al material o la compresión Draco requiere un decodificador local.

## Comprobación

```text
atlas-splitter doctor
atlas-splitter inspect modelo.glb
```

## Solución

Instala Geometry con `atlas-splitter setup geometry`. Usa `inspect` para ver materiales y UV; entrega `--atlas`, `--atlas-dir` o `--bindings` sólo cuando conozcas la asociación. No intentes sustituir un error UV con `semantic`.

## Código y siguiente paso

La CLI muestra un código legible y el comando recomendado. `--debug` revela traceback sólo para diagnóstico.
