"""Code-owned output identity; payload interpretation remains Language-owned."""

from .contracts import ContentDigest, SemanticContractRef, canonical_json_bytes

GRAMMAR_CONTRIBUTION_OUTPUT_DESCRIPTOR = canonical_json_bytes(
    {
        "contract": "aware.code.grammar-contribution-output.v1",
        "version": "1",
        "role": "code.syntax_contribution",
        "body_schema": "aware.language.syntax-contribution.v1",
        "body_codec": "original Language encode_syntax_assembly_value / decode_syntax_assembly_value(expected_type=SyntaxContributionV1); closed canonical V1 carrier and nested validation, no alternate codec",
        "value_ref": "aware.code.grammar.contribution-output:<labelled SHA-256 of the complete canonical contribution body>",
        "source_account": "complete original Language SyntaxContributionV1.sources, preserving occurrence, source address, package, path, size and digest; scanner account remains included",
        "bounds": "original Language carrier/codec bounds and Code aggregate grammar budget",
        "authority": "portable Code-owned output data, not a Language registration, source/dependency permit or executable capability; original registered Code result admission remains required",
        "dependencies": "authored declarations remain lossless; presence does not grant dependency admission",
    }
)
GRAMMAR_CONTRIBUTION_OUTPUT_REF = SemanticContractRef(
    "aware.code.grammar-contribution-output.v1",
    "1",
    ContentDigest.of_bytes(GRAMMAR_CONTRIBUTION_OUTPUT_DESCRIPTOR),
)
