"""
Dart model renderer entrypoint.

Emits Freezed/JsonSerializable "model libraries" to `*_model.dart` paths so the
canonical `*.dart` locations can be reserved for API barrel exports.
"""

from aware_meta.graph.config.render.layout_strategy import ObjectConfigGraphRenderLayoutStrategy

from dart_grammar.layout_strategy import DartModelLayoutStrategy
from dart_grammar.renderer import DartRenderer


class DartModelRenderer(DartRenderer):
    def __init__(self, layout_strategy: ObjectConfigGraphRenderLayoutStrategy) -> None:
        model_layout = DartModelLayoutStrategy.from_parent(layout_strategy)
        super().__init__(layout_strategy=model_layout)


__all__ = ["DartModelRenderer"]
