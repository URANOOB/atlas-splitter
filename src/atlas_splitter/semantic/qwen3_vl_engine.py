"""Backend local Qwen3-VL para agrupación semántica."""

from __future__ import annotations

import logging
from time import perf_counter
from typing import Any, cast

from PIL import Image

from atlas_splitter.exceptions import SemanticInferenceError, SemanticModelUnavailableError
from atlas_splitter.runtime import resolve_device
from atlas_splitter.semantic.protocol import SemanticGroupingBackend
from atlas_splitter.semantic.response_parser import SemanticResponseParseError, parse_response_json
from atlas_splitter.semantic.types import GroupingContext, GroupingResult
from atlas_splitter.semantic.validator import SemanticResponseValidationError, validate_groups
from atlas_splitter.semantic_models.manager import is_semantic_model_downloaded, semantic_model_path

LOGGER = logging.getLogger(__name__)


class Qwen3VLSemanticGroupingBackend(SemanticGroupingBackend):
    """Carga Qwen3-VL desde disco y no permite descargas durante inferencia."""

    def __init__(
        self,
        model_name: str = "qwen3-vl-2b",
        device: str = "cuda",
        minimum_confidence: float = 0.70,
        automatic_confidence: float = 0.80,
    ) -> None:
        self.model_name = model_name
        self.device = device
        self.minimum_confidence = minimum_confidence
        self.automatic_confidence = automatic_confidence
        self._model: Any | None = None
        self._processor: Any | None = None
        self._torch: Any | None = None
        self.runtime_device = "cpu"
        self.last_repaired_responses = 0

    def _load(self) -> None:
        if self._model is not None:
            return
        if not is_semantic_model_downloaded(self.model_name):
            path = semantic_model_path(self.model_name)
            raise SemanticModelUnavailableError(
                f"No existe el modelo semántico local en {path}. "
                f"Ejecute: atlas-splitter semantic-models download {self.model_name}"
            )
        try:
            import torch
            from transformers import AutoModelForImageTextToText, AutoProcessor
        except ImportError as error:
            raise SemanticModelUnavailableError('Instale el extra opcional: pip install -e ".[semantic]"') from error
        model_path = semantic_model_path(self.model_name)
        resolution = resolve_device(self.device)
        selected = resolution.selected
        dtype = torch.float32
        if selected == "cuda":
            dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
        try:
            self._processor = AutoProcessor.from_pretrained(model_path, local_files_only=True)
            self._model = AutoModelForImageTextToText.from_pretrained(
                model_path,
                local_files_only=True,
                torch_dtype=dtype,
            )
            self._model.to(selected)
            self._model.eval()
        except OSError as error:
            raise SemanticModelUnavailableError(f"No se pudo cargar el modelo local {model_path}: {error}") from error
        self._torch = torch
        self.runtime_device = selected

    def _generate(
        self, context: GroupingContext, repair_error: str | None = None, invalid_json: str | None = None
    ) -> str:
        self._load()
        assert self._model is not None and self._processor is not None and self._torch is not None
        image_paths = [context.annotated_atlas_path, *context.contact_sheet_paths]
        images: list[Image.Image] = []
        for image_path in image_paths:
            with Image.open(image_path) as image:
                images.append(image.convert("RGB"))
        prompt = context.prompt
        if repair_error is not None and invalid_json is not None:
            prompt = (
                f"{prompt}\n\nRepair this invalid JSON. Error: {repair_error}\n"
                f"Invalid JSON: {invalid_json}\nReturn JSON only."
            )
        messages = [
            {
                "role": "user",
                "content": [{"type": "image", "image": str(image)} for image in image_paths]
                + [{"type": "text", "text": prompt}],
            }
        ]
        text = self._processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self._processor(text=[text], images=images, return_tensors="pt")
        inputs = inputs.to(self.runtime_device)
        try:
            with self._torch.inference_mode():
                generated = self._model.generate(**inputs, do_sample=False, max_new_tokens=512)
        except self._torch.OutOfMemoryError as error:
            self._release_cuda()
            raise SemanticInferenceError(
                "Qwen3-VL agotó la memoria CUDA. Reduzca el tamaño o resolución de las "
                "hojas semánticas y max_pieces_per_sheet."
            ) from error
        input_length = inputs.input_ids.shape[1]
        decoded = cast(list[str], self._processor.batch_decode(generated[:, input_length:], skip_special_tokens=True))
        return decoded[0].strip()

    def group(self, context: GroupingContext) -> GroupingResult:
        """Obtiene una propuesta, permite una reparación y valida toda su cobertura."""
        started = perf_counter()
        self.last_repaired_responses = 0
        response = self._generate(context)
        try:
            payload = parse_response_json(response)
            groups, unassigned = validate_groups(
                payload,
                {piece.piece_id for piece in context.pieces},
                self.minimum_confidence,
                self.automatic_confidence,
            )
        except (SemanticResponseParseError, SemanticResponseValidationError) as error:
            LOGGER.warning("Respuesta semántica inválida; se intentará una reparación: %s", error)
            try:
                payload = parse_response_json(self._generate(context, str(error), response))
                groups, unassigned = validate_groups(
                    payload,
                    {piece.piece_id for piece in context.pieces},
                    self.minimum_confidence,
                    self.automatic_confidence,
                )
                self.last_repaired_responses = 1
            except (SemanticResponseParseError, SemanticResponseValidationError) as repair_error:
                LOGGER.error("La reparación semántica falló: %s", repair_error)
                return GroupingResult(
                    [],
                    [piece.piece_id for piece in context.pieces],
                    "qwen3-vl",
                    self.model_name,
                    perf_counter() - started,
                )
        return GroupingResult(groups, unassigned, "qwen3-vl", self.model_name, perf_counter() - started)

    def _release_cuda(self) -> None:
        if self._torch is not None and self._torch.cuda.is_available():
            self._torch.cuda.empty_cache()

    def close(self) -> None:
        """Libera referencias y caché CUDA; es seguro antes de cargar el modelo."""
        self._model = None
        self._processor = None
        self._release_cuda()
        self._torch = None
