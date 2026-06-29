from __future__ import annotations

from aware_code.language_service.features.semantic_tokens_capabilities.collector import (
    SemanticTokenCollector,
)
from aware_code.language_service.features.semantic_tokens_capabilities.sections import (
    collect_code_section_tokens,
)


def _sections_provider(collector: SemanticTokenCollector) -> None:
    collect_code_section_tokens(collector=collector)
