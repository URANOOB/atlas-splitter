"""Modelos de configuración y carga YAML para la aplicación."""

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class SegmentationConfig(BaseModel):
    """Umbrales para la segmentación y posterior filtrado."""

    model_config = ConfigDict(extra="forbid")
    confidence: float = Field(default=0.88, ge=0.0, le=1.0)
    stability: float = Field(default=0.92, ge=0.0, le=1.0)
    min_area: int = Field(default=400, ge=1)
    max_area_ratio: float = Field(default=0.45, gt=0.0, le=1.0)
    duplicate_iou: float = Field(default=0.80, ge=0.0, le=1.0)
    preserve_small: bool = True
    background_threshold: float = Field(default=24.0, ge=0.0, le=255.0)
    morphology_kernel: int = Field(default=3, ge=1, le=31)
    sam2_points_per_side: int = Field(default=16, ge=4, le=64)
    sam2_points_per_batch: int = Field(default=16, ge=1, le=64)
    sam2_edge_padding: int = Field(default=4, ge=0, le=8)


class ProcessingConfig(BaseModel):
    """Opciones de procesado y recorte."""

    model_config = ConfigDict(extra="forbid")
    padding: int = Field(default=16, ge=0)
    crop_elements: bool = False
    use_mixed_precision: bool = True


class OutputConfig(BaseModel):
    """Archivos que el pipeline debe generar."""

    model_config = ConfigDict(extra="forbid")
    include_psd: bool = True
    include_png: bool = True
    include_masks: bool = True
    create_contact_sheet: bool = True
    create_zip: bool = True


class GroupingConfig(BaseModel):
    """Opciones de la agrupación semántica, desactivada por defecto."""

    model_config = ConfigDict(extra="forbid")
    enabled: bool = False
    backend: Literal["qwen3-vl"] = "qwen3-vl"
    model: Literal["qwen3-vl-2b"] = "qwen3-vl-2b"
    device: Literal["auto", "cpu", "cuda"] = "cuda"
    minimum_confidence: float = Field(default=0.70, ge=0.0, le=1.0)
    automatic_confidence: float = Field(default=0.80, ge=0.0, le=1.0)
    max_pieces_per_sheet: int = Field(default=25, ge=1)
    naming_language: Literal["en"] = "en"
    keep_semantic_inputs: bool = False

    @model_validator(mode="after")
    def _validate_confidence_order(self) -> "GroupingConfig":
        if self.automatic_confidence < self.minimum_confidence:
            raise ValueError("automatic_confidence no puede ser menor que minimum_confidence")
        return self


class GltfConfig(BaseModel):
    """Opciones del modo guiado por geometría."""

    model_config = ConfigDict(extra="forbid")
    group_by: Literal["node", "mesh", "primitive", "uv-island"] = "uv-island"
    texture_slot: Literal["baseColor", "normal", "metallicRoughness", "occlusion", "emissive"] = "baseColor"
    crop_padding: int = Field(default=2, ge=0)
    export_blender_script: bool = True


class SemanticConfig(BaseModel):
    """Opciones del modo semántico sin geometría, desactivado por defecto."""

    model_config = ConfigDict(extra="forbid")
    enabled: bool = False
    backend: Literal["qwen3-vl"] = "qwen3-vl"
    model: str = "Qwen/Qwen3-VL-4B-Instruct"
    min_confidence: float = Field(default=0.65, ge=0.0, le=1.0)
    allow_uncertain: bool = True
    refine_with_sam2: bool = False


class AppConfig(BaseModel):
    """Configuración completa, con valores seguros para el MVP."""

    model_config = ConfigDict(extra="forbid")
    device: Literal["auto", "cpu", "cuda"] = "cuda"
    model: Literal["sam2-tiny", "sam2-small"] = "sam2-small"
    segmentation: SegmentationConfig = Field(default_factory=SegmentationConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    grouping: GroupingConfig = Field(default_factory=GroupingConfig)
    gltf: GltfConfig = Field(default_factory=GltfConfig)
    semantic: SemanticConfig = Field(default_factory=SemanticConfig)


def load_config(path: Path | None = None) -> AppConfig:
    """Carga una configuración YAML; sin ruta devuelve los valores por defecto."""
    if path is None:
        return AppConfig()
    with path.open("r", encoding="utf-8") as config_file:
        contents = yaml.safe_load(config_file) or {}
    if not isinstance(contents, dict):
        msg = "La configuración YAML debe contener un objeto en su raíz."
        raise ValueError(msg)
    return AppConfig.model_validate(contents)


def write_default_config(path: Path) -> Path:
    """Crea una configuración YAML editable sin sobrescribir decisiones del usuario."""
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(AppConfig().model_dump(mode="json"), sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    return path


def apply_cli_overrides(config: AppConfig, overrides: dict[str, Any]) -> AppConfig:
    """Aplica solo valores CLI explícitos, que tienen prioridad sobre YAML."""
    data = config.model_dump()
    for dotted_key, value in overrides.items():
        if value is None:
            continue
        target = data
        parts = dotted_key.split(".")
        for part in parts[:-1]:
            target = target[part]
        target[parts[-1]] = value
    return AppConfig.model_validate(data)
