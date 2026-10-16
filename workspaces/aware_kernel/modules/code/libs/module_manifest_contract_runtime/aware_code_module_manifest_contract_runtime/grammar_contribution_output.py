"""Optional Code adapter over the original Language codec; no admission."""

from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    SemanticValueCoordinate,
)
from aware_code_semantic_contract_runtime.grammar_contribution_contract import (
    GRAMMAR_CONTRIBUTION_OUTPUT_REF,
)
from aware_code_semantic_contract_runtime.grammar_profile_contract import (
    MAX_GRAMMAR_BODY_BYTES,
)
from aware_code_semantic_contract_runtime.runtime import SemanticBody
from aware_language_parsed_document_contract import (
    SyntaxContributionV1,
    decode_syntax_assembly_value,
    encode_syntax_assembly_value,
)


def grammar_contribution_output_body(value: SyntaxContributionV1) -> SemanticBody:
    if type(value) is not SyntaxContributionV1:
        raise TypeError("exact Language contribution required")
    body = encode_syntax_assembly_value(value)
    if len(body) > MAX_GRAMMAR_BODY_BYTES:
        raise ContractViolation("Code contribution body exceeds aggregate bound")
    digest = ContentDigest.of_bytes(body)
    return SemanticBody(
        SemanticValueCoordinate(
            "code.syntax_contribution",
            GRAMMAR_CONTRIBUTION_OUTPUT_REF,
            "aware.code.grammar.contribution-output:" + digest.value,
            digest,
            len(body),
        ),
        body,
    )


def decode_grammar_contribution_output(body: SemanticBody) -> SyntaxContributionV1:
    if type(body) is not SemanticBody:
        raise TypeError("exact Code contribution body required")
    body.__post_init__()
    if len(body.canonical_body) > MAX_GRAMMAR_BODY_BYTES:
        raise ContractViolation("Code contribution body exceeds aggregate bound")
    if (
        body.coordinate.role != "code.syntax_contribution"
        or body.coordinate.contract != GRAMMAR_CONTRIBUTION_OUTPUT_REF
    ):
        raise ContractViolation("complete Code contribution output contract differs")
    value = decode_syntax_assembly_value(
        body.canonical_body, expected_type=SyntaxContributionV1
    )
    if type(value) is not SyntaxContributionV1:
        raise ContractViolation("Code contribution payload root differs")
    if grammar_contribution_output_body(value) != body:
        raise ContractViolation("complete Code contribution coordinate/body differs")
    return value
