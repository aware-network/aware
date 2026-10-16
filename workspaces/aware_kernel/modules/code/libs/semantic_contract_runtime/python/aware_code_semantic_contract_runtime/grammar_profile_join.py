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
    decode_grammar_source_group,
    grammar_source_group_body,
)
from .retained_declaration_scope import CodeRetainedDependencyScopeClosureV3
from .retained_declaration_scope_codec import (
    RETAINED_DECLARATION_SCOPE_V3_REF,
    decode_retained_declaration_scope,
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


def read_grammar_declaration_context(
    input: SemanticInputProductionInput,
) -> tuple[CodeGrammarSourceGroupV1, CodeRetainedDependencyScopeClosureV3]:
    """Decode and cross-check the two original supplied contexts, never admit them.

    Invoke inside registered Code production so the original owner authenticates
    source, context, currentness and lifetime before and after this synchronous
    data step. A self-consistent manufactured input is still portable data.
    No source read, TOML interpretation, registration or validation cache occurs.
    """
    owner_input = _validate_input_graph(input)
    grouped = tuple(
        item
        for item in owner_input.context_bodies
        if item.coordinate.role == "grammar_source_group"
        or item.coordinate.contract.key == GRAMMAR_SOURCE_GROUP_REF.key
    )
    declared = tuple(
        item
        for item in owner_input.context_bodies
        if item.coordinate.role == "declaration_scope"
        or item.coordinate.contract.key == RETAINED_DECLARATION_SCOPE_V3_REF.key
    )
    if len(grouped) != 1 or len(declared) != 1:
        raise ContractViolation(
            "one complete grammar group and declaration context required"
        )
    group_body, declaration_body = grouped[0], declared[0]
    coordinate = declaration_body.coordinate
    if (
        coordinate.role != "declaration_scope"
        or coordinate.contract != RETAINED_DECLARATION_SCOPE_V3_REF
        or coordinate.value_ref != "workspace-context:" + coordinate.digest.value
    ):
        raise ContractViolation("grammar declaration context identity differs")
    if (
        group_body.coordinate.role != "grammar_source_group"
        or group_body.coordinate.contract != GRAMMAR_SOURCE_GROUP_REF
    ):
        raise ContractViolation("grammar source group context identity differs")
    group = decode_grammar_source_group(group_body.canonical_body)
    validate_grammar_source_group_input(group, input=owner_input)
    closure = decode_retained_declaration_scope(declaration_body.canonical_body)
    # Each member is joined by complete original occurrence, never by a display
    # package label, first matching path, content digest or closure membership alone.
    scopes = {scope.scope_key: scope for scope in closure.scopes}
    for member in group.members:
        origin = decode_source_origin(bytes.fromhex(member.origin_body_hex))
        occurrence = origin.occurrence
        scope = scopes.get(occurrence.scope_key)
        if (
            occurrence.repository_binding_ref != closure.repository_binding_ref
            or scope is None
        ):
            raise ContractViolation("grammar member declaration scope differs")
        modules = tuple(
            item
            for item in scope.projection.modules
            if item.module_id == occurrence.module_id
        )
        packages = tuple(
            item
            for item in scope.projection.packages
            if item.module_id == occurrence.module_id
            and item.package_id == occurrence.package_id
        )
        if len(modules) != 1 or len(packages) != 1:
            raise ContractViolation("grammar member declaration occurrence unavailable")
        package = packages[0]
        manifest = package.manifest
        outer = origin.outer_manifest
        expected_root = "" if package.package_root == "." else package.package_root
        if (
            expected_root != occurrence.package_root
            or package.manifest_relative_path != occurrence.outer_manifest_path
            or modules[0].manifest.relative_path != package.module_manifest_path
            or manifest.relative_path
            != (
                (expected_root + "/" if expected_root else "")
                + occurrence.outer_manifest_path
            )
            or outer.relative_path != package.manifest_relative_path
            or outer.coordinate.value_ref != manifest.body_ref
            or outer.coordinate.digest != manifest.content_digest
            or outer.coordinate.size_bytes != len(manifest.body)
            or origin.package.package_kind != package.package_kind
            or origin.package.manifest_digest != manifest.content_digest
        ):
            raise ContractViolation(
                "grammar member complete manifest correspondence differs"
            )
    return group, closure
