"""Excepciones propias del dominio."""


class AtlasSplitterError(Exception):
    """Error base de la aplicación."""


class StageNotAvailableError(AtlasSplitterError):
    """Funcionalidad reservada para una etapa posterior."""


class ModelUnavailableError(AtlasSplitterError):
    """El modelo solicitado no está instalado o no tiene checkpoint local."""


class DeviceResolutionError(AtlasSplitterError):
    """El dispositivo solicitado no puede usarse en este equipo."""


class Sam2InferenceError(AtlasSplitterError):
    """SAM 2 no pudo completar una inferencia en el dispositivo elegido."""


class SemanticModelUnavailableError(AtlasSplitterError):
    """El modelo semántico local o sus dependencias no están disponibles."""


class SemanticInferenceError(AtlasSplitterError):
    """El backend semántico no pudo completar una inferencia local."""


class GltfLoadError(AtlasSplitterError):
    """No se pudo cargar de forma segura un GLB o glTF local."""


class AccessorDecodeError(AtlasSplitterError):
    """Un accessor glTF no cumple el formato esperado."""


class PrimitiveDecodeError(AtlasSplitterError):
    """Una primitiva de malla no puede convertirse a triángulos."""


class DracoDecoderUnavailableError(PrimitiveDecodeError):
    """Los artefactos locales o Node necesarios para Draco no están disponibles."""


class DracoDecodeError(PrimitiveDecodeError):
    """El decodificador local Draco rechazó una primitiva comprimida."""
