"""Complete portable input correspondence, not original-source admission."""

from __future__ import annotations

from .contracts import ContractViolation, SemanticPackageCoordinate
from .grammar_source_group import (
    GRAMMAR_SOURCE_GROUP_REF,
    MAX_GROUP_BYTES,
    CodeGrammarSourceGroupV1,
    _coordinate,
    _digest,
    _exact,
    _field,
    _token,
    _tuple_items,
    grammar_source_group_body,
)
from .runtime import SemanticBody
from .semantic_candidates import MAX_CANDIDATES
from .semantic_input_producer import (
    MAX_CONTEXT_BODIES,
    SemanticInputPackageIdentity,
    SemanticInputProductionInput,
    SemanticInputSourceBody,
    SemanticInputSourceCoordinate,
)
from .source_origin import decode_source_origin


def _validate_input_graph(value: object) -> SemanticInputProductionInput:
    """Close exact nested types before invoking the original input validator."""
    item = _exact(value, SemanticInputProductionInput)
    for name in ("use_ref", "operation_ref", "stage"):
        _ = _token(_field(item, name))
    _ = _digest(_field(item, "input_digest"))
    identity = _exact(_field(item, "package_identity"), SemanticInputPackageIdentity)
    _ = _token(_field(identity, "package_name"))
    package = _exact(_field(identity, "package"), SemanticPackageCoordinate)
    _ = _token(_field(package, "package_ref"))
    _ = _token(_field(package, "package_kind"))
    _ = _digest(_field(package, "manifest_digest"))

    sources = _tuple_items(_field(item, "sources"))
    contexts = _tuple_items(_field(item, "context_bodies"))
    if len(sources) > MAX_CANDIDATES or len(contexts) > MAX_CONTEXT_BODIES:
        raise ContractViolation("grammar input collection bound exceeded")
    # Every source must later match one bounded root-group body. Every context
    # remains charged by the existing aggregate validator, including coordinates.
    source_total = 0
    for value in sources:
        body = _exact(value, SemanticInputSourceBody)
        source = _exact(_field(body, "source"), SemanticInputSourceCoordinate)
        _ = _exact(_field(source, "relative_path"), str)
        _ = _coordinate(_field(source, "coordinate"))
        raw = _exact(_field(body, "canonical_body"), bytes)
        source_total += len(raw)
        if source_total > MAX_GROUP_BYTES:
            raise ContractViolation("grammar input source body bound exceeded")
    total = 0
    for value in contexts:
        body = _exact(value, SemanticBody)
        _ = _coordinate(_field(body, "coordinate"))
        raw = _exact(_field(body, "canonical_body"), bytes)
        total += len(raw)
        if total > MAX_GROUP_BYTES:
            raise ContractViolation("grammar input context body bound exceeded")
    # Preserve the original digest, path, byte correspondence, ordering and
    # complete context-budget laws. No caller flag can waive digest validation.
    SemanticInputProductionInput.__post_init__(item)
    return item


def validate_grammar_source_group_input(
    value: CodeGrammarSourceGroupV1,
    *,
    input: SemanticInputProductionInput,
) -> None:
    """Check the complete group against one detached original owner input.

    Registered execution must authenticate source/context before and after the
    owner call. This synchronous, uncached helper issues no authority, lifetime
    receipt, contribution result or admission, and does not call source owners.
    """
    expected_group = grammar_source_group_body(value)
    owner_input = _validate_input_graph(input)
    matches = tuple(
        body
        for body in owner_input.context_bodies
        if body.coordinate.role == "grammar_source_group"
        or body.coordinate.contract == GRAMMAR_SOURCE_GROUP_REF
    )
    if (
        len(matches) != 1
        or matches[0].coordinate != expected_group.coordinate
        or matches[0].canonical_body != expected_group.canonical_body
    ):
        raise ContractViolation("grammar group differs from its complete input context")
    root = next(
        member
        for member in value.members
        if member.occurrence_ref == value.root_occurrence_ref
    )
    origin = decode_source_origin(bytes.fromhex(root.origin_body_hex))
    if origin.package != owner_input.package_identity.package:
        raise ContractViolation("grammar group root package differs from input")
    if len(root.sources) != len(owner_input.sources):
        raise ContractViolation(
            "grammar group root source inventory differs from input"
        )
    for grouped, original in zip(root.sources, owner_input.sources, strict=True):
        if (
            grouped.relative_path != original.source.relative_path
            or grouped.coordinate != original.source.coordinate
            or bytes.fromhex(grouped.body_hex) != original.canonical_body
        ):
            raise ContractViolation("grammar group root source differs from input")
