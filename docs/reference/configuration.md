# Configuración

Genera una base con `atlas-splitter config init archivo.yml`, revísala con `config validate archivo.yml` y muestra una configuración con `config show`. La CLI tiene prioridad sobre los valores YAML que expone.

| Modelo | Campos y valores predeterminados |
| --- | --- |
| `AppConfig` | `device=auto`, `model=sam2-small` y los seis grupos siguientes. |
| `SegmentationConfig` | `confidence=.88`, `stability=.92`, `min_area=400`, `max_area_ratio=.45`, `duplicate_iou=.80`, `preserve_small=true`, `background_threshold=24`, `morphology_kernel=3`, `sam2_points_per_side=16`, `sam2_points_per_batch=16`, `sam2_edge_padding=4`. |
| `ProcessingConfig` | `padding=16`, `crop_elements=false`, `use_mixed_precision=true`. |
| `OutputConfig` | `include_psd=true`, `include_png=true`, `include_masks=true`, `create_contact_sheet=true`, `create_zip=true`. |
| `GroupingConfig` | `enabled=false`, `backend=qwen3-vl`, `model=qwen3-vl-2b`, `device=auto`, `minimum_confidence=.70`, `automatic_confidence=.80`, `max_pieces_per_sheet=25`, `naming_language=en`, `keep_semantic_inputs=false`. |
| `GltfConfig` | `group_by=uv-island`, `uv_tolerance=0.000001`, `texture_slot=baseColor`, `crop_padding=2`, `export_blender_script=true`. |
| `SemanticConfig` | `enabled=false`, `backend=qwen3-vl`, `model=Qwen/Qwen3-VL-4B-Instruct`, `min_confidence=.65`, `allow_uncertain=true`, `refine_with_sam2=false`. |

Los límites son: confidencias y ratios entre 0 y 1; `min_area` desde 1; kernel de 1 a 31; puntos SAM 2 de 4 a 64; y padding SAM 2 de 0 a 8. `automatic_confidence` no puede ser menor que `minimum_confidence`. `device` admite `auto`, `cpu`, `cuda` o `mps`; `texture_slot` admite `baseColor`, `normal`, `metallicRoughness`, `occlusion` y `emissive`.

## YAML mínimo

```yaml
segmentation:
  min_area: 200
processing:
  padding: 8
```

## YAML avanzado

```yaml
device: cpu
segmentation:
  min_area: 200
  duplicate_iou: 0.85
processing:
  crop_elements: true
output:
  create_zip: false
grouping:
  enabled: false
```

No añadas claves desconocidas: los modelos Pydantic las rechazan. La configuración semántica y la de geometría describen capacidades opcionales; instalarlas y descargar modelos sigue siendo una decisión explícita.
