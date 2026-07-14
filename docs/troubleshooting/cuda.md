# CUDA, MPS y CPU

## Síntoma

La IA no inicia en CUDA/MPS o falta memoria.

## Causa probable

El dispositivo pedido no existe, PyTorch no lo ve o el modelo local no está descargado.

## Comprobación

```text
atlas-splitter doctor
atlas-splitter models info qwen3-vl-2b
```

## Solución

Empieza con `atlas-splitter setup ai --device auto`; auto no asume CUDA. Usa `--device cpu` para máxima compatibilidad. `mps` sólo sirve en macOS; `cuda` no se permite en macOS. Descarga modelos sólo con `atlas-splitter models download ...`.

## Código y siguiente paso

Un error de modelo no muestra traceback salvo `--debug`; sigue el comando `models download` mostrado.
