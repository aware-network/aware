from __future__ import annotations

import pytest

from aware_code.grammar_anchor.value_codec import (
    CodeGrammarValueCodecError,
    decode_aware_string_literal,
    encode_code_grammar_anchor_semantic_value,
)
from aware_code_sdk.dto import (
    CodeGrammarAnchorRenderSemanticValue,
    CodeGrammarAnchorRenderSemanticValueKind,
    CodeGrammarAnchorRenderTypeRefValue,
)


def test_aware_string_value_codec_round_trips_experience_profile_title() -> None:
    semantic_value = CodeGrammarAnchorRenderSemanticValue(
        kind=CodeGrammarAnchorRenderSemanticValueKind.string,
        string_value="Home Story OS",
    )

    rendered = encode_code_grammar_anchor_semantic_value(
        value_domain="aware_string_literal",
        semantic_value=semantic_value,
    )

    assert rendered == '"Home Story OS"'
    assert decode_aware_string_literal(rendered) == "Home Story OS"


@pytest.mark.parametrize(
    ("semantic_value", "expected"),
    (
        (
            CodeGrammarAnchorRenderSemanticValue(
                kind=CodeGrammarAnchorRenderSemanticValueKind.string,
                string_value="hello",
            ),
            '"hello"',
        ),
        (
            CodeGrammarAnchorRenderSemanticValue(
                kind=CodeGrammarAnchorRenderSemanticValueKind.boolean,
                boolean_value=True,
            ),
            "true",
        ),
        (
            CodeGrammarAnchorRenderSemanticValue(
                kind=CodeGrammarAnchorRenderSemanticValueKind.integer,
                integer_value=42,
            ),
            "42",
        ),
        (
            CodeGrammarAnchorRenderSemanticValue(
                kind=CodeGrammarAnchorRenderSemanticValueKind.null,
            ),
            "null",
        ),
    ),
)
def test_aware_default_value_codec_is_canonical(
    semantic_value: CodeGrammarAnchorRenderSemanticValue,
    expected: str,
) -> None:
    assert (
        encode_code_grammar_anchor_semantic_value(
            value_domain="aware_default_value",
            semantic_value=semantic_value,
        )
        == expected
    )


def test_aware_type_ref_codec_owns_primitive_spelling_and_nullability() -> None:
    semantic_value = CodeGrammarAnchorRenderSemanticValue(
        kind=CodeGrammarAnchorRenderSemanticValueKind.type_ref,
        type_ref_value=CodeGrammarAnchorRenderTypeRefValue(
            type_name="string",
            nullable=True,
        ),
    )

    assert (
        encode_code_grammar_anchor_semantic_value(
            value_domain="aware_type_ref",
            semantic_value=semantic_value,
        )
        == "String?"
    )


def test_identifier_codec_rejects_source_token_syntax() -> None:
    semantic_value = CodeGrammarAnchorRenderSemanticValue(
        kind=CodeGrammarAnchorRenderSemanticValueKind.string,
        string_value="not-an-identifier",
    )

    with pytest.raises(CodeGrammarValueCodecError, match="identifier-shaped"):
        encode_code_grammar_anchor_semantic_value(
            value_domain="identifier",
            semantic_value=semantic_value,
        )
