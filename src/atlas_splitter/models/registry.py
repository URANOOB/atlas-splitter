"""Registro extensible de checkpoints SAM 2 admitidos."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelSpec:
    """Identidad, URL y configuración de un modelo SAM 2."""

    name: str
    checkpoint_filename: str
    config_name: str
    download_url: str
    approximate_size: str


MODELS: dict[str, ModelSpec] = {
    "sam2-tiny": ModelSpec(
        "sam2-tiny",
        "sam2.1_hiera_tiny.pt",
        "configs/sam2.1/sam2.1_hiera_t.yaml",
        "https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_tiny.pt",
        "~150 MB",
    ),
    "sam2-small": ModelSpec(
        "sam2-small",
        "sam2.1_hiera_small.pt",
        "configs/sam2.1/sam2.1_hiera_s.yaml",
        "https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_small.pt",
        "~185 MB",
    ),
}


def get_model(name: str) -> ModelSpec:
    """Devuelve la especificación registrada o un error legible."""
    try:
        return MODELS[name]
    except KeyError as error:
        raise ValueError(f"Modelo no admitido: {name}. Disponibles: {', '.join(MODELS)}") from error
