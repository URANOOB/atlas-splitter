"""Modelos de visión-lenguaje admitidos por la agrupación semántica."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SemanticModelSpec:
    """Identidad remota y nombre local estable de un modelo semántico."""

    name: str
    repository_id: str
    local_directory_name: str
    approximate_size: str


SEMANTIC_MODELS: dict[str, SemanticModelSpec] = {
    "qwen3-vl-2b": SemanticModelSpec(
        name="qwen3-vl-2b",
        repository_id="Qwen/Qwen3-VL-2B-Instruct",
        local_directory_name="qwen3-vl-2b",
        approximate_size="~4 GB",
    )
}


def get_semantic_model(name: str) -> SemanticModelSpec:
    """Devuelve un modelo registrado o un error legible."""
    try:
        return SEMANTIC_MODELS[name]
    except KeyError as error:
        raise ValueError(f"Modelo semántico no admitido: {name}. Disponibles: {', '.join(SEMANTIC_MODELS)}") from error
