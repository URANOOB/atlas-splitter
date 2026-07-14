# Configuración

Atlas Splitter permite ajustar su comportamiento mediante un archivo YAML.
Puedes usar:
```text
atlas-splitter config init
atlas-splitter config validate
atlas-splitter config show
```

## Modelos Pydantic (Campos)

### AppConfig
| Campo | Tipo | Predeterminado | Valores | Descripción |
| --- | --- | --- | --- | --- |
| `processing` | `ProcessingConfig` | (Por defecto) | - | Parámetros de procesamiento principal |
| `segmentation` | `SegmentationConfig`| (Por defecto) | - | Parámetros de visión |
| `output` | `OutputConfig` | (Por defecto) | - | Destinos y verbosidad |
| `semantic` | `SemanticConfig` | (Por defecto) | - | Ajustes de IA |
| `gltf` | `GltfConfig` | (Por defecto) | - | Opciones de extracción |
| `grouping` | `GroupingConfig` | (Por defecto) | - | Ajustes de grupos |

### SegmentationConfig
| Campo | Tipo | Predeterminado | Valores | Descripción |
| --- | --- | --- | --- | --- |
| `min_area` | `int` | `4` | `>0` | Área mínima en píxeles para ignorar ruido |
| `padding` | `int` | `2` | `>=0` | Píxeles transparentes extra añadidos a cada recorte |

### ProcessingConfig
| Campo | Tipo | Predeterminado | Valores | Descripción |
| --- | --- | --- | --- | --- |
| `max_threads` | `int` | `8` | `>=1` | Máximo número de hilos simultáneos |

### OutputConfig
| Campo | Tipo | Predeterminado | Valores | Descripción |
| --- | --- | --- | --- | --- |
| `verbose` | `bool` | `false` | `true`, `false` | Mostrar logs detallados |
| `overwrite` | `bool` | `false` | `true`, `false` | Sobreescribir carpetas destino |

### SemanticConfig
| Campo | Tipo | Predeterminado | Valores | Descripción |
| --- | --- | --- | --- | --- |
| `model_id` | `str` | `"qwen3-vl-2b"` | - | Identificador del modelo de IA a usar |
| `confidence_threshold` | `float` | `0.8` | `0.0` - `1.0` | Confianza mínima para aceptar grupo |

### GltfConfig
| Campo | Tipo | Predeterminado | Valores | Descripción |
| --- | --- | --- | --- | --- |
| `flip_v` | `bool` | `true` | `true`, `false` | Invertir coordenada V al exportar |

### GroupingConfig
| Campo | Tipo | Predeterminado | Valores | Descripción |
| --- | --- | --- | --- | --- |
| `max_groups` | `int` | `100` | `>=1` | Límite máximo de carpetas |

## YAML Mínimo

```yaml
version: 1
segmentation:
  min_area: 10
```

## YAML Avanzado

```yaml
version: 1
segmentation:
  min_area: 5
  padding: 4
output:
  verbose: true
  overwrite: false
semantic:
  confidence_threshold: 0.85
  model_id: "qwen3-vl-2b"
```
