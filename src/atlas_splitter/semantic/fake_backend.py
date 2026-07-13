"""Backend controlable para pruebas sin modelos ni GPU."""

from __future__ import annotations

from atlas_splitter.semantic.types import GroupingContext, GroupingResult


class FakeSemanticGroupingBackend:
    """Devuelve un resultado predefinido y registra el contexto recibido."""

    def __init__(self, result: GroupingResult) -> None:
        self.result = result
        self.last_context: GroupingContext | None = None
        self.closed = False

    def group(self, context: GroupingContext) -> GroupingResult:
        self.last_context = context
        return self.result

    def close(self) -> None:
        self.closed = True
