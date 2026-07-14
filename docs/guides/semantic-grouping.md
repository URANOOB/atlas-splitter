# Agrupación semántica

Puedes agrupar piezas visuales basándote en inteligencia artificial para inferir qué representan (por ejemplo, "pared", "suelo", "personaje").

## ¿Qué hace Qwen3-VL?
Es un modelo de lenguaje visual. Analiza la imagen recortada y devuelve un nombre que describe su contenido.
* **Tamaño aproximado:** Requiere descargar varios gigabytes.
* **Requisitos:** Debes ejecutar `setup ai`.
* **Procesamiento local:** Ninguna imagen se envía a servidores externos. Qwen3-VL corre en tu máquina.

## CPU, CUDA y MPS
* **CPU:** Funciona, pero es lento.
* **CUDA:** Aceleración rápida si tienes una gráfica NVIDIA.
* **MPS:** Aceleración en procesadores de Apple (M1, M2, etc.).

## Confianza y Estados
La IA evalúa cada pieza y asigna:
* **Confianza:** Un número de 0.0 a 1.0.
* **Grupos aceptados:** Si la confianza es alta.
* **Grupos inciertos:** Si el modelo duda, se envían a revisión.
* **Grupos rechazados:** Se marcan como no asignados.
* **Errores de clasificación:** La IA puede equivocarse y llamar "pared" a una "mesa". Siempre puedes arreglarlo en la revisión manual.

## Comandos

Preparar el entorno y descargar (descarga explícita):
```text
atlas-splitter setup ai
atlas-splitter models download qwen3-vl-2b
```

Agrupar semánticamente:
```text
atlas-splitter semantic atlas.webp --output resultados
```

## Salida generada

```text
semantic_manifest.json
review.json
grouped/
objects/
uncertain/
unassigned/
report/index.html
```
