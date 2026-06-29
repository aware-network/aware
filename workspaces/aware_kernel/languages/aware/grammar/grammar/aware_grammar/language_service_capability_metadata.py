from __future__ import annotations

from aware_code.language_service_capability_contract import (
    build_language_service_capability_metadata_from_semantic_contract,
)
from aware_grammar.semantic_contract import (
    AWARE_GRAMMAR_CAPABILITY_EXECUTION_POLICY,
    AWARE_GRAMMAR_CAPABILITY_PARTICIPATION,
    AWARE_GRAMMAR_LEXICAL_OWNER,
    AWARE_GRAMMAR_SEMANTIC_CONTRACT,
)

AWARE_GRAMMAR_CAPABILITY_METADATA = (
    build_language_service_capability_metadata_from_semantic_contract(
        AWARE_GRAMMAR_SEMANTIC_CONTRACT
    )
)

__all__ = [
    "AWARE_GRAMMAR_CAPABILITY_EXECUTION_POLICY",
    "AWARE_GRAMMAR_CAPABILITY_METADATA",
    "AWARE_GRAMMAR_CAPABILITY_PARTICIPATION",
    "AWARE_GRAMMAR_LEXICAL_OWNER",
]
