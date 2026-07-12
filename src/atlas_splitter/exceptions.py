"""Excepciones propias del dominio."""


class AtlasSplitterError(Exception):
    """Error base de la aplicación."""


class StageNotAvailableError(AtlasSplitterError):
    """Funcionalidad reservada para una etapa posterior."""


class ModelUnavailableError(AtlasSplitterError):
    """El modelo solicitado no está instalado o no tiene checkpoint local."""


class Sam2InferenceError(AtlasSplitterError):
    """SAM 2 no pudo completar una inferencia en el dispositivo elegido."""
