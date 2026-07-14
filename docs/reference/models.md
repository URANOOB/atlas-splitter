# Modelos locales

`atlas-splitter models list` muestra checkpoints de SAM 2. Los modelos registrados son `sam2-tiny` (aprox. 150 MB) y `sam2-small` (aprox. 185 MB). Descárgalos sólo de forma explícita.

```text
atlas-splitter models list
atlas-splitter models download sam2-tiny
```

Qwen3-VL se usa para agrupación semántica y se prepara con `atlas-splitter setup ai` seguido de `atlas-splitter models download qwen3-vl-2b`. La descarga y el tamaño pueden cambiar con sus dependencias; `doctor` informa disponibilidad local.

Ningún comando de procesamiento descarga un modelo por sí mismo. Si falta uno, instala o descarga el componente pedido y vuelve a ejecutar el comando.
