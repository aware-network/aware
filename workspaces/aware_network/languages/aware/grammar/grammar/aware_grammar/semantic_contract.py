from __future__ import annotations

from aware_code.module_semantic_contract import (
    ModuleCapabilityExecutionPolicyDescriptor,
    ModuleSemanticContract,
)
from aware_code.semantic_package.schemas import CapabilityParticipationDescriptor


AWARE_GRAMMAR_LEXICAL_OWNER = "aware_grammar.lexical"

AWARE_GRAMMAR_CAPABILITY_PARTICIPATION = (
    CapabilityParticipationDescriptor(
        capability="semantic_tokens",
        semantic_owner=AWARE_GRAMMAR_LEXICAL_OWNER,
    ),
)

AWARE_GRAMMAR_CAPABILITY_EXECUTION_POLICY = (
    ModuleCapabilityExecutionPolicyDescriptor(
        capability="semantic_tokens",
        semantic_owner=AWARE_GRAMMAR_LEXICAL_OWNER,
        callable_name="_lexical_provider",
        priority=10,
    ),
)

AWARE_GRAMMAR_SEMANTIC_CONTRACT = ModuleSemanticContract(
    provider_key="aware_grammar",
    capability_participation=AWARE_GRAMMAR_CAPABILITY_PARTICIPATION,
    capability_execution_policy=AWARE_GRAMMAR_CAPABILITY_EXECUTION_POLICY,
)
AWARE_MODULE_SEMANTIC_CONTRACT = AWARE_GRAMMAR_SEMANTIC_CONTRACT


__all__ = [
    "AWARE_GRAMMAR_CAPABILITY_EXECUTION_POLICY",
    "AWARE_GRAMMAR_CAPABILITY_PARTICIPATION",
    "AWARE_GRAMMAR_LEXICAL_OWNER",
    "AWARE_GRAMMAR_SEMANTIC_CONTRACT",
    "AWARE_MODULE_SEMANTIC_CONTRACT",
]
