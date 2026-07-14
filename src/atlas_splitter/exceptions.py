"""Errores de dominio con codigos estables y orientacion para la CLI."""

from __future__ import annotations


class AtlasSplitterError(Exception):
    """Error base que puede mostrarse sin traceback a una persona usuaria."""

    code = "AS-CORE-001"
    probable_cause = "Los datos de entrada no cumplen el contrato esperado."
    solution = "Revise las rutas y opciones y vuelva a intentarlo."

    def __str__(self) -> str:
        detail = super().__str__()
        return f"{self.code}: {detail}\nCausa probable: {self.probable_cause}\nSolucion: {self.solution}"


class StageNotAvailableError(AtlasSplitterError):
    """Funcionalidad reservada para una etapa posterior."""


class InputValidationError(AtlasSplitterError):
    """Una ruta u opcion de la interfaz de linea de comandos no es valida."""

    code = "AS-CLI-004"
    probable_cause = "Una opcion o ruta no cumple el formato requerido por el comando."
    solution = "Consulta --help, corrige el valor indicado y vuelve a ejecutar el comando."


class ModelUnavailableError(AtlasSplitterError):
    """El modelo solicitado no esta instalado o no tiene checkpoint local."""

    code = "AS-MODEL-003"
    probable_cause = "El checkpoint local solicitado no esta disponible."
    solution = "Descarguelo explicitamente con el subcomando models correspondiente antes de ejecutar."


class DeviceResolutionError(AtlasSplitterError):
    """El dispositivo solicitado no puede usarse en este equipo."""

    code = "AS-MODEL-003"
    probable_cause = "CUDA o MPS no estan disponibles, o el dispositivo indicado no es valido."
    solution = "Use --device auto o --device cpu, o instale PyTorch compatible con el acelerador solicitado."


class Sam2InferenceError(AtlasSplitterError):
    """SAM 2 no pudo completar una inferencia en el dispositivo elegido."""


class SemanticModelUnavailableError(ModelUnavailableError):
    """El modelo semantico local o sus dependencias no estan disponibles."""


class SemanticInferenceError(AtlasSplitterError):
    """El backend semantico no pudo completar una inferencia local."""


class GltfLoadError(AtlasSplitterError):
    """No se pudo cargar de forma segura un GLB o glTF local."""

    code = "AS-GLB-002"
    probable_cause = "El GLB/glTF, sus buffers, texturas o su asociacion de atlas no son compatibles."
    solution = "Revise las rutas locales y use --bindings para confirmar asociaciones ambiguas."


class AccessorDecodeError(GltfLoadError):
    """Un accessor glTF no cumple el formato esperado."""


class PrimitiveDecodeError(AtlasSplitterError):
    """Una primitiva de malla no puede convertirse a triangulos."""

    code = "AS-UV-001"
    probable_cause = "La primitiva no contiene UV o indices triangulares compatibles."
    solution = "Seleccione otro --uv-set o exporte el modelo con primitivas trianguladas y UV validas."


class DracoDecoderUnavailableError(PrimitiveDecodeError):
    """Los artefactos locales o Node necesarios para Draco no estan disponibles."""


class DracoDecodeError(PrimitiveDecodeError):
    """El decodificador local Draco rechazo una primitiva comprimida."""
