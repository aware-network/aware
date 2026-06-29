from __future__ import annotations

from aware_code.language_service.features.semantic_tokens_capabilities.collector import (
    SemanticTokenCollector,
)
from aware_code.language_service.features.semantic_tokens_capabilities.lexer import (
    collect_aware_lexical_tokens,
)


def _lexical_provider(collector: SemanticTokenCollector) -> None:
    collect_aware_lexical_tokens(collector=collector)
