from __future__ import annotations

from aware_code.language_service_capability_contract import (
    build_language_service_capability_metadata_from_semantic_contract,
)
from aware_code.semantic_contract import (
    AWARE_CODE_SEMANTIC_CONTRACT,
    CODE_CAPABILITY_EXECUTION_POLICY,
    CODE_CAPABILITY_PARTICIPATION,
    CODE_SECTION_OWNER,
)

CODE_CAPABILITY_METADATA = build_language_service_capability_metadata_from_semantic_contract(
    AWARE_CODE_SEMANTIC_CONTRACT
)

CODE_SEMANTIC_TOKENS_CAPABILITY_METADATA = tuple(
    item for item in CODE_CAPABILITY_METADATA if item.capability == "semantic_tokens"
)

__all__ = [
    "CODE_CAPABILITY_EXECUTION_POLICY",
    "CODE_CAPABILITY_METADATA",
    "CODE_CAPABILITY_PARTICIPATION",
    "CODE_SECTION_OWNER",
    "CODE_SEMANTIC_TOKENS_CAPABILITY_METADATA",
]
