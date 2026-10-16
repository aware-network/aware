"""Strict Code owner codecs; decoded bodies are data, never admitted sources."""

from __future__ import annotations

import json
from typing import cast

from .codec import decode_profile_declaration, encode_profile_declaration
from .contracts import (
    ContentDigest,
    ContractViolation,
    SemanticContractRef,
    SemanticImplementationCoordinate,
    SemanticValueCoordinate,
    canonical_json_bytes,
)
from .grammar_profile_contract import (
    GRAMMAR_PROFILE_RESULT_REF,
    GRAMMAR_SYNTAX_BINDING_V2_REF,
    MAX_GRAMMAR_ANCHORS,
    MAX_GRAMMAR_BODY_BYTES,
    MAX_GRAMMAR_CONTRIBUTIONS,
    MAX_GRAMMAR_PROVIDERS,
    CodeGrammarAnchorRequirementV1,
    CodeGrammarContributionBindingV1,
    CodeGrammarDeclarationSourceV1,
    CodeGrammarProviderBindingV2,
    CodeGrammarSyntaxBindingV2,
    _bounded,
    _coordinate,
    _exact,
    _ref,
)
from .profile import SemanticContractProfileDeclaration
from .runtime import SemanticBody


def _implementation(
    ref: SemanticContractRef, name: str, recipe: str
) -> SemanticImplementationCoordinate:
    return SemanticImplementationCoordinate(
        name,
        ContentDigest.of_bytes(
            canonical_json_bytes({"contract": ref.to_wire(), "recipe": recipe})
        ),
    )


GRAMMAR_PROFILE_CODEC_IMPLEMENTATION = _implementation(
    GRAMMAR_PROFILE_RESULT_REF,
    "aware.code.grammar-profile-declaration.codec.v1",
    "complete original profile encode/decode; exact canonical UTF-8 bytes; reject field/digest/canonical substitutions; bounded body adapter; no source or provider authority",
)
GRAMMAR_SYNTAX_V2_CODEC_IMPLEMENTATION = _implementation(
    GRAMMAR_SYNTAX_BINDING_V2_REF,
    "aware.code.grammar-syntax-binding.codec.v2",
    "complete closed V2 syntax and repository-qualified declaration references; original complete coordinate wires; exact fields/types/literals; bounds and canonical ordering; duplicate rejection and byte-identical canonical re-encoding; no source or provider authority",
)


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ContractViolation("duplicate grammar JSON key")
        result[key] = value
    return result


def _constant(value: str) -> object:
    raise ContractViolation(f"nonfinite grammar JSON value: {value}")


def _load(body: bytes, limit: int = MAX_GRAMMAR_BODY_BYTES) -> object:
    _ = _exact(body, bytes)
    if not body or len(body) > limit:
        raise ContractViolation("grammar body exceeds wire bound")
    try:
        value = cast(
            object,
            json.loads(
                body.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_constant
            ),
        )
        stack = [(value, 1)]
        while stack:
            item, depth = stack.pop()
            if depth > 64:
                raise ContractViolation("grammar JSON nesting exceeds bound")
            if type(item) is dict:
                stack.extend(
                    (v, depth + 1) for v in cast(dict[str, object], item).values()
                )
            elif type(item) is list:
                stack.extend((v, depth + 1) for v in cast(list[object], item))
        if _bounded(value, limit) != body:
            raise ContractViolation("grammar body must be canonical JSON")
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise ContractViolation("invalid canonical grammar JSON") from exc
    return value


def _keys(
    value: object, keys: set[str], contract: str | None = None
) -> dict[str, object]:
    row = cast(dict[str, object], _exact(value, dict))
    if any(type(key) is not str for key in row) or set(row) != keys:
        raise ContractViolation("grammar wire fields differ")
    if contract is not None and _exact(row["contract"], str) != contract:
        raise ContractViolation("grammar contract literal differs")
    return row


def _list(value: object, limit: int) -> list[object]:
    rows = cast(list[object], _exact(value, list))
    if len(rows) > limit:
        raise ContractViolation("grammar array exceeds bound")
    return rows


def _read_ref(value: object) -> SemanticContractRef:
    row = _keys(value, {"key", "version", "schema_digest"})
    return _ref(
        SemanticContractRef(
            _exact(row["key"], str),
            _exact(row["version"], str),
            ContentDigest.of_wire(row["schema_digest"]),
        )
    )


def _read_coordinate(value: object) -> SemanticValueCoordinate:
    row = _keys(value, {"role", "contract", "value_ref", "digest", "size_bytes"})
    return _coordinate(
        SemanticValueCoordinate(
            _exact(row["role"], str),
            _read_ref(row["contract"]),
            _exact(row["value_ref"], str),
            ContentDigest.of_wire(row["digest"]),
            _exact(row["size_bytes"], int),
        )
    )


def _read_declaration(value: object) -> CodeGrammarDeclarationSourceV1:
    row = _keys(
        value,
        {
            "contract",
            "repository_binding_ref",
            "scope_key",
            "source_kind",
            "relative_path",
            "body_ref",
            "content_digest",
            "size_bytes",
        },
        "aware.code.grammar-declaration-source.v1",
    )
    return CodeGrammarDeclarationSourceV1(
        _exact(row["repository_binding_ref"], str),
        _exact(row["scope_key"], str),
        _exact(row["source_kind"], str),
        _exact(row["relative_path"], str),
        _exact(row["body_ref"], str),
        ContentDigest.of_wire(row["content_digest"]),
        _exact(row["size_bytes"], int),
    )


def _read_provider(value: object) -> CodeGrammarProviderBindingV2:
    row = _keys(
        value,
        {
            "contract",
            "occurrence_ref",
            "module_id",
            "provider_key",
            "semantic_contract",
            "declaration",
            "syntax_binding_digest",
        },
        "aware.code.grammar-provider-binding.v2",
    )
    return CodeGrammarProviderBindingV2(
        _exact(row["occurrence_ref"], str),
        _exact(row["module_id"], str),
        _exact(row["provider_key"], str),
        _read_ref(row["semantic_contract"]),
        _read_declaration(row["declaration"]),
        ContentDigest.of_wire(row["syntax_binding_digest"]),
    )


def _read_contribution(value: object) -> CodeGrammarContributionBindingV1:
    row = _keys(
        value,
        {"contract", "occurrence_ref", "relative_path", "contribution_coordinate"},
        "aware.code.grammar-contribution-binding.v1",
    )
    return CodeGrammarContributionBindingV1(
        _exact(row["occurrence_ref"], str),
        _exact(row["relative_path"], str),
        _read_coordinate(row["contribution_coordinate"]),
    )


def _read_anchor(value: object) -> CodeGrammarAnchorRequirementV1:
    row = _keys(
        value,
        {
            "contract",
            "provider_key",
            "consumer_contract",
            "role",
            "rule_name",
            "field_path",
            "required",
            "top_level",
        },
        "aware.code.grammar-anchor-requirement.v1",
    )
    return CodeGrammarAnchorRequirementV1(
        _exact(row["provider_key"], str),
        _read_ref(row["consumer_contract"]),
        _exact(row["role"], str),
        _exact(row["rule_name"], str),
        tuple(_exact(v, str) for v in _list(row["field_path"], 64)),
        _exact(row["required"], bool),
        _exact(row["top_level"], bool),
    )


def encode_grammar_syntax_binding(value: CodeGrammarSyntaxBindingV2) -> bytes:
    item = _exact(value, CodeGrammarSyntaxBindingV2)
    return _bounded(item.to_wire())


def decode_grammar_syntax_binding(body: bytes) -> CodeGrammarSyntaxBindingV2:
    row = _keys(
        _load(body),
        {
            "contract",
            "profile_key",
            "profile_ref",
            "profile_version",
            "code_profile_digest",
            "profile_source",
            "provider_bindings",
            "contribution_coordinates",
            "contribution_bindings",
            "anchor_requirements",
            "interpretation_profile",
            "trivia_policy",
        },
        "aware.code.grammar-syntax-binding.v2",
    )
    if _exact(row["trivia_policy"], str) != "shared_syntax_only":
        raise ContractViolation("grammar trivia policy differs")
    value = CodeGrammarSyntaxBindingV2(
        _exact(row["profile_key"], str),
        _exact(row["profile_ref"], str),
        _exact(row["profile_version"], str),
        ContentDigest.of_wire(row["code_profile_digest"]),
        _read_declaration(row["profile_source"]),
        tuple(
            _read_provider(v)
            for v in _list(row["provider_bindings"], MAX_GRAMMAR_PROVIDERS)
        ),
        tuple(
            _read_coordinate(v)
            for v in _list(row["contribution_coordinates"], MAX_GRAMMAR_CONTRIBUTIONS)
        ),
        tuple(
            _read_contribution(v)
            for v in _list(row["contribution_bindings"], MAX_GRAMMAR_CONTRIBUTIONS)
        ),
        tuple(
            _read_anchor(v)
            for v in _list(row["anchor_requirements"], MAX_GRAMMAR_ANCHORS)
        ),
        _read_coordinate(row["interpretation_profile"]),
    )
    if encode_grammar_syntax_binding(value) != body:
        raise ContractViolation("grammar syntax round trip differs")
    return value


class CodeGrammarProfileSelectionCodec:
    contract: SemanticContractRef = GRAMMAR_PROFILE_RESULT_REF
    implementation: SemanticImplementationCoordinate = (
        GRAMMAR_PROFILE_CODEC_IMPLEMENTATION
    )

    def encode(self, value: object) -> bytes:
        item = _exact(value, SemanticContractProfileDeclaration)
        try:
            body = encode_profile_declaration(item).encode("utf-8")
        except UnicodeError as exc:
            raise ContractViolation("profile body must be UTF-8") from exc
        if len(body) > MAX_GRAMMAR_BODY_BYTES:
            raise ContractViolation("profile body exceeds bound")
        return body

    def decode(self, body: bytes) -> SemanticContractProfileDeclaration:
        _ = _load(body)
        value = decode_profile_declaration(body.decode("utf-8"))
        if self.encode(value) != body:
            raise ContractViolation("profile body round trip differs")
        return value


class CodeGrammarSyntaxBindingCodec:
    contract: SemanticContractRef = GRAMMAR_SYNTAX_BINDING_V2_REF
    implementation: SemanticImplementationCoordinate = (
        GRAMMAR_SYNTAX_V2_CODEC_IMPLEMENTATION
    )

    def encode(self, value: object) -> bytes:
        return encode_grammar_syntax_binding(_exact(value, CodeGrammarSyntaxBindingV2))

    def decode(self, body: bytes) -> CodeGrammarSyntaxBindingV2:
        return decode_grammar_syntax_binding(body)


def _body(
    role: str, ref: SemanticContractRef, prefix: str, body: bytes
) -> SemanticBody:
    digest = ContentDigest.of_bytes(body)
    return SemanticBody(
        SemanticValueCoordinate(role, ref, prefix + digest.value, digest, len(body)),
        body,
    )


def grammar_profile_selection_body(
    value: SemanticContractProfileDeclaration,
) -> SemanticBody:
    return _body(
        "code.profile_selection",
        GRAMMAR_PROFILE_RESULT_REF,
        "code-profile-selection:",
        CodeGrammarProfileSelectionCodec().encode(value),
    )


def grammar_syntax_binding_body(value: CodeGrammarSyntaxBindingV2) -> SemanticBody:
    return _body(
        "code.syntax_binding",
        GRAMMAR_SYNTAX_BINDING_V2_REF,
        "code-grammar-syntax-binding:",
        encode_grammar_syntax_binding(value),
    )
